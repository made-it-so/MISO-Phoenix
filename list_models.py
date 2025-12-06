import os
import google.generativeai as genai
from dotenv import load_dotenv

try:
    # Load the .env file to get the key
    load_dotenv()
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"ERROR: Could not load API key from .env file. Please check the file.")
    print(e)
    exit()

print("--- Finding all available Google AI Models ---")
print("--- (that support the 'generateContent' method) ---")

try:
    for m in genai.list_models():
        # This is the critical filter. We only want models we can
        # actually use with the 'generate_content' method.
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"\n*** API CALL FAILED ***")
    print(f"Error: {e}")
    print("Please double-check that your GOOGLE_API_KEY in the .env file is correct.")

print("\n--- Model discovery complete. ---")
