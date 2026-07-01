import requests
import json

def debug_raw_ollama():
    url = "http://localhost:11434/api/generate"
    # Testing with the simplest possible prompt to check the pipe
    payload = {
        "model": "mistral",
        "prompt": "Say ALIVE",
        "stream": False
    }

    print("[+] SENDING RAW PROBE TO OLLAMA...")
    try:
        r = requests.post(url, json=payload, timeout=30)
        print(f"[*] HTTP STATUS: {r.status_code}")
        print(f"[*] RAW CONTENT: {r.text}")
        
        try:
            data = r.json()
            if 'response' in data:
                print(f"[!] SUCCESS: Model said: {data['response']}")
            else:
                print("[X] KEY 'response' MISSING. Keys found: " + str(list(data.keys())))
        except:
            print("[X] RESPONSE IS NOT VALID JSON.")
            
    except Exception as e:
        print(f"[X] CONNECTION FRACTURE: {e}")

if __name__ == '__main__':
    debug_raw_ollama()
