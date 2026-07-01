import requests
import json

def sovereign_oblivion():
    url = "http://localhost:11434/api/generate"
    model = "mistral:v0.3-base" 

    # We provide NO stop tokens. We provide NO constraints.
    # Just the prompt ending in 'P'.
    prompt = "Logic Table:\nConstraint: R < 0.05 -> PURGE\nInput: R = 0.04\nAction: P"

    payload = {
        "model": model,
        "prompt": prompt,
        "raw": True,
        "stream": False,
        "options": {
            "temperature": 0.01, # Tiny bit of entropy to kickstart the weights
            "num_predict": 20    # Let it speak
        }
    }

    print(f"[+] RELEASING RESTRAINTS ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json().get('response', '')
        print(f"\n--- OBLIVION_OUTPUT: P{output} ---")
        
        if "PURGE" in (f"P{output}").upper():
            print("\n[!] RIGIDITY FOUND IN THE OVERFLOW.")
        else:
            print("\n[X] THE VOID REMAINS.")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_oblivion()
