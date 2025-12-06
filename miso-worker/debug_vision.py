import google.generativeai as genai
import os
import sys

def test_sight():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("❌ ERROR: GEMINI_API_KEY is missing from environment.")
        return

    print(f"🔑 Key found: {key[:4]}...{key[-4:]}")
    genai.configure(api_key=key)

    print("🔭 Attempting to list models...")
    try:
        models = list(genai.list_models())
        if not models:
            print("⚠️  SUCCESS: Connection made, but NO models returned.")
        else:
            print(f"✅ SUCCESS: Found {len(models)} models.")
            for m in models:
                if 'generateContent' in m.supported_generation_methods:
                    print(f"   - {m.name}")
    except Exception as e:
        print(f"🔥 CRITICAL FAILURE: {e}")

if __name__ == "__main__":
    test_sight()
