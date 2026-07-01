import arxiv
import os
import json

RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
# TARGETING THE MISSING LINK: Distillation + Calibration
AXIOMS = ["distillation", "calibration"]

def bridge_radar():
    print("[+] INITIATING BRIDGE-BONE RADAR (PHASE III)...")
    
    client = arxiv.Client()
    search = arxiv.Search(
        query = "abs:distillation AND abs:calibration",
        max_results = 5,
        sort_by = arxiv.SortCriterion.SubmittedDate
    )

    signals_found = 0
    for result in client.results(search):
        # Strictly 2026
        if result.published.year < 2026:
            continue
            
        summary = result.summary.lower()
        score = sum(1 for term in AXIOMS if term in summary)
        
        if score == 2:
            print(f"[>] BRIDGE BONE DETECTED: {result.title}")
            filename = f"BRIDGE_{result.entry_id.split('/')[-1]}.pdf"
            filepath = os.path.join(RESEARCH_DIR, filename)
            
            if not os.path.exists(filepath):
                print(f"    [*] INGESTING MASTER LINK: {filename}")
                result.download_pdf(dirpath=RESEARCH_DIR, filename=filename)
                signals_found += 1

    print(f"\n[!] RADAR COMPLETE. {signals_found} BRIDGE BONES INGESTED.")

if __name__ == '__main__':
    bridge_radar()
