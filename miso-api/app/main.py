import boto3
import json
import time
import uuid
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from botocore.exceptions import ClientError

# --- CONFIGURATION ---
REGION = "us-east-1"
QUEUE_NAME = "miso_job_queue"
TABLE_NAME = "miso_replay_buffer"

# Logging
logger = logging.getLogger("MISO_Broker")
logger.setLevel(logging.INFO)

# Initialize AWS Clients
sqs = boto3.resource("sqs", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)

try:
    queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
    table = dynamodb.Table(TABLE_NAME)
except ClientError as e:
    logger.error(f"Failed to connect to AWS resources: {e}")
    # We don't crash here, hoping they exist by the time a request comes in

app = FastAPI()

# --- DATA MODELS ---
class UserRequest(BaseModel):
    prompt: str
    priority: str = "normal"
    max_cost: float = 0.01

# --- LAYER 1 LOGIC ---

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "miso-broker"}

@app.post("/task")
def submit_task(request: UserRequest):
    task_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # 1. ANALYZE: (Placeholder for future Replay Buffer lookup)
    # Future logic: Check DynamoDB for 'intent' match to find cached plan.
    
    # 2. CONSTRUCT PERSONA
    persona = {
        "task_id": task_id,
        "task_type": "generate_intelligence",
        "created_at": timestamp,
        "payload": {
            "prompt": request.prompt
        },
        "routing_instructions": {
            "model_tier": "flash", # Defaulting to our spot leader
            "max_cost": request.max_cost,
            "priority": request.priority
        }
    }
    
    try:
        # 3. MEMORIZE: Write intent to Replay Buffer (DynamoDB)
        table.put_item(Item={
            "task_id": task_id,
            "intent": "generate_intelligence", # simplified intent
            "status": "PENDING",
            "persona": json.dumps(persona),
            "timestamp": timestamp
        })
        
        # 4. ROUTE: Dispatch to Order Book (SQS)
        queue.send_message(MessageBody=json.dumps(persona))
        
        logger.info(f"Task {task_id} dispatched.")
        return {"task_id": task_id, "status": "queued"}
        
    except Exception as e:
        logger.error(f"Broker Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

