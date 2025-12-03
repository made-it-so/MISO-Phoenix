import os
import google.generativeai as genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("CRITICAL: GEMINI_API_KEY is missing.")
    exit(1)

genai.configure(api_key=api_key)

print("\n>>> AVAILABLE GEMINI MODELS:")
print("="*40)
try:
    count = 0
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
            count += 1
    if count == 0:
        print("No models found. Check API Key permissions/region.")
except Exception as e:
    print(f"Discovery Failed: {e}")
print("="*40 + "\n")
