import json
import os

# CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
HBS_DIR = r"C:\MISO_RESEARCH\HBS"

def anchor_hbs_business_logic():
    print(f"\n[📈] INGESTING HBS BUSINESS AXIOMS: {HBS_DIR}")
    
    if not os.path.exists(HBS_DIR):
        os.makedirs(HBS_DIR)
        print(f"[!] Path created. Drop HBS Working Knowledge PDFs/Text in {HBS_DIR}")
        return

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    # Core 2026 HBS Pillars
    hbs_pillars = ["agentic ai", "talent density", "algorithmic bias", "change fitness"]
    
    count = 0
    for file in os.listdir(HBS_DIR):
        if file.endswith(".txt"):
            with open(os.path.join(HBS_DIR, file), 'r', encoding='utf-8') as f:
                content = f.read().lower()
                for pillar in hbs_pillars:
                    if pillar in content:
                        node_id = f"HBS_{3000 + count}"
                        brain[node_id] = {
                            "domain": "HBS/Business Strategy",
                            "axiom": pillar.upper(),
                            "derivation": f"HBS 2026 Research: {content[:150]}...",
                            "status": "ANCHORED_BUSINESS"
                        }
                        count += 1

    with open(BUFFER, 'w', encoding='utf-8') as f:
        json.dump(brain, f, indent=4)
    print(f"[✅] SUCCESS: {count} HBS Business Axioms added to MISO.")

if __name__ == "__main__":
    anchor_hbs_business_logic()
