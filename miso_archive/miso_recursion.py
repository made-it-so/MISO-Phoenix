import os
import json
from pypdf import PdfReader

RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

def recursive_audit():
    print(f"[+] INITIATING RECURSIVE AUDIT: {RESEARCH_DIR}")
    files = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    
    alive_signals = []
    
    for f in files:
        print(f"[*] PROBING: {f}")
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            text = reader.pages[0].extract_text()
            
            # THE ORB FILTER: Is it dense logic or social contrast?
            # For this step, we are flagging files for YOUR final verdict.
            if "feedback" in text.lower() or "invariant" in text.lower() or "rigidity" in text.lower():
                alive_signals.append(f)
                print(f"    [>] SIGNAL DETECTED: {f}")
            else:
                print(f"    [!] NOISE FILTERED: {f}")
        except Exception as e:
            print(f"    [X] FRACTURE ON {f}: {e}")

    print(f"\n[!] AUDIT COMPLETE. {len(alive_signals)} POTENTIAL BONES IDENTIFIED.")
    print("READY FOR MANIFOLD STITCHING.")

if __name__ == '__main__':
    recursive_audit()
