import json
from litellm import completion
from app.config import MODEL_MAP

async def classify_intent(user_prompt: str):
    """
    Uses Gemini Flash to decide the routing strategy.
    Cost: < -bash.001 per call.
    Latency: ~300ms.
    """
    system_prompt = (
        "You are a routing system. Analyze the user prompt. "
        "Return strictly valid JSON with two keys: "
        "'intent' (one of: 'CODING', 'CREATIVE', 'FACTUAL', 'COMPLEX_REASONING') "
        "and 'confidence' (0.0-1.0). Do not output markdown."
    )
    
    try:
        response = completion(
            model=MODEL_MAP["flash"],
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=50
        )
        content = response.choices[0].message.content
        # Clean potential markdown backticks from "smart" models
        content = content.replace('', '').strip()
        return json.loads(content)
    except Exception as e:
        print(f"Routing Failure: {e}")
        # Failover to cheap model if router breaks
        return {"intent": "FACTUAL", "confidence": 0.0}

def select_model(classification):
    intent = classification.get("intent", "FACTUAL")
    
    if intent == "CODING":
        return MODEL_MAP["coder"]
    elif intent == "COMPLEX_REASONING":
        return MODEL_MAP["reasoner"]
    else:
        return MODEL_MAP["cheap"]
