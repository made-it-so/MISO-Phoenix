from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
import uvicorn
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler

from miso_project.core.cortex import Cortex
from miso_project.core.deep_optimizer import DeepOptimizer
from miso_project.core.critic import HypercriticalLobe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.interface")

app = FastAPI(title="MISO V87: Vision", version="0.87.0")

os.environ["PYTHONPATH"] = os.getcwd()
cortex = Cortex()
optimizer = DeepOptimizer()
critic = HypercriticalLobe()

def trigger_sleep_cycle():
    logger.info(">>> CIRCADIAN RHYTHM: Initiating Sleep Cycle...")
    optimizer.sleep_cycle()
    cortex.active_weights = cortex._load_synaptic_weights()

def trigger_audit():
    logger.info(">>> IMMUNE PATROL: Starting Proactive Scan...")
    critic.audit_organism()

scheduler = BackgroundScheduler()
scheduler.add_job(trigger_sleep_cycle, 'interval', hours=24)
scheduler.add_job(trigger_audit, 'interval', hours=6)
scheduler.start()

class TaskRequest(BaseModel):
    type: str 
    payload: str
    image_data: Optional[str] = None # Base64 encoded image

class ResponseModel(BaseModel):
    status: str
    data: dict

@app.get("/")
async def root(): return {"status": "MISO V87 ONLINE", "mode": "Multimodal"}

@app.post("/process", response_model=ResponseModel)
async def process_task(request: TaskRequest):
    try:
        logger.info(f"Incoming Request: {request.type}")
        result = cortex.process_task(request.type, request.payload, request.image_data)
        return ResponseModel(status="success", data=result)
    except Exception as e:
        logger.error(f"Processing Error: {e}")
        return ResponseModel(status="error", data={"error": str(e)})

@app.get("/system/stats")
async def system_stats():
    return {"active_weights": cortex.active_weights, "status": "Online"}

@app.post("/system/force_sleep")
async def force_sleep():
    trigger_sleep_cycle()
    return {"status": "Sleep Cycle Complete"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
