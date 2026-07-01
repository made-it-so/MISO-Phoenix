import os
import json
import shutil
from pypdf import PdfReader

# PATHS
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
NOISE_DIR = r"C:\MISO_RESEARCH\00_Noise_Floor"
MASTER_PATTERN = ["feedback", "distillation", "verification", "calibration"]

def signal_purity_purge():
    print("[+] INITIATING SIGNAL PURITY PURGE...")
    
    files = [f for f in os.listdir(RESEARCH_DIR) if f.endswith('.pdf')]
    purged = 0
    remaining = 0

    for f in files:
        try:
            reader = PdfReader(os.path.join(RESEARCH_DIR, f))
            text = ""
            for i in range(min(5, len(reader.pages))):
                text += (reader.pages[i].extract_text() or "").lower()
            
            # Does this bone contain the Four-Fold Path?
            score = sum(1 for term in MASTER_PATTERN if term in text)
            
            if score < 4:
                # Sequestration
                shutil.move(os.path.join(RESEARCH_DIR, f), os.path.join(NOISE_DIR, f))
                print(f"[!] DILUTIVE BONE REMOVED: {f} (Score: {score}/4)")
                purged += 1
            else:
                print(f"[>] PURE SIGNAL RETAINED: {f}")
                remaining += 1
        except Exception as e:
            print(f"[X] FRACTURE: {f} - {e}")

    print(f"\n[!] PURGE COMPLETE.")
    print(f"    - DILUTIVE NOISE REMOVED: {purged}")
    print(f"    - PURE SIGNALS REMAINING: {remaining}")

if __name__ == '__main__':
    signal_purity_purge()
