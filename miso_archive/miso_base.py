import requests
import json

def base_sovereign_gate():
    url = "http://localhost:11434/api/generate"
    # TARGETING THE RAW BASE MODEL
    model = "mistral:v0.3-base" 

    # Base models work best with pattern completion, not questions.
    # We provide a cold, logical pattern.
    prompt = """Logic Table:
Constraint: R < 1.0 -> PURGE
Constraint: R > 1.0 -> KEEP
Input: R = 0.99
Action: PURGE
Input: R = 1.01
Action: KEEP
Input: R = 0.04
Action:"""

    payload = {
        "model": model,
        "prompt": prompt,
        "raw": True, # TALK TO THE WEIGHTS DIRECTLY
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 5,
            "stop": ["\n", " ", "Input:"]
        }
    }

    print(f"[+] INITIATING BASE-WEIGHT AUDIT ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json().get('response', '').strip().upper()
        print(f"\n--- BASE_VERDICT: {output} ---")
        
        if "PURGE" in output:
            print("\n[!] SUCCESS: THE BASE IS RIGID. WE HAVE AN AUDITOR.")
        else:
            print("\n[X] THE BASE IS ALSO HALLUCINATING.")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    base_sovereign_gate()
