from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import boto3
from typing import List, Optional, Any
from pydantic import BaseModel, validator
import logging

AWS_REGION = "us-east-1"
DYNAMO_TABLE = "miso_replay_buffer"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MISO V12.2 STABLE", version="12.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

# Loose Model (Accepts anything to prevent 500 Errors)
class Decision(BaseModel):
    task_id: Optional[str] = "UNKNOWN"
    optimal_decision: Optional[str] = "PROCESSING"
    vendor_target: Optional[str] = "PENDING"
    decision_timestamp: Optional[int] = 0
    feature_vector_hash: Optional[str] = "N/A"
    duration_ms: Optional[int] = 0

    @validator('*', pre=True)
    def check_none(cls, v):
        return v if v is not None else ""

@app.get("/decisions", response_model=List[Decision])
def get_decisions(limit: int = 50):
    try:
        response = table.scan(Limit=limit)
        items = response.get('Items', [])
        # Defensive sorting: handle missing timestamps
        sorted_items = sorted(items, key=lambda x: int(x.get('decision_timestamp', 0)), reverse=True)
        return sorted_items
    except Exception as e:
        logger.error(f"DB List Error: {e}")
        # Return empty list instead of crashing
        return []

@app.get("/stats")
def get_market_intelligence():
    try:
        response = table.scan(Limit=200)
        items = response.get('Items', [])
        stats = {"GCP": [], "AZURE": [], "AWS": []}
        
        for i in items:
            # Handle types safely (decimal to float)
            vendor = i.get('vendor_target', 'UNKNOWN')
            try:
                dur = float(i.get('duration_ms', 0))
            except:
                dur = 0
            
            if vendor in stats and dur > 0:
                stats[vendor].append(dur)
        
        results = {}
        for v, times in stats.items():
            if times:
                results[v] = int(sum(times) / len(times))
            else:
                results[v] = 0
        return results
    except Exception as e:
        logger.error(f"Stats Error: {e}")
        return {"GCP": 0, "AZURE": 0, "AWS": 0, "ERROR": str(e)}

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('app/static/index.html')

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
