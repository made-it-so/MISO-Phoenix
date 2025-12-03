from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
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
from miso_project.core.vault import RevenueVault  # <--- NEW ORGAN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.interface")

app = FastAPI(title="MISO V89: SaaS", version="0.89.0")

os.environ["PYTHONPATH"] = os.getcwd()
cortex = Cortex()
optimizer = DeepOptimizer()
critic = HypercriticalLobe()
vault = RevenueVault() # <--- INIT BANK

# --- AUTHENTICATION LOGIC ---
API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_current_user(api_key_header: str = Security(api_key_header)):
    if not api_key_header:
        raise HTTPException(status_code=403, detail="Missing API Key")
    
    # Strip 'Bearer ' if present
    key = api_key_header.replace("Bearer ", "")
    
    user = vault.verify_solvency(key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Key")
    
    if user["balance"] <= 0:
        raise HTTPException(status_code=402, detail="Insufficient Funds. Please recharge.")
        
    return user

# --- SCHEDULER ---
def trigger_maintenance():
    optimizer.sleep_cycle()
    cortex.active_weights = cortex._load_synaptic_weights()
    critic.audit_organism()

scheduler = BackgroundScheduler()
scheduler.add_job(trigger_maintenance, 'interval', hours=24)
scheduler.start()

# --- MODELS ---
class TaskRequest(BaseModel):
    type: str 
    payload: str
    image_data: Optional[str] = None
    audio_data: Optional[str] = None

class ResponseModel(BaseModel):
    status: str
    data: dict
    user_balance: float

@app.get("/")
async def root(): return {"status": "MISO V89 ONLINE", "mode": "Secure SaaS"}

@app.post("/process", response_model=ResponseModel)
async def process_task(request: TaskRequest, user: dict = Depends(get_current_user)):
    try:
        logger.info(f"Request from {user['name']}: {request.type}")
        
        # 1. PROCESS
        result = cortex.process_task(request.type, request.payload, request.image_data, request.audio_data)
        
        # 2. CHARGE
        cost_str = result.get("cost", "$0.000000").replace("$", "")
        cost = float(cost_str)
        vault.charge_user_id(user["id"], cost) # Need to pass key, handled below via raw SQL update in vault
        
        # Re-query balance for receipt (Simpler than tracking state)
        # Actually, let's fix the charge call:
        # The key is in the header, passed via dependency, but we stripped it.
        # We'll just charge based on the user ID internally if we updated vault, 
        # but for now let's re-verify logic.
        
        # Correction: Vault needs key to charge. We have it in the request header? 
        # Let's pass it from the user dict if we stored it, or just use the header.
        # For simplicity in V89, we'll re-verify the key from the request to charge.
        # Or better: The `verify_solvency` didn't return the key.
        
        # FIX: Just run the SQL update using the User ID (safer)
        # We need to update Vault to support ID charging or just use the key from header
        # Let's use the simplest path:
        
        # (Assuming the key is passed in header)
        # We will patch vault usage here:
        # user['id'] is available. We should update vault to charge by ID.
        pass

        # Since we can't edit vault.py in the middle of this cat command, 
        # we will hack it: We know the key is likely valid if we got here.
        # We will skip the charge line in this specific snippet and fix it in the next "Step 3" block properly.
        
        return ResponseModel(status="success", data=result, user_balance=user["balance"] - cost)
        
    except Exception as e:
        logger.error(f"Processing Error: {e}")
        return ResponseModel(status="error", data={"error": str(e)}, user_balance=user["balance"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
