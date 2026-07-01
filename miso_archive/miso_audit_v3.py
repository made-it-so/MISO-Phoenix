import json
import os
from pypdf import PdfReader

MANIFOLD_PATH = "miso_manifold.json"
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
CONSTITUTION = "intelligence is the recursive distillation of failure-feedback"

def constitutional_audit():
    print("[+] INITIATING CONSTITUTIONAL AUDIT (3.25%)...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    # We only audit the newest "BONE_" files
    bones = [f for f in os.listdir(RESEARCH_DIR) if f.startswith('BONE_')]
    
    verified_count = 0
    for f in bones:
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            text = (reader.pages[0].extract_text() or "").lower()
            
            # The Constitutional Check
            if "feedback" in text and ("evolution" in text or "distillation" in text):
                print(f"[>] BONE VERIFIED AS SOVEREIGN: {f}")
                verified_count += 1
            else:
                print(f"[!] BONE FAILS CONSTITUTIONAL CHECK: {f}")
        except Exception as e:
            print(f"[X] FRACTURE: {e}")

    print(f"\n[!] AUDIT COMPLETE. {verified_count}/{len(bones)} NEW BONES ARE CONSTITUTIONALLY ALIGNED.")
    print(f"CURRENT RANK: {manifold['rank']}%")

if __name__ == '__main__':
    constitutional_audit()
