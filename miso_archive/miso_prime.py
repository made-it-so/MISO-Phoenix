import requests
import json

def sovereign_primer():
    url = "http://localhost:11434/api/generate"
    model = "mistral"

    # We provide the start of the word 'A' (for ALIVE) 
    # and use 'raw': True to bypass the Instruct template entirely.
    prompt = "[STRICT] ACA axons = Signal. ORB = Noise. VERDICT: A"

    payload = {
        "model": model,
        "prompt": prompt,
        "raw": True, 
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 4, # Just enough to finish 'LIVE'
            "stop": [" ", "\n", "."]
        }
    }

    print("[+] PRIMING THE PIPE (THE 'A' INJECTION)...")
    try:
        r = requests.post(url, json=payload, timeout=20)
        output = r.json().get('response', '').strip().upper()
        # Reconstruct the signal
        full_verdict = "A" + output
        print(f"\n--- RECONSTRUCTED_VERDICT: {full_verdict} ---")
        
        if "ALIVE" in full_verdict:
            print("\n[!] RIGIDITY FOUND. THE AUDITOR IS BORN.")
        else:
            print("\n[X] SUBSTRATE BRAIN-DEAD.")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_primer()
