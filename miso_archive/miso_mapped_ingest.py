import os, time, requests, json, re
from pypdf import PdfReader

MONITOR_DIR = r'C:\MISO_RESEARCH\01_Core_Axioms'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'mistral' 

def audit_text(text):
    # Reduced window (800 chars) for faster processing
    clean_snippet = re.sub(r'[^a-zA-Z0-9\s\.\,\%\$\-]', '', text)[:800]
    if not clean_snippet.strip(): return "EMPTY"
    
    prompt = f"AUDIT_v1301.186. DATA: {clean_snippet}. TASK: If this is RIGID DATA, output 'ALIVE'. If it is FLUFF, output 'DEAD'. VERDICT:"
    payload = {
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5}
    }
    try:
        # 60-second timeout to allow for heavy compute
        r = requests.post(OLLAMA_URL, json=payload, timeout=60) 
        return r.json()['response'].strip().upper()
    except Exception as e: return f"TIMEOUT_{type(e).__name__}"

def start_ingestion():
    print(f"[+] THROTTLE-BYPASS ACTIVE: Watching {MONITOR_DIR}")
    processed = set()
    while True:
        files = [f for f in os.listdir(MONITOR_DIR) if f.endswith('.pdf') and f not in processed]
        for f in files:
            print(f"[*] ATOMIZING: {f}")
            try:
                reader = PdfReader(os.path.join(MONITOR_DIR, f))
                # Only pull the first page for the high-density check
                text = reader.pages[0].extract_text()
                
                verdict = audit_text(text)
                status = "SIGNAL" if "ALIVE" in verdict else "NOISE"
                print(f"[>] MAPPED VERDICT: {status} ({verdict})")
                
                with open('miso_manifold.json', 'r+') as mf:
                    data = json.load(mf)
                    if 'ingested_data' not in data: data['ingested_data'] = []
                    data['ingested_data'].append({"file": f, "verdict": status, "timestamp": time.time()})
                    mf.seek(0); json.dump(data, mf, indent=4); mf.truncate()
                
                processed.add(f)
            except Exception as e: print(f"FRACTURE: {e}")
        time.sleep(2)

if __name__ == '__main__':
    start_ingestion()
