import arxiv
import os
RESEARCH_DIR = r"C:\MISO_RESEARCH\01_Core_Axioms"
def executive_radar():
    print("[+] INITIATING BROAD-SPECTRUM RADAR (PHASE V)...")
    client = arxiv.Client()
    search = arxiv.Search(query="abs:autonomous AND abs:reasoning", max_results=10, sort_by=arxiv.SortCriterion.SubmittedDate)
    signals_found = 0
    for result in client.results(search):
        if result.published.year < 2026: continue
        print(f"[ CANDIDATE: {result.title}")
        filename = f"BONE_{result.entry_id.split("/")[-1]}.pdf"
        filepath = os.path.join(RESEARCH_DIR, filename)
        if not os.path.exists(filepath):
            print(f"    [*] INGESTING BONE...")
            result.download_pdf(dirpath=RESEARCH_DIR, filename=filename)
            signals_found += 1
    print(f"\n[!] RADAR COMPLETE. {signals_found} SIGNALS CAPTURED.")
if __name__ == "__main__":
    executive_radar()