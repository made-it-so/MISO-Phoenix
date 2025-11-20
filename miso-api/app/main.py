import boto3
import json
import time
import uuid
import logging
import os
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .models import PersonaContract, RoutingInstructions, CognitiveStep 

# --- CONFIGURATION (Clients and Database) ---
REGION = "us-east-1"
QUEUE_NAME = "miso_job_queue"
TABLE_NAME = "miso_replay_buffer"

sqs = boto3.resource("sqs", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
table = dynamodb.Table(TABLE_NAME)

# Configure Gemini Client
try:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=gemini_key)
    broker_model = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    broker_model = None
    print(f"FATAL: Gemini client failed to initialize: {e}")

app = FastAPI()

class UserRequest(BaseModel):
    prompt: str

SYSTEM_INSTRUCTION = """
You are the MISO Persona Broker (Layer 1). Your sole job is to analyze a user's task request and generate a complete, optimized execution plan (a Persona contract).
[Instructions and rules remain the same...]
"""
logger = logging.getLogger("MISO_Broker")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def lookup_cache(intent: str):
    try:
        response = table.query(
            IndexName='IntentIndex',
            KeyConditionExpression=boto3.dynamodb.conditions.Key('intent').eq(intent),
            Limit=1,
            ScanIndexForward=False
        )
        if response['Items']:
            return json.loads(response['Items'][0]['persona_contract_json'])
        return None
    except Exception as e:
        print(f"DynamoDB Cache Lookup Failed: {e}")
        return None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker-v1"}

@app.post("/task")
def submit_task(request: UserRequest):
    if not broker_model:
        raise HTTPException(status_code=503, detail="Broker model not initialized.")

    task_intent = " ".join(request.prompt.lower().split()[:2])
    
    # 1. METACOGNITIVE REUSE (CACHE CHECK)
    cached_persona = lookup_cache(task_intent)
    
    if cached_persona:
        print(f"Cache HIT for intent: {task_intent}. Bypassing LLM generation.")
        persona_data = cached_persona
        source = "CACHE"
    else:
        # 2. ANALYZE & GENERATE PERSONA (CRITIC LOGIC)
        try:
            response = broker_model.generate_content(
                contents=f"User Task: {request.prompt}",
                config=genai.types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=PersonaContract,
                    temperature=0.0
                )
            )
            persona_data = json.loads(response.text)
            source = "LLM_GEN"
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM Generation Failed: {e}")

    # 3. VALIDATE, MEMORIZE, & ROUTE
    try:
        PersonaContract(**persona_data)
        task_id = str(uuid.uuid4())

        # MEMORIZE (DynamoDB Write)
        table.put_item(Item={
            "task_id": task_id,
            "intent": persona_data['task_intent'],
            "status": "QUEUED",
            "model_tier_chosen": persona_data['routing_instructions']['model_tier'],
            "dependency_steps": [s['step_name'] for s in persona_data['dependency_graph']],
            "persona_contract_json": json.dumps(persona_data),
            "timestamp": int(time.time())
        })
        
        # ROUTE (SQS Dispatch)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        # --- CRITICAL LOGGING ADDED HERE ---
        logger.info(json.dumps({
            "event": "PERSONA_DISPATCHED",
            "task_id": task_id,
            "source": source
        }))
        
        return {"task_id": task_id, "status": "Persona Dispatched", "source": source}
        
    except Exception as e:
        print(f"ERROR: {response.text}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")
