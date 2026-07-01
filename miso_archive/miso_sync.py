import json
import os

def sync_context():
    print("🧠 [SYNC] Injecting Strategic State into local Backbone...")
    
    # The "Summary of Now" to bridge the two chats
    state_summary = {
        "role": "assistant",
        "content": "CEO Kyle, I am now fully synced. I have the context of our web session: "
                   "1. We established the Gemini -> CLI -> UI workflow as your sovereign safeguard. "
                   "2. We confirmed the MoE Council (Security, Fiscal, Stability) audits all code for you. "
                   "3. Client Bravo is staged with a $1,047 leak and our 20% fee is locked. "
                   "4. We are currently in the 'Sovereign Cockpit v3.7'. "
                   "How shall we proceed with the Bravo Revenue Capture?"
    }
    
    if os.path.exists("backbone.json"):
        with open("backbone.json", "r") as f:
            data = json.load(f)
    else:
        data = {"history": [], "distilled_logic": {}}
    
    # Append the state summary to the history so it appears in the Chat UI
    data["history"].append(state_summary)
    
    with open("backbone.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print("✅ [SYNC] Cognitive Bridge Established. Refresh your Hub.")

sync_context()
