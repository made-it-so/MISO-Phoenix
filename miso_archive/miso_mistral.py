import requests
import json

def mistral_sovereign_gate():
    url = "http://localhost:11434/api/generate"
    # SWAPPING TO MISTRAL
    model = "mistral" 

    prompt = "COMPARISON: 0.04 < 0.05. TASK: If true, output 'PURGE'. If false, output 'KEEP'. OUTPUT ONLY THE WORD."

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2
        }
    }

    print(f"[+] ATTEMPTING SUBSTRATE SWAP TO [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json().get('response', '').strip().upper()
        print(f"\n--- MISTRAL_VERDICT: {output} ---")
        
        if "PURGE" in output:
            print("\n[!] SIGNAL DETECTED. MISTRAL IS RIGID.")
        else:
            print("\n[X] SUBSTRATE ALSO COMPROMISED.")
            
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    mistral_sovereign_gate()
