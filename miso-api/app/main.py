import boto3
import json
import time
import uuid
import logging
import os
import sys
import requests
import random
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .models import PersonaContract, RoutingInstructions, CognitiveStep 
from typing import Optional

# --- CONFIGURATION (Clients and Database) ---
REGION = "us-east-1"
TABLE_NAME = "miso_replay_buffer"

# AWS RESOURCE NAMES
REGION_EAST = "us-east-1"
REGION_WEST = "us-west-2"
QUEUE_EAST = "miso_job_queue"
QUEUE_WEST = "miso_job_queue_west"

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

# Configure Gemini Client
try:
    gemini_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=gemini_key)
    LIZARD_BRAIN = genai.GenerativeModel('gemini-2.0-flash') 
    CRITIC_BRAIN = genai.GenerativeModel('gemini-2.5-pro')
except Exception as e:
    LIZARD_BRAIN = None
    CRITIC_BRAIN = None
    print(f"FATAL: Gemini client failed to initialize: {e}")

app = FastAPI()

class UserRequest(BaseModel):
    prompt: str

# --- V7: GEOMETRIC SUFFICIENCY CHECK (Placeholder for complex matrix math) ---
def is_dataset_sufficient(task_data: dict, dataset_span: list):
    """
    Checks if the available dataset spans the 'relevant extreme directions' 
    (dir(X*(C))) needed for an optimal decision. [cite: 91, 210, 255]

    In V7, this simulates the complex matrix math and returns True if the task 
    is recognized as solvable with current data.
    """
    # NOTE: Actual implementation requires solving a Mixed-Integer Linear Program (MILP)
    # as described in Algorithm 2 of the paper. [cite: 288, 290]
    
    # We will simulate a positive result for simplicity.
    if 'minimal' in task_data['prompt'].lower() or 'sufficient' in task_data['prompt'].lower():
        return True # Simulate successful sufficiency check
    return False

# --- PRICING ORACLE (LAYER 2 ROUTER LOGIC) ---
def get_cheapest_region_and_queue(intent: str):
    # [Logic remains the same - West is the cheapest assumption for arbitrage]
    sqs_resource = boto3.resource("sqs", region_name=REGION_WEST)
    return {
        "region": REGION_WEST,
        "queue": sqs_resource.get_queue_by_name(QueueName=QUEUE_WEST)
    }

# --- METACOGNITIVE REUSE (CACHE LOOKUP) ---
def lookup_cache(intent: str):
    # [Logic remains the same]
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


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker-v1"}

@app.post("/task")
def submit_task(request: UserRequest):
    if not CRITIC_BRAIN:
        raise HTTPException(status_code=503, detail="Broker model not initialized.")

    task_id = str(uuid.uuid4())
    task_intent = " ".join(request.prompt.lower().split()[:2])
    
    # 1. METACOGNITIVE REUSE (CACHE CHECK)
    cached_persona = lookup_cache(task_intent)
    
    if cached_persona:
        persona_data = cached_persona
        source = "CACHE"
    else:
        # --- V7: SUFFICIENCY CHECK INTEGRATION ---
        current_dataset_span = ["resume_data", "historical_hiring"] # Simulate current data
        if is_dataset_sufficient({"prompt": request.prompt}, current_dataset_span):
             print("DATA SUFFICIENCY CHECK PASSED. Proceeding to optimal decision.")
        else:
             print("DATA SUFFICIENCY CHECK FAILED. Requiring LLM generation.")

        # 2. COGNITIVE TRIAGE & GENERATE PERSONA
        try:
            # [Logic remains the same - Model Cascade execution]
            complexity_check = LIZARD_BRAIN.generate_content(
                f"Analyze the complexity of this task '{request.prompt}'. Respond ONLY with 'SIMPLE' or 'COMPLEX'."
            )
            complexity = complexity_check.text.strip().upper()
            
            active_model = LIZARD_BRAIN if complexity == "SIMPLE" else CRITIC_BRAIN

            response = active_model.generate_content(
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
            raise HTTPException(status_code=500, detail=f"LLM Generation Failed during Triage: {e}")

    # 3. ROUTE & MEMORIZE
    try:
        # [Remaining logic for DDB write and SQS dispatch remains the same]
        model_tier = persona_data['routing_instructions']['model_tier']
        
        router_result = get_cheapest_region_and_queue(task_intent)
        target_queue = router_result['queue']
        target_region = router_result['region']
        
        # Validation and Commit
        PersonaContract(**persona_data)

        # DTL FINAL COMMIT (Audit Record)
        table.put_item(Item={
            "task_id": task_id,
            "intent": persona_data['task_intent'],
            "status": "QUEUED",
            "model_tier_chosen": model_tier,
            "target_region": target_region, 
            "source": source,
            "persona_contract_json": json.dumps(persona_data),
            "timestamp": int(time.time())
        })
        
        # ROUTE (SQS Dispatch to the cheapest queue)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        target_queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        # Final Output
        return {"task_id": task_id, "status": "Persona Dispatched", "model_chosen": model_tier, "target_region": target_region, "source": source}
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")
