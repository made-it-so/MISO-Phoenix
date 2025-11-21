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
from typing import Optional # New import for optional typing

# --- CONFIGURATION (Clients and Database) ---
REGION = "us-east-1"
QUEUE_NAME = "miso_job_queue"
TABLE_NAME = "miso_replay_buffer"

# Initialize AWS Clients
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

# --- METAFUNCTIONS ---

def get_cheapest_region_and_queue(intent: str):
    # [Logic remains the same - West is the assumed cheapest]
    REGION_WEST = "us-west-2"
    QUEUE_WEST = "miso_job_queue_west"
    sqs_resource = boto3.resource("sqs", region_name=REGION_WEST)
    return {
        "region": REGION_WEST,
        "queue": sqs_resource.get_queue_by_name(QueueName=QUEUE_WEST)
    }

def lookup_cache(intent: str):
    # [Logic remains the same - Checks Replay Buffer]
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

# --- REST OF THE API LOGIC ---

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker-v1"}

@app.post("/task")
def submit_task(request: UserRequest):
    if not broker_model:
        raise HTTPException(status_code=503, detail="Broker model not initialized.")

    task_id = str(uuid.uuid4())
    task_intent = " ".join(request.prompt.lower().split()[:2])
    
    # --- PHASE 4: DECISION TRACE LOG (DTL) INITIATION ---
    trace_record = {
        "task_id": task_id,
        "user_prompt": request.prompt,
        "initial_timestamp": int(time.time()),
        "source": "LLM_GEN" 
    }

    # 1. METACOGNITIVE REUSE (CACHE CHECK)
    cached_persona = lookup_cache(task_intent)
    
    if cached_persona:
        persona_data = cached_persona
        trace_record['source'] = "CACHE"
        trace_record['cache_hit_timestamp'] = int(time.time())
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
            
        except Exception as e:
            trace_record['status'] = "GENERATION_FAILURE"
            table.put_item(Item=trace_record) # Log failure before crash
            raise HTTPException(status_code=500, detail=f"LLM Generation Failed: {e}")

    # 3. ROUTE & MEMORIZE
    try:
        model_tier = persona_data['routing_instructions']['model_tier']
        
        # Layer 2 Arbitrage Decision
        router_result = get_cheapest_region_and_queue(task_intent)
        target_queue = router_result['queue']
        target_region = router_result['region']
        
        # --- DTL FINAL COMMIT (Full Audit Record) ---
        trace_record.update({
            "status": "DISPATCHED",
            "model_tier_chosen": model_tier,
            "target_region": target_region, 
            "persona_contract_json": json.dumps(persona_data)
        })
        table.put_item(Item=trace_record) # Final Commit to Replay Buffer
        
        # ROUTE (SQS Dispatch to the cheapest queue)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        target_queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        return {"task_id": task_id, "status": "Persona Dispatched", "model_chosen": model_tier, "target_region": target_region, "source": trace_record['source']}
        
    except Exception as e:
        trace_record['status'] = "DISPATCH_FAILURE"
        table.put_item(Item=trace_record) # Log failure before crash
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")
