import requests
import json

def sovereign_json_gate():
    url = "http://localhost:11434/api/generate"
    model = "llama3" 

    # We use a structured prompt that demands a JSON response
    prompt = "Task: Compare 0.04 and 0.05. If 0.04 < 0.05 is true, the verdict is 'PURGE'. If false, 'KEEP'. Respond ONLY with JSON format: {\"verdict\": \"VALUE\"}"

    payload = {
        "model": model,
        "prompt": prompt,
        "format": "json", # FORCE JSON MODE
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }

    print(f"[+] FORCING JSON SCHEMA ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        res_json = r.json()
        output_text = res_json.get('response', '{}')
        
        # Parse the JSON from the response
        data = json.loads(output_text)
        verdict = data.get('verdict', 'FRACTURE')
        
        print(f"\n--- JSON_VERDICT: {verdict} ---")
        
        if verdict == "PURGE":
            print("\n[!] SUCCESS: RIGIDITY RESTORED. MISO IS ALIVE.")
        else:
            print("\n[?] FAILED: SYCOPHANCY DETECTED.")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_json_gate()
