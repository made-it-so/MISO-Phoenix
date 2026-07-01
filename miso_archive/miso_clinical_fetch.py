import requests
import xml.etree.ElementTree as ET
import json
import time

def fetch_medical_evidence(query, email="miso_admin@example.com"):
    print(f"\n[🔬] SEARCHING PUBMED/PMC FOR: {query}")
    
    # 1. ESEARCH: Find the IDs (PMIDs) for the query
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": 1,
        "retmode": "json",
        "tool": "MISO_Sovereign_Gate",
        "email": email
    }
    
    try:
        r = requests.get(search_url, params=search_params)
        pmids = r.json().get("esearchresult", {}).get("idlist", [])
        
        if not pmids:
            return {"Error": "No matching clinical evidence found."}

        # 2. EFETCH: Get the Abstract/Details for the top ID
        fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        fetch_params = {
            "db": "pubmed",
            "id": pmids[0],
            "retmode": "xml",
            "tool": "MISO_Sovereign_Gate",
            "email": email
        }
        
        response = requests.get(fetch_url, params=fetch_params)
        root = ET.fromstring(response.content)

        # 3. PARSE: Extract Clinical Intelligence
        article = root.find(".//Article")
        title = article.find(".//ArticleTitle").text if article is not None else "N/A"
        abstract_parts = article.findall(".//AbstractText")
        abstract = " ".join([p.text for p in abstract_parts if p.text])

        return {
            "Status": "SUCCESS",
            "Title": title,
            "Abstract_Snippet": abstract[:500] + "...",
            "PMID": pmids[0],
            "Context": "STEM/Law Evidence Verification"
        }
    except Exception as e:
        return {"Error": f"Clinical Fetch Failed: {str(e)}"}

if __name__ == "__main__":
    # TEST: Use MISO to verify a clinical claim for a legal case
    # Adding a 2026 filter to ensure real-time relevance
    evidence = fetch_medical_evidence("Adverse effects of AI-driven drug titration 2026")
    print(json.dumps(evidence, indent=4))
