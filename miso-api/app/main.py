import boto3
import json
import time
import uuid
import logging
import os
import sys
import random 
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .models import PersonaContract, RoutingInstructions, CognitiveStep 

# --- CONFIGURATION (Clients and Database) ---
REGION = "us-east-1"
TABLE_NAME = "miso_replay_buffer"

# --- V8: GLOBAL ARBITRAGE POOL DEFINITION ---
# This dictionary simulates the current live pricing feed from external Oracles.
# The Broker uses this list to find the best market.
GLOBAL_COMPUTE_POOL = [
    {"vendor": "AWS", "region": "us-east-1", "queue_name": "miso_job_queue"},
    {"vendor": "AWS", "region": "us-west-2", "queue_name": "miso_job_queue_west"},
    {"vendor": "GCP", "region": "us-central1", "queue_endpoint": "https://gcp-sqs-sim/us-central1"}, # Placeholder for GCP/Azure
    {"vendor": "AZURE", "region": "eastus", "queue_endpoint": "https://azure-sqs-sim/eastus"} 
]

# Initialize AWS Clients
dynamodb = boto3.resource("dynamodb", region_name=REGION)
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

# --- PRICING ORACLE (LAYER 2 ROUTER LOGIC) ---
def get_cheapest_region_and_queue(intent: str):
    """
    V8 Global Arbitrage: Selects the best performing and cheapest provider/region.
    
    This simulation randomly selects a target from the GLOBAL_COMPUTE_POOL.
    """
    # 1. Simulate Oracle Query (Find current cheapest provider)
    cheapest_route = random.choice(GLOBAL_COMPUTE_POOL)
    
    # 2. Handle Routing based on Vendor
    if cheapest_route['vendor'] == "AWS":
        # Use Boto3 for internal AWS queues
        sqs_resource = boto3.resource("sqs", region_name=cheapest_route['region'])
        target_queue = sqs_resource.get_queue_by_name(QueueName=cheapest_route['queue_name'])
    else:
        # For external clouds (GCP/Azure), we would use an external HTTP client or vendor SDK
        # We simulate the queue object for consistent logging
        class ExternalQueue:
            def send_message(self, MessageBody):
                print(f"Simulating send to {cheapest_route['vendor']} at {cheapest_route['region']}")
        target_queue = ExternalQueue()

    return {
        "region": cheapest_route['region'],
        "queue": target_queue,
        "vendor": cheapest_route['vendor']
    }

# --- METACOGNITIVE REUSE (CACHE LOOKUP) ---
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
    if not broker_model:
        raise HTTPException(status_code=503, detail="Broker model not initialized.")

    task_id = str(uuid.uuid4())
    task_intent = " ".join(request.prompt.lower().split()[:2])
    
    # 1. METACOGNITIVE REUSE (CACHE CHECK)
    cached_persona = lookup_cache(task_intent)
    
    if cached_persona:
        persona_data = cached_persona
        source = "CACHE"
    else:
        # 2. COGNITIVE TRIAGE & GENERATE PERSONA
        try:
            # [Logic remains the same - uses LIZARD_BRAIN for complexity check]
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
        model_tier = persona_data['routing_instructions']['model_tier']
        
        # --- NEW LAYER 2 ARBITRAGE DECISION ---
        router_result = get_cheapest_region_and_queue(task_intent)
        target_queue = router_result['queue']
        target_region = router_result['region']
        target_vendor = router_result['vendor']
        
        # Validation and Commit
        PersonaContract(**persona_data)

        # DTL FINAL COMMIT (Audit Record)
        table.put_item(Item={
            "task_id": task_id,
            "intent": persona_data['task_intent'],
            "status": "QUEUED",
            "model_tier_chosen": model_tier,
            "target_region": target_region, 
            "target_vendor": target_vendor, # Log the vendor (New V8 Metric)
            "source": source,
            "persona_contract_json": json.dumps(persona_data),
            "timestamp": int(time.time())
        })
        
        # ROUTE (SQS Dispatch to the cheapest queue)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        target_queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        # Final Output
        return {"task_id": task_id, "status": "Persona Dispatched", "model_chosen": model_tier, "target_vendor": target_vendor, "target_region": target_region, "source": source}
        
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")
