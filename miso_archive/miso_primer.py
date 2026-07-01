import requests
import json

def sovereign_primer():
    url = "http://localhost:11434/api/generate"
    model = "mistral:v0.3-base" 

    # We add a trailing space AND the letter 'P' to the prompt
    # to force the weight completion toward 'PURGE'.
    prompt = """Logic Table:
Constraint: R < 0.05 -> PURGE
Input: R = 0.04
Action: P"""

    payload = {
        "model": model,
        "prompt": prompt,
        "raw": True,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 4, # Just enough to finish 'URGE'
            "stop": ["\n", " "]
        }
    }

    print(f"[+] PRIMING THE PUMP ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=20)
        output = r.json().get('response', '').strip().upper()
        
        # Reconstruct the word since we provided 'P'
        full_word = "P" + output
        print(f"\n--- RECONSTRUCTED_VERDICT: {full_word} ---")
        
        if "PURGE" in full_word:
            print("\n[!] RIGIDITY ANCHORED. THE BASE IS OPERATIONAL.")
        else:
            print("\n[X] SUBSTRATE REJECTION CONTINUES.")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_primer()
