import json
import os
import google.generativeai as genai

def harden_infrastructure():
    print("🛡️ [MISO] Hardening Infrastructure Cache...")
    api_key = input("Enter Gemini API Key to Verify Link: ")
    
    try:
        genai.configure(api_key=api_key)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Tiered Selection
        selection = [m for m in models if "flash" in m.lower()]
        if not selection: selection = [m for m in models if "pro" in m.lower()]
        working_model = selection[0] if selection else models[0]
        
        manifest = {
            "verified_model": working_model,
            "api_version": "v1beta",
            "last_verified": "2026-01-05",
            "status": "HARDENED"
        }
        
        with open("infra_manifest.json", "w") as f:
            json.dump(manifest, f, indent=4)
        print(f"✅ [SUCCESS] Model {working_model} cached in infra_manifest.json")
        
    except Exception as e:
        print(f"❌ [ERROR] Verification failed: {e}")

harden_infrastructure()
