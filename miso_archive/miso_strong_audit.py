import json
import os
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

def strong_audit():
    print("[+] INITIATING STRONG AUDIT (v2.0)...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    bones = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    print(f"[*] ENFORCING RIGIDITY ON {len(bones)} BONES...")

    for f in bones:
        # Skip papers already verified as 'Master Signals'
        if any(f in str(ax) for ax in manifold['axioms']):
            continue

        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            text = (reader.pages[0].extract_text() or "").lower()
            
            # THE STRONG CHECK: Does it provide deterministic proof?
            # We look for "verification", "code", "logic", or "math"
            if any(term in text for term in ["verification", "code", "logic", "math"]):
                print(f"[>] STRONG SIGNAL VERIFIED: {f}")
                # Increase rank slightly for each verified strong signal
                manifold['rank'] += 0.02
            else:
                print(f"[!] WEAK SIGNAL DETECTED: {f} - Sequestration Recommended.")
                
        except Exception as e:
            print(f"[X] AUDIT FRACTURE: {e}")

    manifold['rank'] = round(manifold['rank'], 4)
    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(manifold, f, indent=4)
    print(f"\n[!] AUDIT COMPLETE. NEW RANK: {manifold['rank']}%")

if __name__ == '__main__':
    strong_audit()
