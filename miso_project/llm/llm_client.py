import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict

# Load environment variables
load_dotenv(os.path.join(os.getenv('GIT_ROOT', '.'), '.env'))

API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

def get_llm_response(persona_prompt: str, context_prompt: str, model_provider: Dict) -> str:
    '''
    Generates a response from the LLM based on the persona, context,
    and the specified model provider.
    '''
    
    provider_type = model_provider.get("provider", "google_api")
    model_name = model_provider.get("model_name", "gemini-2.5-flash-preview-09-2025")
    
    # CRITICAL FIX: Make the check more robust
    is_simple_mypy_bug = "stats.py" in context_prompt and "type annotation" in context_prompt

    # --- SIMULATED OLLAMA PROVIDER (Tier 2: Lizard) ---
    if provider_type == "ollama":
        print(f"LLM: Simulating call to Ollama (Model: {model_name})")
        
        # This is the "dumb model" check
        if "TypeError" in context_prompt and "utils.py" in context_prompt:
            print(f"LLM (Ollama): Detected complex multi-file bug. Simulating failure.")
            return "[]"
        
        # This is the "cheap model success" check
        if is_simple_mypy_bug:
            print(f"LLM (Lizard 🦎): Detected simple mypy error. Simulating fix.")
            # CRITICAL FIX: Use json.dumps to create a valid, single-line JSON string
            fix_data = [
                {
                    "filename": "stats.py",
                    "code": "from typing import List\n\ndef calculate_mean(l: List[float]) -> float:\n    if not l:\n        return 0.0\n    return sum(l) / len(l)\n"
                }
            ]
            return json.dumps(fix_data)
        
        # Fallback for other simple Ollama calls
        print(f"LLM (Ollama): Simulating simple fix... (Returning empty for test)")
        return "[]" # Return empty to escalate if it's not the bug we're testing
    
    # --- GOOGLE AI API PROVIDER (Tiers 4 & 5) ---
    if not API_KEY:
        raise EnvironmentError("GOOGLE_API_KEY not found in .env file.")

    print(f"LLM: Calling Google AI API (Model: {model_name})")
    try:
        model = genai.GenerativeModel(model_name)
        full_prompt = f"{persona_prompt}\n\n{context_prompt}"
        response = model.generate_content(full_prompt)
        
        if not response.parts:
            print("LLM Error: Received empty response.")
            return "[]"
        return response.text
    except Exception as e:
        print(f"CRITICAL: LLM call failed: {e}")
        return "[]"
