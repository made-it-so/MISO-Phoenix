from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import boto3
from typing import List
from pydantic import BaseModel
import logging

AWS_REGION = "us-east-1"
DYNAMO_TABLE = "miso_replay_buffer"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MISO Market Maker API", version="8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

class Decision(BaseModel):
    task_id: str
    optimal_decision: str
    vendor_target: str
    decision_timestamp: int
    feature_vector_hash: str

# --- API ENDPOINTS ---
@app.get("/decisions", response_model=List[Decision])
def get_recent_decisions(limit: int = 50):
    try:
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        sorted_items = sorted(items, key=lambda x: x.get('decision_timestamp', 0), reverse=True)
        return sorted_items
    except Exception as e:
        logger.error(f"DB Read Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch market data")

# --- FRONTEND SERVING ---
# Mount static folder
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('app/static/index.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
