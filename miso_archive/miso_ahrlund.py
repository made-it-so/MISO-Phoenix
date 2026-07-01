import requests
import json

def audit_ahrlund():
    url = "http://localhost:11434/api/generate"
    model = "mistral"

    # DATA extracted from your preview
    data = "ACA enhances visual encoding based on arousal. ORB reduces high-contrast visual encoding. Feedback is laminar-specific."
    
    prompt = f"AUDIT_v1301.212. DATA: {data}. If this describes a RIGID CONTROL MECHANISM, output 'ALIVE'. If it is social fluff, output 'DEAD'. VERDICT:"

    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5}
    }

    print("[+] AUDITING AHRLUND-RICHTER 2026...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        output = r.json()['response'].strip().upper()
        print(f"\n--- VERDICT: {output} ---")
        
        if "ALIVE" in output:
            print("\n[!] SIGNAL CAPTURED. THE MANIFOLD EXPANDS.")
        else:
            print("\n[X] SUBSTRATE REJECTION.")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    audit_ahrlund()
