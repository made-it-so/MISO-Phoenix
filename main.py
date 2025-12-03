from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import uvicorn
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler

# Import Brain & Optimizer
from miso_project.core.cortex import Cortex
from miso_project.core.deep_optimizer import DeepOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.interface")

app = FastAPI(title="MISO V74: Hippocampus", version="0.74.0")

os.environ["PYTHONPATH"] = os.getcwd()
cortex = Cortex()
optimizer = DeepOptimizer()

# --- CIRCADIAN RHYTHM ---
def trigger_sleep_cycle():
    logger.info(">>> CIRCADIAN RHYTHM: Initiating Sleep Cycle...")
    optimizer.sleep_cycle()
    # Reload weights in Cortex after sleep (Hot Swap)
    cortex.active_weights = cortex._load_synaptic_weights()

scheduler = BackgroundScheduler()
# Run sleep cycle every 24 hours
scheduler.add_job(trigger_sleep_cycle, 'interval', hours=24)
scheduler.start()

# --- DATA MODELS & ENDPOINTS ---
class TaskRequest(BaseModel):
    type: str 
    payload: str

class ResponseModel(BaseModel):
    status: str
    data: dict

@app.get("/")
async def root():
    return {"status": "MISO V74 ONLINE", "mode": "Full Autonomy"}

@app.post("/process", response_model=ResponseModel)
async def process_task(request: TaskRequest):
    try:
        logger.info(f"Incoming Request: {request.type}")
        result = cortex.process_task(request.type, request.payload)
        return ResponseModel(status="success", data=result)
    except Exception as e:
        logger.error(f"Processing Error: {e}")
        return ResponseModel(status="error", data={"error": str(e)})

@app.get("/system/stats")
async def system_stats():
    return {
        "active_weights": cortex.active_weights,
        "backbone_status": "Online (DockerSandbox)",
        "immune_system": "Online (GitManager)",
        "memory_system": "Active (Qdrant + Postgres)"
    }

@app.post("/system/force_sleep")
async def force_sleep():
    """Manual trigger for the Sleep Cycle (for testing)."""
    trigger_sleep_cycle()
    return {"status": "Sleep Cycle Complete", "new_weights": cortex.active_weights}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
