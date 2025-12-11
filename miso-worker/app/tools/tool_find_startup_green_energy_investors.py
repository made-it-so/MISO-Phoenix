import json

def solve(input_str):
    """
    Identifies potential green energy investors based on keywords in the input string.

    Args:
        input_str (str): A string describing the green energy startup's focus area.

    Returns:
        str: A JSON string containing lists of specialized investors, generalist investors,
             and useful platforms/resources.
    """
    investor_database = {
        # Keywords map to lists of VCs, firms, or angels known for that sector
        "solar": ["Generate Capital", "NextEra Energy", "Sunrun", "Breakthrough Energy Ventures"],
        "wind": ["Orsted Ventures", "GE Ventures", "Vestas Ventures"],
        "hydrogen": ["Plug Power Ventures", "Equinor Ventures", "ARAMCO Ventures", "Lowercarbon Capital"],
        "battery": ["Volta Energy Technologies", "The Engine", "Breakthrough Energy Ventures", "Congruent Ventures"],
        "storage": ["Volta Energy Technologies", "Breakthrough Energy Ventures", "Energy Impact Partners"],
        "carbon": ["Lowercarbon Capital", "Carbon Direct", "Khosla Ventures", "Y Combinator"],
        "capture": ["Lowercarbon Capital", "Carbon Direct", "Occidental Ventures"],
        "geothermal": ["Fervo Energy Investors", "Google (as a corporate partner)", "Chevron Technology Ventures"],
        "agriculture": ["AgFunder", "S2G Ventures", "Pontifax AgTech"],
        "agritech": ["AgFunder", "S2G Ventures", "Pontifax AgTech"],
        "nuclear": ["Third Way", "TerraPower Investors", "Fusion Industry Association (resource)"],
        "fusion": ["Helion Energy Investors", "Commonwealth Fusion Systems Investors", "Breakthrough Energy Ventures"]
    }

    generalist_investors = {
        "Top Tier VCs & Accelerators": [
            "Breakthrough Energy Ventures",
            "Lowercarbon Capital",
            "Khosla Ventures",
            "Andreessen Horowitz (a16z)",
            "Union Square Ventures (USV)",
            "Prelude Ventures",
            "Energy Impact Partners",
            "Congruent Ventures",
            "Y Combinator"
        ],
        "Platforms & Resources": [
            "AngelList (search for 'climate tech' or 'cleantech' syndicates)",
            "Crunchbase (research recent funding rounds in your sector)",
            "Climate Tech VC (newsletter and community for networking)",
            "PitchBook (data platform for private capital markets)"
        ]
    }

    found_specialized = {}
    input_lower = input_str.lower()
    
    # Check for specialized investors by keyword
    for keyword, investors in investor_database.items():
        if keyword in input_lower:
            if keyword not in found_specialized:
                 found_specialized[keyword] = set()
            for investor in investors:
                found_specialized[keyword].add(investor)

    # Convert sets to sorted lists for consistent JSON output
    for keyword in found_specialized:
        found_specialized[keyword] = sorted(list(found_specialized[keyword]))

    results = {
        "query": input_str,
        "specialized_investors_by_keyword": found_specialized if found_specialized else "No specific keyword matches found. See general list below.",
        "generalist_climate_tech_vcs_and_resources": generalist_investors
    }

    return json.dumps(results, indent=4)