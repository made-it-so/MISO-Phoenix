import json

# Mock database of green energy investors
# In a real-world scenario, this would come from an API or a dynamic database like PitchBook or Crunchbase.
INVESTOR_DATABASE = [
    {
        "name": "Breakthrough Energy Ventures",
        "focus_areas": ["solar", "wind", "hydrogen", "carbon_capture", "grid_tech", "sustainable_materials"],
        "stage": "Seed to Growth",
        "website": "https://www.breakthroughenergy.org/investing/ventures"
    },
    {
        "name": "Congruent Ventures",
        "focus_areas": ["solar", "ev", "grid_tech", "sustainability_software", "agritech"],
        "stage": "Pre-seed to Series A",
        "website": "https://www.congruentventures.com/"
    },
    {
        "name": "Generate Capital",
        "focus_areas": ["solar", "wind", "battery_storage", "waste_management", "water_treatment"],
        "stage": "Growth / Project Finance",
        "website": "https://generatecapital.com/"
    },
    {
        "name": "Energy Impact Partners",
        "focus_areas": ["grid_tech", "ev", "cybersecurity", "sustainability_software"],
        "stage": "Series A to Growth",
        "website": "https://www.energyimpactpartners.com/"
    },
    {
        "name": "Lowercarbon Capital",
        "focus_areas": ["carbon_capture", "fusion", "geothermal", "sustainable_materials", "ocean_tech"],
        "stage": "Pre-seed to Series B",
        "website": "https://lowercarboncapital.com/"
    },
    {
        "name": "Powerhouse Ventures",
        "focus_areas": ["solar", "battery_storage", "grid_tech", "sustainability_software", "ev"],
        "stage": "Pre-seed, Seed",
        "website": "https://www.powerhouse.fund/"
    },
    {
        "name": "DBL Partners",
        "focus_areas": ["solar", "wind", "sustainable_materials", "agritech", "ev"],
        "stage": "Series B onwards",
        "website": "https://www.dbl.vc/"
    }
]

def solve(input_str):
    """
    Finds potential green energy investors based on a specific keyword or sector.

    Args:
        input_str (str): A keyword representing a green energy sector 
                         (e.g., 'solar', 'wind', 'carbon_capture', 'all').

    Returns:
        str: A JSON formatted string containing a list of matching investors or a message.
    """
    if not input_str:
        query = "all"
    else:
        # Normalize the input query: lowercase and replace spaces/hyphens with underscores
        query = input_str.lower().strip().replace(" ", "_").replace("-", "_")

    found_investors = []
    if query == "all":
        found_investors = INVESTOR_DATABASE
    else:
        for investor in INVESTOR_DATABASE:
            if query in investor["focus_areas"]:
                found_investors.append(investor)
    
    if not found_investors:
        result = {
            "query": input_str,
            "status": "No investors found matching your criteria.",
            "investors": []
        }
    else:
        result = {
            "query": input_str,
            "status": f"Found {len(found_investors)} investors for '{input_str}'.",
            "investors": found_investors
        }
        
    return json.dumps(result, indent=2)