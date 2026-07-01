import requests
import json

def sovereign_audit():
    url = "http://localhost:11434/api/generate"
    model = "mistral"

    # We use a PRE-HEADER to tell the model it is a cold machine.
    # We set 'num_predict' to 2 to physically stop it from smiling.
    prompt = "[STRICT_LOGIC_ONLY] DATA: ACA axons encode visual signals. ORB reduces noise. TASK: If RIGID, output 'ALIVE'. If FLUFF, output 'DEAD'. VERDICT:"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2, # HARD LIMIT: No room for 'Hello there!'
            "stop": [" ", "\n", ".", "!", ":"]
        }
    }

    print("[+] ATTEMPTING TO MUZZLE THE SYCOPHANT...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        data = r.json()
        verdict = data.get('response', '').strip().upper()
        print(f"\n--- MUZZLED_VERDICT: {verdict} ---")
        
        if "ALIVE" in verdict:
            print("\n[!] SUCCESS: THE BONE IS REVEALED.")
        elif not verdict:
            print("\n[X] SILENCE: The model choked on its own muzzle.")
        else:
            print(f"\n[?] REJECTION: Model said '{verdict}'")
            
    except Exception as e:
        print(f"[X] FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_audit()
