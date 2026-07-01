import json
import os
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

def superior_synthesis():
    print("[+] INITIATING SUPERIOR INVARIANT SYNTHESIS...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    bones = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    
    # THE MASTER PATTERN: Feedback + Distillation + Verification + Calibration
    master_pattern = ["feedback", "distillation", "verification", "calibration"]
    hit_map = {term: 0 for term in master_pattern}

    for f in bones:
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            text = ""
            for i in range(min(5, len(reader.pages))):
                text += (reader.pages[i].extract_text() or "").lower()
            
            for term in master_pattern:
                if term in text:
                    hit_map[term] += 1
        except Exception as e:
            print(f"[X] FRACTURE DURING SCAN: {e}")

    # Determine if a Superior Invariant exists (all terms present in > 60% of bones)
    threshold = len(bones) * 0.6
    superior_terms = [t for t, count in hit_map.items() if count >= threshold]
    
    if len(superior_terms) == len(master_pattern):
        print("[>] SUPERIOR INVARIANT DETECTED: The Four-Fold Path of 2026.")
        manifold['rank'] += 0.25 # Significant jump for full alignment
    else:
        print(f"[!] PARTIAL ALIGNMENT: {len(superior_terms)}/4 terms reached threshold.")
        manifold['rank'] += 0.05

    manifold['rank'] = round(manifold['rank'], 4)
    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(manifold, f, indent=4)
    
    print(f"\n[!] SYNTHESIS COMPLETE. NEW RANK: {manifold['rank']}%")

if __name__ == '__main__':
    superior_synthesis()
