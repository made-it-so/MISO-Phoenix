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

# Import our MISO-defined schema
from .models import PersonaContract, RoutingInstructions, CognitiveStep 

# --- CONFIGURATION ---
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
    broker_model = genai.GenerativeModel('gemini-2.5-pro') # Use PRO for complex reasoning
except Exception as e:
    # Fail fast if key is missing/bad, but keep app running for health check
    broker_model = None
    print(f"FATAL: Gemini client failed to initialize: {e}")

# Application setup
app = FastAPI()

class UserRequest(BaseModel):
    prompt: str

# --- PROMPT ENGINEERING: The Critic's System Instruction ---
# This forces the model to act as our hyper-critical auditor.
SYSTEM_INSTRUCTION = """
You are the MISO Persona Broker (Layer 1). Your sole job is to analyze a user's task request and generate a complete, optimized execution plan (a Persona contract).
You must output ONLY a valid JSON object matching the provided schema.

RULES:
1. EFFICIENCY: Assess the complexity. Simple tasks (typo fix, small data) get 'flash' model_tier and max_cost < 0.05. Complex tasks (refactoring, large reasoning) get 'pro' model_tier and max_cost > 0.05.
2. INTEGRITY: The dependency_graph must contain at least three steps: ANALYZE, IMPLEMENT, and VERIFY.
3. OUTPUT: Respond only with the raw JSON object. Do not add any conversational text, headers, or markdown.
"""

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker-v1"}

@app.post("/task")
def submit_task(request: UserRequest):
    if not broker_model:
        raise HTTPException(status_code=503, detail="Broker model not initialized due to missing API key.")

    # 1. ANALYZE & GENERATE PERSONA
    try:
        response = broker_model.generate_content(
            contents=f"User Task: {request.prompt}",
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=PersonaContract, # Enforce the schema
                temperature=0.0 # Force deterministic output
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Generation Failed: {e}")

    # 2. VALIDATE & PARSE
    try:
        persona_data = json.loads(response.text)
        PersonaContract(**persona_data) # Re-validate using Pydantic
        task_id = str(uuid.uuid4())

        # 3. MEMORIZE (DynamoDB Write)
        table.put_item(Item={
            "task_id": task_id,
            "intent": persona_data['task_intent'],
            "status": "QUEUED",
            "persona_data": json.dumps(persona_data),
            "timestamp": int(time.time())
        })
        
        # 4. ROUTE (SQS Dispatch)
        persona_to_dispatch = { "task_id": task_id, "persona": persona_data }
        queue.send_message(MessageBody=json.dumps(persona_to_dispatch))
        
        return {"task_id": task_id, "status": "Persona Dispatched"}
        
    except Exception as e:
        print(f"ERROR: {response.text}")
        raise HTTPException(status_code=500, detail=f"Internal Broker Error: {e}")

