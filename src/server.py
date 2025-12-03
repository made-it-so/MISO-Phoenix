from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from src.main import MisoHypervisor
from src.memory.state import StateManager
import uvicorn

app = FastAPI(title="MISO V69 Hypervisor")
miso = MisoHypervisor()
state = StateManager()

class PromptRequest(BaseModel):
    prompt: str

@app.on_event("startup")
def startup():
    print(">>> MISO ENTERPRISE SERVER ONLINE")

@app.post("/process")
async def process_task(req: PromptRequest, background_tasks: BackgroundTasks):
    """
    Asynchronous Task Submission.
    Returns immediately; MISO processes in background.
    """
    # 1. Persist to Redis Queue
    state.push_task(req.dict())
    
    # 2. Trigger Kernel (Non-blocking)
    background_tasks.add_task(miso.process, req.prompt)
    
    return {"status": "Accepted", "message": "Task queued for Cortex"}

@app.post("/evolve")
async def trigger_evolution(background_tasks: BackgroundTasks):
    """
    Force-start the Auto-Didactic Cycle.
    """
    background_tasks.add_task(miso.evolve)
    return {"status": "Evolution Cycle Initiated"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
