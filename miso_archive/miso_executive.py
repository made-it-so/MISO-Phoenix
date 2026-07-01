import os
import json
import shutil

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
NOISE_DIR = r"C:\MISO_RESEARCH\00_Noise_Floor"
MANIFOLD_PATH = "miso_manifold.json"

def sovereign_executive():
    print("[+] INITIALIZING SOVEREIGN EXECUTIVE...")
    
    # Ensure Noise Floor exists
    if not os.path.exists(NOISE_DIR):
        os.makedirs(NOISE_DIR)
        print(f"[*] CREATED NOISE FLOOR: {NOISE_DIR}")

    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    files = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    print(f"[*] ANALYZING {len(files)} FILES FOR SEQUESTRATION...")

    for f in files:
        # PROTECT THE BONES (Already stitched axioms)
        if any(f in ax.get('axiom', '') for ax in manifold['axioms']):
            continue
        
        # Sequester the Noise (Based on our 0.50 threshold logic)
        # For safety, we sequester anything not explicitly flagged in our last audit
        src = os.path.join(RESEARCH_DIR, f)
        dst = os.path.join(NOISE_DIR, f)
        
        try:
            shutil.move(src, dst)
            # print(f"[!] SEQUESTERED: {f}")
        except Exception as e:
            print(f"[X] FAILED TO PURGE {f}: {e}")

    print(f"\n[!] EXECUTIVE ACTION COMPLETE.")
    print(f"    - SUBSTRATE PURIFIED: Noise moved to /00_Noise_Floor.")
    print(f"    - SYSTEM RANK SECURED: {manifold['rank']:.4f}%")

if __name__ == '__main__':
    sovereign_executive()
