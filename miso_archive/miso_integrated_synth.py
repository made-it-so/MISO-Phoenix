import json
import os
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

# THE FOUR-FOLD PATH (2.0% Core Invariants)
MASTER_PATTERN = ["feedback", "distillation", "verification", "calibration"]

def integrated_synthesis():
    print("[+] INITIATING INTEGRATED SYNTHESIS...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    bones = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    print(f"[*] AGGREGATING DENSITY ACROSS {len(bones)} BONES...")

    collective_logic = {term: False for term in MASTER_PATTERN}

    for f in bones:
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            # Scan deeper (first 8 pages) to overcome keyword "weakness"
            text = ""
            for i in range(min(8, len(reader.pages))):
                text += (reader.pages[i].extract_text() or "").lower()
            
            for term in MASTER_PATTERN:
                if term in text:
                    collective_logic[term] = True
        except Exception as e:
            print(f"[X] FRACTURE: {f} - {e}")

    # SCORING THE COLLECTIVE
    found_terms = [t for t, found in collective_logic.items() if found]
    coverage = len(found_terms) / len(MASTER_PATTERN)

    print(f"[>] COLLECTIVE COVERAGE: {len(found_terms)}/4 ({coverage*100:.1f}%)")

    if coverage == 1.0:
        print("[!] SUCCESS: DISTRIBUTED INVARIANT REACHED.")
        # Trigger the 3.0% threshold jump
        manifold['rank'] = 3.0025 
        print(f"    - ALL 2026 INVARIANTS PRESENT IN PENTAD.")
    else:
        print(f"[!] PARTIAL COVERAGE. MISSING: {[t for t, found in collective_logic.items() if not found]}")
        manifold['rank'] += 0.05

    manifold['rank'] = round(manifold['rank'], 4)
    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(manifold, f, indent=4)
    
    print(f"\n[!] SYNTHESIS COMPLETE. NEW RANK: {manifold['rank']}%")

if __name__ == '__main__':
    integrated_synthesis()
