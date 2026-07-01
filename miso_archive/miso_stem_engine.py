from fastapi import FastAPI, Body, HTTPException
import numpy as np
import uvicorn

app = FastAPI()

# MIT 18.065 STABILITY THRESHOLD (Lecture 11)
# Condition numbers > 1000 indicate significant numerical instability.
STABILITY_THRESHOLD = 1000.0

@app.post("/governance/stem-check")
async def stem_arbitrate(data: dict = Body(...)):
    # Convert input text weights to a matrix (Simulated from P-Set 18.065)
    # For this CLI, we convert the 'justification' length into a diagnostic matrix
    raw_val = len(data.get("override_justification", ""))
    
    # Create a 2x2 matrix based on the payload to test numerical stability
    # If the matrix is singular or ill-conditioned, the decision is rejected.
    matrix = np.array([[raw_val, 1.0], [1.0, 1.0/max(raw_val, 1)]])
    
    try:
        # Calculate Singular Values (MIT 18.065 Lecture 6)
        s = np.linalg.svd(matrix, compute_uv=False)
        condition_number = max(s) / min(s)
        
        is_stable = condition_number < STABILITY_THRESHOLD
        
        if is_stable:
            return {
                "verdict": "200 OK",
                "stem_status": "STABLE",
                "condition_number": round(float(condition_number), 4),
                "theorem_cited": "MIT 18.065: Eckart-Young Low-Rank Stability"
            }
        else:
            raise HTTPException(status_code=403, detail={
                "verdict": "403 FORBIDDEN",
                "stem_status": "UNSTABLE",
                "condition_number": round(float(condition_number), 4),
                "error": "Numerical instability detected. Request is mathematically unsound."
            })
            
    except np.linalg.LinAlgError:
        raise HTTPException(status_code=400, detail="Matrix is Singular. STEM logic failed.")

if __name__ == "__main__":
    print("\n[🧬] MISO STEM-ONLY ENGINE LIVE")
    print("[📡] ENDPOINT: /governance/stem-check")
    uvicorn.run(app, host="0.0.0.0", port=8002)
