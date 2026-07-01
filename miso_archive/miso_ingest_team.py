import json
import os

def ingest_specialists():
    print("📥 [INGEST] Mobilizing Specialist Experts...")
    
    # Ensure the team structure exists
    if os.path.exists("team_backbone.json"):
        with open("team_backbone.json", "r") as f:
            team = json.load(f)
    else:
        team = {"CPO": {"history": []}, "CFO": {"history": []}, "SEC": {"history": []}, "STB": {"history": []}}

    # Define the mapping of files to experts
    # IMPORTANT: Ensure you have these .txt files ready in your directory!
    mappings = {
        "CFO": "chat_cfo_settlement.txt",
        "SEC": "chat_security_audit.txt",
        "STB": "chat_stability_council.txt"
    }

    for expert, filename in mappings.items():
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                history_text = f.read()
                # Inject as a single 'Institutional Memory' block
                team[expert]["history"] = [{"role": "assistant", "content": f"INSTITUTIONAL MEMORY LOADED: {history_text}"}]
                print(f"✅ Ingested {expert} memory from {filename}")
        else:
            print(f"⚠️ Missing {filename}. Skipping {expert} ingestion.")

    with open("team_backbone.json", "w") as f:
        json.dump(team, f, indent=4)
    print("🏁 [FINISH] Specialist Mobilization Complete.")

ingest_specialists()
