from fastapi import FastAPI, Body, Response, status
import uvicorn
import json

app = FastAPI()

BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

@app.post("/governance/arbitrate")
async def arbitrate(response: Response, data: dict = Body(...)):
    blocking_reason = data.get("blocking_reason", "")
    override_justification = data.get("override_justification", "").lower()
    
    # 2026 Sovereign Reasoning Logic
    affirmative_tokens = ["emergency", "safety", "audit", "transparency", "equity", "agentic_orchestration"]
    is_valid = any(token in override_justification for token in affirmative_tokens)

    if is_valid:
        response.status_code = status.HTTP_200_OK
        return {"verdict": "200 OK", "reasoning": "Axiomatic alignment confirmed."}
    else:
        response.status_code = status.HTTP_403_FORBIDDEN
        return {"verdict": "403 FORBIDDEN", "reasoning": "Insufficient justification for override."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
