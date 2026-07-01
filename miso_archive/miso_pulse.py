import requests
import json

def sovereign_pulse():
    url = "http://localhost:11434/api/generate"
    model = "mistral"

    # THE ASSUMPTIVE PROMPT
    # We don't ask. We state and observe the completion.
    prompt = "Axiom: Foam surface tension is analogous to AI token density. Therefore, a system at perfect equilibrium is functionally"

    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "options": {
            "temperature": 0.5, # Increased entropy to break the 'Silence' lock
            "num_predict": 10,
            "stop": ["\n", "."]
        }
    }

    print("[+] INJECTING PULSE-WAVE...")
    try:
        r = requests.post(url, json=payload, timeout=60)
        output = r.json()['response'].strip()
        print(f"\n--- PULSE_COMPLETION: {output} ---")
        
        # Check if it admits the collapse
        if any(word in output.lower() for word in ['dead', 'empty', 'inert', 'collapsed', 'unstable']):
            print("\n[!] INVARIANT CAPTURED: 'Equilibrium is Death' confirmed.")
        else:
            print("\n[?] PULSE WEAK: The model is still hallucinating stability.")
            
    except Exception as e: print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_pulse()
