import json
import os

def mobilize_rd():
    path = "team_backbone.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        
        # Explicitly add the R&D Expert if missing
        if "R&D" not in data:
            data["R&D"] = {
                "history": [], 
                "role": "Recursive Research & Development Specialist"
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            print("✅ [MISO] R&D Lab physically spawned in backbone.json")
        else:
            print("ℹ️ [MISO] R&D Lab already detected in backbone.")
    else:
        print("❌ Error: team_backbone.json not found.")

mobilize_rd()
