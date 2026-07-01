import os, time, requests, json, re
from pypdf import PdfReader

MONITOR_DIR = r'C:\MISO_RESEARCH\01_Core_Axioms'
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'miso-auditor:latest' # ENSURE YOU CREATED THIS MODEL

def audit_chunk(chunk):
    # Short, high-impact prompt to avoid context timeouts
    prompt = f"AUDIT_SIGNAL_v1301.164. DATA: {chunk[:1000]}. VERDICT: SIGNAL or NOISE? (One word only)"
    payload = {
        "model": MODEL, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5}
    }
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=20)
        return r.json().get('response', 'ERROR_EMPTY').strip().upper()
    except Exception as e:
        return f"ERROR_{type(e).__name__}"

def process_pdfs():
    print(f"[+] ATOMIC SHOVEL ACTIVE: Watching {MONITOR_DIR}")
    processed = set()
    while True:
        files = [f for f in os.listdir(MONITOR_DIR) if f.endswith('.pdf') and f not in processed]
        for f in files:
            path = os.path.join(MONITOR_DIR, f)
            print(f"[*] SHOVELING: {f}")
            try:
                reader = PdfReader(path)
                # Only take the first 3 pages of text to prevent OOM/Timeouts
                content = ""
                for i in range(min(3, len(reader.pages))):
                    text = reader.pages[i].extract_text()
                    if text: content += text + " "
                
                if not content.strip():
                    print(f"[!] FAILED: {f} yielded no text (Image-based PDF?)")
                    processed.add(f)
                    continue

                verdict = audit_chunk(re.sub(r'\s+', ' ', content))
                print(f"[>] FINAL BONE VERDICT: {verdict}")
                processed.add(f)
            except Exception as e:
                print(f"FRACTURE on {f}: {e}")
        time.sleep(2)

if __name__ == '__main__':
    process_pdfs()
