import json
import os
import sys

BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def adversarial_audit():
    print("[🛡️] ADVERSARIAL AUDIT: SCANNING FOR LOGIC DRIFT...")
    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    purged = 0
    # Core STEM Anchor: MIT 18.965 (Riemannian Geometry)
    stem_anchor = brain.get("HLE_18.965", {}).get("derivation", "")

    for node_id, data in list(brain.items()):
        # Check if Social/Business nodes contradict geometric stability
        if node_id.startswith(("SOC_", "HBS_")):
            content = data.get("derivation", "").lower()
            if "unstable" in content and "stability" in stem_anchor.lower():
                print(f"[⚠️] DRIFT DETECTED: {node_id} violates Geometric Axiom 18.965.")
                del brain[node_id]
                purged += 1

    with open(BUFFER, 'w', encoding='utf-8') as f:
        json.dump(brain, f, indent=4)
    print(f"[✅] AUDIT COMPLETE: {purged} nodes purged. Logic symmetry restored.")

if __name__ == "__main__":
    adversarial_audit()
