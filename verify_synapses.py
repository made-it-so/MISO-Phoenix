import os
import logging
from typing import List, Tuple

# Configure Drivers
import openai
from anthropic import Anthropic
import google.generativeai as genai

# Setup Logger
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("miso.diagnostic")

def check_openai() -> List[Tuple[str, str]]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return [("OpenAI", "MISSING API KEY")]
    
    results = []
    client = openai.OpenAI(api_key=key)
    # Test specific models used in MISO V71
    for model in ["gpt-4o", "gpt-3.5-turbo"]:
        try:
            client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5
            )
            results.append((model, "ACTIVE"))
        except Exception as e:
            err = str(e).split(" - ")[0] # Shorten error
            results.append((model, f"FAILED: {err}"))
    return results

def check_anthropic() -> List[Tuple[str, str]]:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return [("Anthropic", "MISSING API KEY")]
    
    results = []
    client = Anthropic(api_key=key)
    # Test specific models used in MISO V71
    # Note: Using exact model identifiers
    for model, name in [("claude-3-haiku-20240307", "claude-3-haiku"), ("claude-3-opus-20240229", "claude-3-opus")]:
        try:
            client.messages.create(
                model=model,
                max_tokens=5,
                messages=[{"role": "user", "content": "ping"}]
            )
            results.append((name, "ACTIVE"))
        except Exception as e:
            err = str(e).split(" - ")[0]
            results.append((name, f"FAILED: {err}"))
    return results

def check_google() -> List[Tuple[str, str]]:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return [("Google Gemini", "MISSING API KEY")]
    
    results = []
    genai.configure(api_key=key)
    for model in ["gemini-1.5-flash", "gemini-1.5-pro"]:
        try:
            m = genai.GenerativeModel(model)
            m.generate_content("ping")
            results.append((model, "ACTIVE"))
        except Exception as e:
            err = str(e).split(" - ")[0]
            results.append((model, f"FAILED: {err}"))
    return results

if __name__ == "__main__":
    print("\n>>> MISO SYNAPTIC DIAGNOSTIC REPORT")
    print("="*40)
    
    all_checks = []
    all_checks.extend(check_openai())
    all_checks.extend(check_anthropic())
    all_checks.extend(check_google())
    
    for model, status in all_checks:
        # Visual formatting
        color = "\033[92m" if "ACTIVE" in status else "\033[91m"
        reset = "\033[0m"
        print(f"{model:<20} : {color}{status}{reset}")
    
    print("="*40)
    
    # Validation for Cortex Weights
    active_models = [m for m, s in all_checks if "ACTIVE" in s]
    if not active_models:
        print("\nCRITICAL: No active lobes detected. The Cortex is vegetative.")
    else:
        print(f"\nOperational Lobes: {len(active_models)}/{len(all_checks)}")
        print("Recommendation: Update routing_weights.json to favor ACTIVE models.")

