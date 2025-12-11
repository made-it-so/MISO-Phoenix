from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.router import classify_intent, select_model
from litellm import completion
import os

app = FastAPI(title="miso-phoenix")

class ChatRequest(BaseModel):
    prompt: str
    force_model: str = None

@app.get("/health")
def health():
    return {"status": "healthy", "service": "miso-core"}

@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    # 1. ARBITRAGE STEP: Classify Intent
    if not request.force_model:
        classification = await classify_intent(request.prompt)
        target_model = select_model(classification)
        strategy = "dynamic"
    else:
        target_model = request.force_model
        classification = {"intent": "MANUAL_OVERRIDE"}
        strategy = "manual"

    # 2. EXECUTION STEP: Call the Provider
    # Note: In Phase 3, we add Streaming here. For Phase 2, we block (sorry).
    try:
        response = completion(
            model=target_model,
            messages=[{"role": "user", "content": request.prompt}]
        )
        
        return {
            "response": response.choices[0].message.content,
            "meta": {
                "router_classification": classification,
                "selected_model": target_model,
                "strategy": strategy
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
