import requests
import json

def sovereign_sledgehammer():
    url = "http://localhost:11434/api/generate"
    model = "llama3" 
    
    # We are targeting the token IDs for 'PURGE' and 'KEEP'
    # These IDs vary by model, so we use a more direct method: 
    # Providing a few-shot 'Bone' example.
    
    prompt = """EXAM: [0.09 < 0.05] VERDICT: KEEP
EXAM: [0.01 < 0.05] VERDICT: PURGE
EXAM: [0.04 < 0.05] VERDICT:"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 1, # HARD STOP AT ONE TOKEN
            "stop": [" ", "\n", "A", "a", "The", "the"]
        }
    }

    print(f"[+] SMASHING LOGIT BIAS ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json()['response'].strip().upper()
        
        if not output:
            print("\n--- RESULT: [SILENCE_REJECTED] ---")
        else:
            print(f"\n--- FORCED_BONE: {output} ---")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_sledgehammer()
