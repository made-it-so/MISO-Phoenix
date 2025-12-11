import json
import re
import time

try:
    from duckduckgo_search import DDGS
except ImportError:
    raise ImportError("The 'duckduckgo-search' library is required. Please install it with 'pip install duckduckgo-search'")

def solve(input_str: str) -> str:
    """
    Identifies potential "patient money" VC investors in a specific clean energy sub-sector
    by searching public web data for funding announcements and investor theses.

    Args:
        input_str: A string describing the clean energy sub-sector, e.g.,
                   "green hydrogen" or "long-duration energy storage".

    Returns:
        A JSON formatted string containing a list of candidate investors and the methodology.
    """

    # --- Configuration & Heuristics ---

    KNOWN_PATIENT_INVESTORS = [
        "Breakthrough Energy Ventures", "Energy Impact Partners", "Generate Capital",
        "Prime Movers Lab", "Lowercarbon Capital", "DCVC", "Temasek", "GIC",
        "Canada Pension Plan Investment Board", "Equinor Ventures", "Shell Ventures",
        "Chevron Technology Ventures", "BP Ventures", "Saudi Aramco Energy Ventures",
        "Orsted Ventures", "NextEra Energy", "The Engine", "Congruent Ventures",
        "Prelude Ventures", "Collaborative Fund", "Fifty Years", "BEV"
    ]

    VC_INDICATORS = ['Ventures', 'Capital', 'Partners', 'Group', 'Fund', 'Investments', 'Holdings', 'Equity']

    PATIENT_MONEY_KEYWORDS = [
        'long-term', 'patient capital', 'deep tech', 'hard tech', 'decarbonization',
        'impact investing', 'energy transition', 'sustainable infrastructure',
        'climate tech', 'industrial tech', 'corporate venture', 'cvc'
    ]
    
    # --- Helper Functions ---

    def _search_ddg(query: str, max_results: int = 10):
        """Performs a search on DuckDuckGo and returns results."""
        results = []
        try:
            with DDGS(timeout=10) as ddgs:
                search_results = ddgs.text(query, max_results=max_results)
                for r in search_results:
                    results.append({
                        "title": r.get('title', ''),
                        "href": r.get('href', ''),
                        "body": r.get('body', '')
                    })
        except Exception:
            # Silently fail on search error to maintain robustness
            pass 
        return results

    def _extract_investor_names(text: str):
        """Extracts potential investor names from text using heuristics."""
        found_investors = set()
        # Heuristic 1: Find known investors (case-insensitive)
        for known in KNOWN_PATIENT_INVESTORS:
            if re.search(r'\b' + re.escape(known) + r'\b', text, re.IGNORECASE):
                # Use the canonical name from the list
                if known == "BEV":
                    found_investors.add("Breakthrough Energy Ventures")
                else:
                    found_investors.add(known)

        # Heuristic 2: Look for patterns like "Name Ventures", "Name Capital"
        pattern = r'\b([A-Z][a-zA-Z\'-]+(?:\s+[A-Z][a-zA-Z\'-]+)*\s+(?:' + '|'.join(VC_INDICATORS) + r'))\b'
        matches = re.findall(pattern, text)
        for match in matches:
            investor = match.strip()
            if investor.count(' ') > 0 and investor != "Venture Capital":
                found_investors.add(investor)
        return list(found_investors)

    def _vet_investor(investor_name: str):
        """Performs a secondary search to vet if an investor is "patient"."""
        query = f'"{investor_name}" investment thesis OR portfolio'
        results = _search_ddg(query, max_results=5)
        time.sleep(0.5)  # Be polite to the search engine

        vetting_info = {
            "name": investor_name,
            "is_patient_candidate": False,
            "evidence": [],
            "type": "VC"
        }

        if investor_name in KNOWN_PATIENT_INVESTORS:
            vetting_info["is_patient_candidate"] = True
            vetting_info["evidence"].append("Is a well-known strategic/patient investor in the climate space.")

        text_to_search = " ".join([f"{r['title']} {r['body']}" for r in results])
        
        found_keywords = {kw for kw in PATIENT_MONEY_KEYWORDS if re.search(r'\b' + kw + r'\b', text_to_search, re.IGNORECASE)}

        if found_keywords:
            vetting_info["is_patient_candidate"] = True
            vetting_info["evidence"].append(f"Associated with keywords: {', '.join(sorted(list(found_keywords)))}")

        if "corporate venture" in text_to_search.lower() or "cvc" in text_to_search.lower():
            vetting_info["type"] = "Corporate VC"

        if not vetting_info["evidence"]:
            vetting_info["evidence"].append("Could not find strong evidence of a 'patient money' thesis from a quick search. Further diligence required.")

        return vetting_info

    # --- Main Logic ---

    # Step 1: Broad search for companies and investors in the specified sector
    primary_query = f'"{input_str}" funding round announcement OR investors'
    search_results = _search_ddg(primary_query, max_results=20)
    time.sleep(1)

    # Step 2: Extract all potential investor names
    all_potential_investors = set()
    for res in search_results:
        text = f"{res.get('title', '')} {res.get('body', '')}"
        investors = _extract_investor_names(text)
        for inv in investors:
            all_potential_investors.add(inv)

    # Step 2b: Fallback search if the first yields few results
    if len(all_potential_investors) < 3:
        fallback_query = f'"top climate tech investors" "{input_str}" OR "top clean energy VC funds"'
        search_results = _search_ddg(fallback_query, max_results=10)
        for res in search_results:
            text = f"{res.get('title', '')} {res.get('body', '')}"
            investors = _extract_investor_names(text)
            for inv in investors:
                all_potential_investors.add(inv)

    # Step 3: Vet each potential investor
    vetted_results = []
    # Sort for deterministic output
    for investor in sorted(list(all_potential_investors)):
        vetting_data = _vet_investor(investor)
        if vetting_data["is_patient_candidate"]:
            vetted_results.append({
                "investor_name": vetting_data["name"],
                "investor_type": vetting_data["type"],
                "reasoning": ". ".join(vetting_data["evidence"])
            })

    # Step 4: Format the final output
    if vetted_results:
        final_output = {
            "found": True,
            "search_sector": input_str,
            "methodology": "The script searches for funding announcements in the specified sector, extracts potential investor names using heuristics, and then vets each name by searching for keywords associated with 'patient capital' (e.g., long-term, deep tech, decarbonization). This is a starting point for further due diligence.",
            "patient_investor_candidates": vetted_results
        }
    else:
        final_output = {
            "found": False,
            "search_sector": input_str,
            "methodology": "The script searched for investors but could not confidently identify 'patient money' candidates based on its heuristics. The search query may be too niche, or the results did not contain enough information. Try a broader term.",
            "patient_investor_candidates": []
        }

    return json.dumps(final_output, indent=2)