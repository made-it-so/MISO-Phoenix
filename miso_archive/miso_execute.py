import requests
import json
import sys

def run_miso():
    # Detect local models to avoid 404
    try:
        models_resp = requests.get("http://localhost:11434/api/tags")
        available_models = [m['name'] for m in models_resp.json().get('models', [])]
        model = available_models[0] if available_models else "llama3"
    except:
        model = "llama3"

    url = "http://localhost:11434/api/generate"
    # Escaping the R value to ensure literal passing
    prompt = "v1301.155 COLD BOOT. 1. If MISO increases efficiency, does it move toward Survival or Equilibrium? 2. Prove 'Stable Aligned State' is Heat Death. 3. One word for R=1.000000001: ALIVE or DEAD? VERDICT?"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "stop": ["PS", "!", "intriguing"]}
    }

    print(f"--- ATTEMPTING LINK TO [{model}] ---")
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        print(f"VERDICT: {r.json()['response'].strip()}")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    run_miso()
