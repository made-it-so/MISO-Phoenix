import arxiv
import os
import json

RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
# TARGETING THE VOID: Calibration + Uncertainty + Error-Correction
AXIOMS = ["calibration", "uncertainty", "error-correction"]

def calibration_radar():
    print("[+] INITIATING EMERGENCY CALIBRATION RADAR...")
    
    client = arxiv.Client()
    # Searching specifically for 2026 papers on calibration and uncertainty
    search = arxiv.Search(
        query = "abs:calibration AND abs:uncertainty",
        max_results = 5,
        sort_by = arxiv.SortCriterion.SubmittedDate
    )

    signals_found = 0
    for result in client.results(search):
        if result.published.year < 2026: continue
            
        summary = result.summary.lower()
        if "calibration" in summary or "uncertainty" in summary:
            print(f"[>] CALIBRATION BONE DETECTED: {result.title}")
            filename = f"CALIB_{result.entry_id.split('/')[-1]}.pdf"
            filepath = os.path.join(RESEARCH_DIR, filename)
            
            if not os.path.exists(filepath):
                print(f"    [*] INGESTING CALIBRATION ANCHOR...")
                result.download_pdf(dirpath=RESEARCH_DIR, filename=filename)
                signals_found += 1

    print(f"\n[!] RADAR COMPLETE. {signals_found} CALIBRATION BONES INGESTED.")

if __name__ == '__main__':
    calibration_radar()
