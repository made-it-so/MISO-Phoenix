import os
import json
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
MANIFOLD_PATH = "miso_manifold.json"

# AXIOM WEIGHTS (from our previous stitches)
AXIOMS = [
    "feedback",      # Ahrlund-Richter (ORB/ACA)
    "distillation",  # SDPO (Self-Teacher)
    "calibration",   # Tokyo/CMU (Verification)
    "invariant"      # Structural Mass
]

def autonomous_purge():
    print("[+] INITIATING SYSTEMATIC PURGE...")
    
    with open(MANIFOLD_PATH, 'r') as f:
        manifold = json.load(f)

    files = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    purged_count = 0
    signal_count = 0

    for f in files:
        # Skip the bones we already harvested
        if any(f in ax.get('axiom', '') for ax in manifold['axioms']):
            continue

        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            # Sample first two pages for density
            text = (reader.pages[0].extract_text() or "") + (reader.pages[1].extract_text() or "")
            text = text.lower()

            # The ORB Filter Logic
            matches = [term for term in AXIOMS if term in text]
            rigidity_score = len(matches) / len(AXIOMS)

            if rigidity_score > 0.4:
                print(f"[>] SIGNAL: {f} (Score: {rigidity_score:.2f})")
                signal_count += 1
            else:
                # The Purge
                purged_count += 1
                # print(f"[!] PURGED: {f} (Noise floor reached)")
        except Exception as e:
            print(f"[X] FRACTURE: {f} - {e}")

    print(f"\n[!] PURGE COMPLETE.")
    print(f"    - NOISE REDUCED: {purged_count} files.")
    print(f"    - NEW SIGNALS IDENTIFIED: {signal_count}")
    print(f"    - CURRENT SYSTEM RANK: {manifold['rank']:.4f}%")

if __name__ == '__main__':
    autonomous_purge()
