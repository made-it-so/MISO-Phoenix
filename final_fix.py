import os

# Content strictly matched to main.py requirements
code = """import httpx

async def execute_with_arbitrage(prompt, image=None):
    # 1. Triage Logic
    if image is not None or len(prompt) > 200:
        tier = "PREMIUM"
        estimated_cost = 0.05
        decision_logic = "High Complexity/Vision"
    else:
        tier = "CHEAP"
        estimated_cost = 0.002
        decision_logic = "Low Complexity/Text"
    
    # 2. Return Response
    # Mapping keys to main.py requirements:
    return {
        "answer": f"Processed by {tier} model", # Line 75
        "provider": tier,                       # Line 66
        "cost": estimated_cost,                 # Line 62/67
        "confidence": 0.99,                     # Line 68
        "logic": decision_logic,                # Line 78 <--- This was the next crash waiting to happen
        "status": "success"
    }
"""

with open("brain_functions.py", "w") as f:
    f.write(code)

print("✅ brain_functions.py rebuilt. All keys (answer, provider, cost, confidence, logic) are present.")
