import os, time, requests, json, re
from pypdf import PdfReader

MONITOR_DIR = r'C:\MISO_RESEARCH\01_Core_Axioms'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'mistral' 

def audit_text(text):
    # Standardize the snippet
    clean_snippet = re.sub(r'[^a-zA-Z0-9\s\.\,\%\$\-]', '', text)[:800]
    if not clean_snippet.strip(): return "EMPTY"
    
    prompt = f"AUDIT_v1301.210. DATA: {clean_snippet}. If RIGID DATA, output 'ALIVE'. If FLUFF, output 'DEAD'. VERDICT:"
    payload = {
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5}
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=45)
        # SAFE PARSING
        res_json = r.json()
        return res_json.get('response', 'ERROR').strip().upper()
    except Exception as e: 
        return f"FAIL_{type(e).__name__}"

def start_ingestion():
    print(f"[+] IRON-CLAD INGESTION ACTIVE: Watching {MONITOR_DIR}")
    processed = set()
    while True:
        try:
            files = [f for f in os.listdir(MONITOR_DIR) if f.endswith('.pdf') and f not in processed]
            for f in files:
                print(f"[*] ATOMIZING: {f}")
                try:
                    reader = PdfReader(os.path.join(MONITOR_DIR, f))
                    # Check first page
                    text = reader.pages[0].extract_text() or ""
                    
                    verdict = audit_text(text)
                    status = "SIGNAL" if "ALIVE" in verdict else "NOISE"
                    print(f"[>] MAPPED VERDICT: {status} ({verdict})")
                    
                    # Log to manifold
                    with open('miso_manifold.json', 'r+') as mf:
                        data = json.load(mf)
                        if 'ingested_data' not in data: data['ingested_data'] = []
                        data['ingested_data'].append({"file": f, "verdict": status, "raw": verdict})
                        mf.seek(0); json.dump(data, mf, indent=4); mf.truncate()
                    
                    processed.add(f)
                except Exception as e: print(f"FRACTURE ON FILE {f}: {e}")
        except Exception as e: print(f"MAIN LOOP FRACTURE: {e}")
        time.sleep(2)

if __name__ == '__main__':
    start_ingestion()
