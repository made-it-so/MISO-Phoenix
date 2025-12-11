import os
import httpx
import json

# --- MODEL REGISTRY (SYNCED WITH YOUR AUDIT) ---
MODELS = {
    # TIER 1: The Interns (Cheap/Fast)
    # UPDATED: Using the exact ID from your audit
    "gemini-flash": {"id": "gemini-2.0-flash-exp", "provider": "google",   "tier": 1, "cost": 0.0005},
    "gpt-4o-mini":  {"id": "gpt-4o-mini",          "provider": "openai",   "tier": 1, "cost": 0.002},
    
    # TIER 2: The Middle Class (Balanced)
    "deepseek-v3":  {"id": "deepseek-chat",        "provider": "deepseek", "tier": 2, "cost": 0.0002},
    
    # TIER 3: The Heavyweights (Smart/Vision)
    "gpt-4o":       {"id": "gpt-4o",               "provider": "openai",   "tier": 3, "cost": 0.02},
    "claude-sonnet":{"id": "claude-3-5-sonnet-20240620", "provider": "anthropic","tier": 3, "cost": 0.015},
    # UPDATED: Using the 2.0 Pro equivalent
    "gemini-pro":   {"id": "gemini-2.0-pro-exp",   "provider": "google",   "tier": 3, "cost": 0.01}, 
}

async def execute_with_arbitrage(prompt, image=None):
    keys = _get_keys()
    
    # 1. DETERMINE TARGET TIER
    if image:
        # Allow Tier 1 models (Gemini Flash) to handle vision if they can!
        # This fixes the "Biased toward High End" bug.
        target_tier = 1 
        capability = "vision"
    elif len(prompt) > 1000 or "code" in prompt.lower():
        target_tier = 2
        capability = "text"
    else:
        target_tier = 1
        capability = "text"

    # 2. BUILD CANDIDATE LIST (Cross-Tier Lookup)
    candidates = []
    
    # Helper to find models in a specific tier
    def get_candidates(tier):
        found = []
        for name, meta in MODELS.items():
            if meta["tier"] == tier and keys.get(meta["provider"]):
                # Capability Check
                if capability == "vision" and meta["provider"] not in ["openai", "google"]:
                    continue
                found.append(meta)
        return found

    # Try Target Tier First
    candidates = get_candidates(target_tier)
    
    # If Empty, Escalate to higher tiers (e.g., if Tier 1 has no vision, try Tier 3)
    if not candidates:
        for t in range(target_tier + 1, 4):
            candidates = get_candidates(t)
            if candidates: break

    if not candidates:
        return _error(f"System Error: No valid models found for {capability}")

    # 3. SORT BY COST (Cheapest First)
    queue = sorted(candidates, key=lambda x: x["cost"])

    # 4. TRUE FAILOVER LOOP
    errors = []
    for model in queue:
        try:
            # Try to execute
            result = await _call_provider(model, prompt, image, keys[model["provider"]])
            
            # If successful, return immediately
            if result.get("confidence", 0) > 0:
                return result
            
            # If provider returned an error dict, log it and continue loop
            errors.append(f"{model['provider']}: {result['answer']}")
            
        except Exception as e:
            errors.append(f"{model['provider']} Exception: {str(e)}")
            continue

    # 5. ALL FAILED
    return _error(f"All Providers Failed. Trace: {'; '.join(errors)}")


# --- PROVIDER HANDLERS ---

async def _call_provider(model_meta, prompt, image, key):
    provider = model_meta["provider"]
    model_id = model_meta["id"]
    cost = model_meta["cost"]

    if provider == "openai":
        return await _call_openai(key, model_id, prompt, image, cost)
    elif provider == "deepseek":
        return await _call_openai_compatible(key, "https://api.deepseek.com/chat/completions", model_id, prompt, "DeepSeek", cost)
    elif provider == "anthropic":
        return await _call_anthropic(key, model_id, prompt, cost)
    elif provider == "google":
        return await _call_gemini(key, model_id, prompt, image, cost)
    return _error(f"Unknown provider: {provider}")

async def _call_gemini(key, model, prompt, image, cost):
    try:
        # Using v1beta endpoint which supports the new 2.0 models
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        parts = [{"text": prompt}]
        if image: parts.append({"inline_data": {"mime_type": "image/jpeg", "data": image}})
        
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json={"contents": [{"parts": parts}]}, timeout=50.0)
            
            # FAILOVER TRIGGER: If not 200, return error dict to trigger next model
            if res.status_code != 200:
                return _error(f"Gemini {res.status_code}: {res.text}")
                
            candidates = res.json().get("candidates", [])
            if candidates:
                return _success(candidates[0]["content"]["parts"][0]["text"], f"Google ({model})", cost)
            return _error("Empty Response")
    except Exception as e: return _error(str(e))

async def _call_openai(key, model, prompt, image, cost):
    try:
        messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
        if image: messages[0]["content"].append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}})
        
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": messages, "max_tokens": 500},
                timeout=50.0
            )
            if res.status_code != 200: return _error(f"OpenAI {res.status_code}")
            return _success(res.json()["choices"][0]["message"]["content"], f"OpenAI ({model})", cost)
    except Exception as e: return _error(str(e))

async def _call_openai_compatible(key, url, model, prompt, name, cost):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                timeout=50.0
            )
            if res.status_code != 200: return _error(f"{name} {res.status_code}")
            return _success(res.json()["choices"][0]["message"]["content"], f"{name} ({model})", cost)
    except Exception as e: return _error(str(e))

async def _call_anthropic(key, model, prompt, cost):
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 500},
                timeout=50.0
            )
            if res.status_code != 200: return _error(f"Claude {res.status_code}")
            return _success(res.json()["content"][0]["text"], f"Anthropic ({model})", cost)
    except Exception as e: return _error(str(e))

def _get_keys():
    return {
        "openai": os.getenv("OPENAI_API_KEY"),
        "deepseek": os.getenv("DEEPSEEK_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "google": os.getenv("GEMINI_API_KEY"),
    }

def _success(ans, prov, cost):
    return {"answer": ans, "provider": prov, "cost": cost, "confidence": 0.99, "logic": "Tiered Arbitrage"}

def _error(msg):
    # Confidence 0 triggers the failover loop
    return {"answer": msg, "provider": "System", "cost": 0.0, "confidence": 0.0, "logic": "Fail"}
