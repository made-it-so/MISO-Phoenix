import google.generativeai as genai
import sys

def get_model_arsenal(api_key):
    if not api_key: return {}
    
    arsenal = {"flash": None, "pro": None}
    try:
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Hunt for specific models
        for m in available:
            if "flash" in m and not arsenal["flash"]:
                arsenal["flash"] = genai.GenerativeModel(m)
                print(f">> ⚡ ARSENAL: Added Flash ({m})")
            elif ("pro" in m or "ultra" in m) and not arsenal["pro"]:
                arsenal["pro"] = genai.GenerativeModel(m)
                print(f">> 🧠 ARSENAL: Added Pro ({m})")
        
        # Fallbacks
        if not arsenal["pro"] and available: arsenal["pro"] = genai.GenerativeModel(available[0])
        if not arsenal["flash"]: arsenal["flash"] = arsenal["pro"]
        
    except Exception as e:
        print(f">> ❌ ARSENAL ERROR: {e}")
    
    return arsenal
