import json
import os
from datetime import datetime

def stabilize_backbone(dir_json, log_text):
    path = "backbone.json"
    clean_history = [{
        "role": "assistant", 
        "content": f"CEO Kyle, Cockpit v3.3 stabilized. Background mission progress ingested. Map: {dir_json[:500]}... Logs: {log_text[:500]}..."
    }]
    
    data = {
        "history": clean_history,
        "distilled_logic": {
            "protocol": "MISO CPO v3.3",
            "date": "January 07, 2026",
            "pillars": ["mHC Stability", "RKDO Recursive Alignment", "RLM Persistence"],
            "target": "Background Project Re-Integration"
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("✅ Backbone Hardened with Architectural Map.")

# Receive variables from PS context
import sys
stabilize_backbone(sys.argv[1], sys.argv[2])
