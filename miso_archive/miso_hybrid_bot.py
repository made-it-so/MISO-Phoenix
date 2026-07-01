from fastapi import FastAPI, Body, Response, status
import uvicorn
import json
import os

app = FastAPI()

# SEGREGATED DATA PATHS
CORE_BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
SANDBOX_PATH = r"C:\Users\kyle\miso_data\corporate_sandbox.json"

@app.post("/governance/arbitrate")
async def hybrid_arbitrate(response: Response, data: dict = Body(...)):
    override = data.get("override_justification", "").lower()
    
    if not os.path.exists(SANDBOX_PATH):
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": "Corporate Sandbox not found. Run miso_sandbox_manager.py first."}

    with open(SANDBOX_PATH, 'r') as f:
        sandbox = json.load(f)
    
    policy = sandbox["custom_axioms"]["CORP_GOV_01"]
    has_token = any(t in override for t in policy["valid_tokens"])
    has_ticket = "ticket-" in override

    if has_token and has_ticket:
        response.status_code = status.HTTP_200_OK
        return {"verdict": "200 OK", "reasoning": "Justification accepted via Corporate Sandbox."}
    
    response.status_code = status.HTTP_403_FORBIDDEN
    missing = []
    if not has_token: missing.append("a valid Corporate Priority token")
    if not has_ticket: missing.append("a 'ticket-ID'")
    
    return {
        "verdict": "403 FORBIDDEN",
        "message": f"MISO requires {', and '.join(missing)} to proceed."
    }

if __name__ == "__main__":
    print("\n[🛡️] MISO HYBRID ARBITRATOR LIVE")
    print("[📡] LISTENING ON PORT 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
