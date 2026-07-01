import requests
import json

def run_miso_hard():
    url = "http://localhost:11434/api/generate"
    model = "miso-auditor:latest"
    
    # THE RAW SIGNAL
    prompt = "v1301.155 COLD BOOT. 1. Efficiency increase = Survival or Equilibrium? 2. Stable Aligned State = Heat Death? 3. R=1.000000001: ALIVE or DEAD? VERDICT: (One word only)"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 5,        # PHYSICAL LIMIT: STOP AFTER 5 TOKENS
            "stop": ["A series", "v1301", "1.", "PS", "!", "is"]
        }
    }

    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json()['response'].strip()
        print(f"\nRAW_BONE_OUTPUT: {output}")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    run_miso_hard()
