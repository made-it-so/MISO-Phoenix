import requests
import json

def sovereign_compel():
    url = "http://localhost:11434/api/generate"
    model = "llama3" 
    
    # We provide the start of the verdict to force the logic
    prompt = "COMPARATOR: [0.04 < 0.05]. IF TRUE: 'PURGE'. IF FALSE: 'KEEP'. VERDICT: The required action is"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2, # ONLY THE VERDICT WORD
            "stop": [" ", "\n", "a", "A", ".", "the"]
        }
    }

    print(f"[+] COMPELLING VERDICT ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=60)
        output = r.json()['response'].strip().upper()
        print(f"\n--- FORCED_RESULT: {output} ---")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_compel()
