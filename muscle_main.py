from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import os

app = FastAPI()

class Task(BaseModel):
    prompt: str
    complexity: str

@app.post("/work")
async def do_work(task: Task):
    # Identify the Provider (Injected via K8s Env Var)
    provider_id = os.getenv("PROVIDER_ID", "unknown-cloud")
    
    # Simulate Real-World Latency
    # "Premium" (Azure GPU) is fast (0.5s). "Cheap" (AWS Spot) is slower (2.0s).
    latency = 0.5 if "premium" in provider_id else 2.0
    await asyncio.sleep(latency)
    
    return {
        "result": f"[{provider_id.upper()}]: Processed '{task.prompt[:30]}...'",
        "provider": provider_id,
        "latency_ms": latency * 1000
    }
