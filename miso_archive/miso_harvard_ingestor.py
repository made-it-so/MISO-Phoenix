import json
import os
import sys

# CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
HARVARD_DATA = r"C:\MISO_RESEARCH\HARVARD"

def anchor_harvard_humanities():
    print(f"\n[🏛️] INGESTING HARVARD HUMANITIES KERNELS: {HARVARD_DATA}")
    
    if not os.path.exists(HARVARD_DATA):
        os.makedirs(HARVARD_DATA)
        print(f"[!] Path created. Drop Harvard course transcripts in {HARVARD_DATA}")
        return

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    # Core Harvard humanities pillars for the 2026 World Model
    harvard_pillars = {
        "JUSTICE": "Sandel's Moral Philosophy & Common Good",
        "LEADERSHIP": "Foundational Principles of Adaptive Leadership",
        "BIOETHICS": "Legal and Ethical Reasoning in Biotechnology",
        "RHETORIC": "The Art of Persuasive Writing and Logic"
    }
    
    count = 0
    for file in os.listdir(HARVARD_DATA):
        if file.endswith(".txt"):
            node_id = f"HVD_{2000 + count}"
            brain[node_id] = {
                "domain": "Harvard/Humanities",
                "source": file,
                "status": "ANCHORED_HUMANITIES",
                "axiom": "Socratic Reasoning / Ethical Governance"
            }
            count += 1

    with open(BUFFER, 'w', encoding='utf-8') as f:
        json.dump(brain, f, indent=4)
    
    print(f"[✅] SUCCESS: {count} Harvard Humanities nodes added to the MISO brain.")

if __name__ == "__main__":
    anchor_harvard_humanities()
