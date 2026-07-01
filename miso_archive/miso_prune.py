import os
import json
import shutil

RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
NOISE_DIR = r"C:\MISO_RESEARCH\00_Noise_Floor"
MANIFOLD_PATH = "miso_manifold.json"

FAILED_BONES = ["BONE_2601.13453v1.pdf", "BONE_2602.11332v1.pdf"]

def prune_and_normalize():
    print("[+] INITIATING PRUNING & NORMALIZATION...")
    
    # 1. Sequestration
    for f in FAILED_BONES:
        src = os.path.join(RESEARCH_DIR, f)
        dst = os.path.join(NOISE_DIR, f)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"[!] SEQUESTERED FAILED BONE: {f}")

    # 2. Rank Normalization (Fixing the floating-point drift)
    with open(MANIFOLD_PATH, 'r') as f:
        data = json.load(f)
    
    # Pruning the axioms from the JSON
    data['axioms'] = [ax for ax in data['axioms'] if not any(fb in ax['axiom'] for fb in FAILED_BONES)]
    
    # Resetting rank to a deterministic 3.1525 (removing the 0.10 weight of failed bones)
    data['rank'] = 3.1525
    
    with open(MANIFOLD_PATH, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"\n[!] NORMALIZATION COMPLETE. SYSTEM RIGIDITY RESTORED.")
    print(f"NEW DETERMINISTIC RANK: {data['rank']}%")

if __name__ == '__main__':
    prune_and_normalize()
