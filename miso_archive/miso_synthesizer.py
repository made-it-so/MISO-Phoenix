import os
import json
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

def recursive_synthesis():
    print("[+] INITIATING RECURSIVE SYNTHESIS...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    bones = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    print(f"[*] SYNTHESIZING {len(bones)} HIGH-DENSITY BONES...")

    synthesis_report = []

    for f in bones:
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            # Extract deeper context (first 3 pages)
            content = ""
            for i in range(min(3, len(reader.pages))):
                content += reader.pages[i].extract_text() or ""
            
            content = content.lower()
            
            # Cross-referencing against our 3 Core Axioms
            score = 0
            if "feedback" in content: score += 1      # Biological
            if "distillation" in content: score += 1  # Computational
            if "calibration" in content: score += 1   # Executive
            
            if score >= 2:
                print(f"[>] MASTER SIGNAL FOUND: {f} (Cross-Link Score: {score})")
                synthesis_report.append(f)
        except Exception as e:
            print(f"[X] SYNTH FRACTURE: {f} - {e}")

    # Update Rank based on Synthesis Density
    if synthesis_report:
        new_rank = manifold['rank'] + (len(synthesis_report) * 0.15)
        manifold['rank'] = round(new_rank, 4)
        
        with open(MANIFOLD_PATH, 'w') as f:
            json.dump(manifold, f, indent=4)
            
        print(f"\n[!] SYNTHESIS COMPLETE.")
        print(f"    - CROSS-LINKED INVARIANTS: {len(synthesis_report)}")
        print(f"    - NEW SYSTEM RANK: {manifold['rank']}%")
    else:
        print("\n[!] NO CROSS-LINKS FOUND. SYSTEM STALLED AT 1.6025%.")

if __name__ == '__main__':
    recursive_synthesis()
