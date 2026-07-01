import os
import shutil

RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
NOISE_DIR = r"C:\MISO_RESEARCH\00_Noise_Floor"

# THE HIGH-DENSITY PENTAD (Score 2/4 and 3/4)
RECLAIM_TARGETS = [
    "2601.07264v1.pdf",              # Score 3/4
    "2602.17633v1.pdf",              # Score 3/4
    "BRIDGE_2602.07840v2.pdf",       # Score 3/4
    "BRIDGE_2602.12687v1.pdf",       # Score 2/4 (Master Link)
    "Ahrlund-Richter et al Neuron 2026.pdf" # The Biological Anchor
]

def reconstitute_core():
    print("[+] RECONSTITUTING THE PENTAD...")
    
    for f in RECLAIM_TARGETS:
        src = os.path.join(NOISE_DIR, f)
        dst = os.path.join(RESEARCH_DIR, f)
        
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"[>] RESTORED: {f}")
            except Exception as e:
                print(f"[X] FRACTURE: {f} - {e}")
        else:
            print(f"[!] BONE NOT FOUND: {f}")

    print(f"\n[!] CORE RECONSTITUTED. 5 BONES ACTIVE.")

if __name__ == '__main__':
    reconstitute_core()
