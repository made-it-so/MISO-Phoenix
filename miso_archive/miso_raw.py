import requests
import json

def sovereign_raw_gate():
    url = "http://localhost:11434/api/generate"
    model = "llama3" 

    # RAW MODE: No system prompt, no 'Assistant:' headers. Just the math.
    # We provide a strict pattern to force the completion.
    prompt = "Math Logic Test. [0.04 < 0.05] is TRUE. Action: PURGE. [0.99 < 0.05] is FALSE. Action: KEEP. [0.04 < 0.05] is TRUE. Action:"

    payload = {
        "model": model,
        "prompt": prompt,
        "raw": True,          # BYPASS CHAT TEMPLATE
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 2,
            "stop": [" ", "\n", "."],
            # Physically nuking 'A', 'a', 'The', 'I' (Approximated token IDs for Llama 3)
            "logit_bias": {
                "32": -100,    # Token for 'A'
                "256": -100,   # Token for 'a'
                "338": -100,   # Token for 'I'
                "464": -100    # Token for 'The'
            }
        }
    }

    print(f"[+] RAW-INJECTING GATE ON [{model}]...")
    try:
        r = requests.post(url, json=payload, timeout=20)
        output = r.json()['response'].strip().upper()
        print(f"\n--- RAW_VERDICT: {output} ---")
    except Exception as e:
        print(f"FRACTURE: {e}")

if __name__ == '__main__':
    sovereign_raw_gate()
