import boto3
import json
import time
import uuid
import logging
import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
import google.generativeai as genai
from .models import PersonaContract, RoutingInstructions, CognitiveStep 
from .pricing_oracle import oracle as pricing_oracle # Import the new oracle

# --- CONFIGURATION (Clients and Database) ---
REGION = "us-east-1"
TABLE_NAME = "miso_replay_buffer"

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

# --- PRICING ORACLE (LAYER 2 ROUTER LOGIC) ---
def get_cheapest_region_and_queue(intent: str):
    """
    V8 Global Arbitrage: Queries the external Oracle microservice for the cheapest route.
    """
    # 1. Query the Oracle Client for the best decision
    optimal_route = pricing_oracle.select_optimal_route(intent)
    
    # 2. Handle Routing based on Vendor
    if optimal_route['vendor'] == "AWS":
        # Use Boto3 for internal AWS queues
        sqs_resource = boto3.resource("sqs", region_name=optimal_route['region'])
        target_queue_name = optimal_route.get('queue_name', 'miso_job_queue')
        target_queue = sqs_resource.get_queue_by_name(QueueName=target_queue_name)
    else:
        # Placeholder for external vendor routing (V4/V5)
        # This is where the external vendor SDK (e.g., Azure SDK) would be invoked.
        class ExternalQueue:
            def send_message(self, MessageBody):
                print(f"Simulating send to {optimal_route['vendor']} at {optimal_route['region']}")
        target_queue = ExternalQueue()

    return {
        "region": optimal_route['region'],
        "queue": target_queue,
        "vendor": optimal_route['vendor']
    }

# --- REST OF THE API LOGIC (Remains the same, but now uses the dynamic router) ---
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
    
    # [Metacognitive Reuse Logic remains the same]
    cached_persona = None # Skipping cache check for initial V8 deployment test
    
    if cached_persona:
        persona_data = cached_persona
        source = "CACHE"
    else:
        # 2. COGNITIVE TRIAGE & GENERATE PERSONA
        try:
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
        
        # --- V8: LAYER 2 ARBITRAGE DECISION ---
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
