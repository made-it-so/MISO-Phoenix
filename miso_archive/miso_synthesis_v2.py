import requests
import json

def sovereign_synthesis_v2():
    url = "http://localhost:11434/api/generate"
    model = "mistral"

    # THE BONE-ONLY PROMPT
    # Stripping all fluff. Pure logical mapping.
    prompt = "INVARIANT CHECK: Foam Rigidity (Surface Tension) == AI Rigidity (Token Density). If Equilibrium leads to structural collapse, the system is 'ALIVE'. If Equilibrium leads to stability, the system is 'DEAD'. VERDICT:"

    payload = {
        "model": model, "prompt": prompt, "stream": False,
        "options": {
            "temperature": 0.0, 
            "num_predict": 10,
            "stop": [" ", "\n", "."]
        }
    }

    print("[+] INITIATING DEEP-THINK SYNTHESIS (120s LIMIT)...")
    try:
        # Doubling the timeout again to bypass hardware throttle
        r = requests.post(url, json=payload, timeout=120) 
        output = r.json()['response'].strip().upper()
        print(f"\n--- SYNTHESIS_VERDICT: {output} ---")
        
        # LOG TO MANIFOLD
        with open('miso_manifold.json', 'r+') as f:
            data = json.load(f)
            if "ALIVE" in output:
                data['rank'] = 1.6500
                data['status'] = "SYNTHESIS_SUCCESS"
            else:
                data['status'] = "SYNTHESIS_FLAWED"
            f.seek(0); json.dump(data, f, indent=4); f.truncate()
            print(f"[!] MANIFOLD UPDATED. RANK: {data['rank']}%")
            
    except Exception as e: 
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_synthesis_v2()
