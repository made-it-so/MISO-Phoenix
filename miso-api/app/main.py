from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import boto3
import json
import os
import logging
from typing import List, Optional
from pydantic import BaseModel, validator

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")

AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
DYNAMO_TABLE = "miso_replay_buffer"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

app = FastAPI(title="MISO Gateway", version="40.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS Clients
sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

# Models
class JobRequest(BaseModel):
    session_id: str
    api_key: str
    description: str
    feature_hash: Optional[str] = "0"

class Decision(BaseModel):
    task_id: Optional[str] = "UNKNOWN"
    optimal_decision: Optional[str] = "PROCESSING"
    vendor_target: Optional[str] = "PENDING"
    decision_timestamp: Optional[int] = 0
    feature_vector_hash: Optional[str] = "N/A"
    duration_ms: Optional[int] = 0
    
    @validator('*', pre=True)
    def check_none(cls, v): return v if v is not None else ""

# --- NEW ENDPOINT: HTTP INGESTION ---
@app.post("/miso/trigger")
async def trigger_job(job: JobRequest):
    """
    Bridges HTTP requests to the SQS Queue.
    This allows Locust/Curl to inject jobs into the system.
    """
    try:
        logger.info(f"📥 Ingesting Job: {job.session_id}")
        
        # Forward to SQS
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(job.dict())
        )
        
        return {"status": "queued", "job_id": job.session_id}
    except Exception as e:
        logger.error(f"Ingest Fail: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- EXISTING ENDPOINTS ---
@app.get("/decisions", response_model=List[Decision])
def get_decisions(limit: int = 50):
    try:
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        return sorted(items, key=lambda x: int(x.get('decision_timestamp', 0)), reverse=True)
    except: return []

@app.get("/stats")
def get_stats():
    try:
        response = table.scan(Limit=200)
        items = response.get('Items', [])
        stats = {"GCP": [], "AZURE": [], "AWS": []}
        for i in items:
            v = i.get('vendor_target', 'UNKNOWN')
            try: d = float(i.get('duration_ms', 0))
            except: d = 0
            if v in stats and d > 0: stats[v].append(d)
        return {k: int(sum(v)/len(v)) if v else 0 for k,v in stats.items()}
    except: return {"GCP": 0, "AZURE": 0, "AWS": 0}

# Static Files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    if os.path.exists(INDEX_FILE): return FileResponse(INDEX_FILE)
    return {"error": "Dashboard Offline"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
