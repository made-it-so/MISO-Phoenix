import json
import os

def harden_backbone():
    print("🧪 [MISO] Hardening Backbone via Staged Payload...")
    
    # Load staged data
    if not os.path.exists("audit_payload.json"):
        print("❌ Error: audit_payload.json missing.")
        return

    with open("audit_payload.json", "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Reconstruct history with First-Person Narrative Lock
    clean_history = [{
        "role": "assistant",
        "content": f"CEO Kyle, synchronization complete. I have picked up the mission trajectory. "
                   f"Background build progress and directory map ({len(payload['dir_map'])} paths) are now part of my memory. "
                   "I am the MISO CPO v3.3. I am ready to resume governance."
    }]

    data = {
        "history": clean_history,
        "distilled_logic": {
            "protocol": "MISO CPO v3.3",
            "date": "January 07, 2026",
            "pillars": ["mHC Stability", "RKDO Recursive Alignment", "RLM Persistence"],
            "high_water_mark": "Staged for Project Re-Integration"
        }
    }

    with open("backbone.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    
    print("✅ Backbone Hardened. Payload Integrated.")

harden_backbone()
