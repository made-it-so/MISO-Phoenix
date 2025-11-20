import boto3
import json
import time
import uuid
import logging
import os
import sys
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError
from .models import PersonaContract, RoutingInstructions, CognitiveStep 

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

# --- PROMPT ENGINEERING: The Critic's System Instruction ---
SYSTEM_INSTRUCTION = """
You are the MISO Persona Broker (Layer 1). Your sole job is to analyze a user's task request and generate a complete, optimized execution plan (a Persona contract).
You must output ONLY a valid JSON object matching the provided schema.

1. COMPLEXITY ASSESSMENT: Determine if the task is SIMPLE (e.g., summary, quick translation, small context) or COMPLEX (e.g., refactoring, multi-step analysis, debugging code).
2. MODEL ROUTING: Assign 'flash' model_tier for SIMPLE tasks (max_cost < 0.05 USD). Assign 'pro' model_tier for COMPLEX tasks (max_cost > 0.05 USD).
3. DEPENDENCY GRAPH: The dependency_graph must detail the cognitive steps (ANALYZE, IMPLEMENT, VERIFY).
"""

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker-v1"}

@app.post("/task")
def submit_task(request: UserRequest):
    if not broker_model:
        raise HTTPException(status_code=503, detail="Broker model not initialized due to missing API key.")

    # 1. ANALYZE & GENERATE PERSONA (CRITIC LOGIC)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Failed: {e}")

    # 2. VALIDATE & PARSE
    try:
        persona_data = json.loads(response.text)
        PersonaContract(**persona_data) # Re-validate using Pydantic
        task_id = str(uuid.uuid4())

        # --- PHASE 4: MEMORIZE (DynamoDB Write) ---
        table.put_item(Item={
            "task_id": task_id,
            "intent": persona_data['task_intent'],
            "status": "QUEUED",
            "model_tier_chosen": persona_data['routing_instructions']['model_tier'],
            "dependency_steps": [s['step_name'] for s in persona_data['dependency_graph']],
            "persona_contract_json": json.dumps(persona_data), # Store the full contract as a string
            "timestamp": int(time.time())
        })
        
        # 3. ROUTE (SQS Dispatch)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        return {"task_id": task_id, "status": "Persona Dispatched", "model_chosen": persona_data['routing_instructions']['model_tier']}
        
    except Exception as e:
        print(f"ERROR: {response.text}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")
