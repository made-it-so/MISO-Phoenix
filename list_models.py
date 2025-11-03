import google.generativeai as genai
import os
import warnings

# Suppress the Python version warning
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    # 1. Configure the API key
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
    else:
        genai.configure(api_key=api_key)
        print("API key configured.")

        # 2. Try to list models
        print("Listing models supporting 'generateContent'...")
        print("-" * 40)

        found_models = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
                found_models = True

        if not found_models:
            print("No models supporting 'generateContent' found for this API key.")
        else:
            print("-" * 40)
            print("Success! Found usable models.")

except Exception as e:
    # 3. Print the ACTUAL error message
    print("\n--- AN ERROR OCCURRED ---")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Details: {e}")
    print("\n--- TROUBLESHOOTING ---")
    print("1. Did you enable the 'Gemini API' or 'Vertex AI API' in your Google Cloud project?")
    print("2. Is a valid billing account linked to your 'MISO Phoenix' project?")
    print("3. Did you copy the API key correctly, with no extra spaces?")
    print("4. Did you check for IP or API restrictions on the key itself?")
