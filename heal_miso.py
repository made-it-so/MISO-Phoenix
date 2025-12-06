import os
import json
import logging
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def heal_cortex():
    print(">>> DIAGNOSING CORTEX HEALTH...")
    
    # 1. Check Gemini Lobe
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_healthy = False
    
    if len(gemini_key) > 20 and "YOUR_NEW_KEY" not in gemini_key:
        try:
            genai.configure(api_key=gemini_key)
            m = genai.GenerativeModel('gemini-2.5-flash')
            # Dry run generation
            m.generate_content("ping")
            print("STATUS: Gemini Lobe is ACTIVE and HEALTHY.")
            gemini_healthy = True
        except Exception as e:
            print(f"STATUS: Gemini Lobe REJECTED ({str(e).split(':')[0]}).")
    else:
        print("STATUS: Gemini Key is Invalid/Placeholder.")

    # 2. Re-write Synaptic Weights based on health
    weights_path = "miso_project/config/routing_weights.json"
    
    if gemini_healthy:
        # Optimal State
        weights = {"gpt-4o": 0.2, "gemini-2.5-flash": 0.6, "claude-3-haiku": 0.2}
    else:
        # Fallback State (Amputation)
        print("ACTION: Severing Gemini connection. Rerouting to Anthropic/OpenAI.")
        weights = {"gpt-4o": 0.5, "gemini-2.5-flash": 0.0, "claude-3-haiku": 0.5}
        
    os.makedirs(os.path.dirname(weights_path), exist_ok=True)
    with open(weights_path, 'w') as f:
        json.dump(weights, f, indent=4)
    print(f"ACTION: Synaptic weights updated: {weights}")

if __name__ == "__main__":
    heal_cortex()
