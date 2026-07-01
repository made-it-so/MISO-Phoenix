import json
import os
import sys
import hashlib

# CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def run_diagnostic():
    print(f"\n[🛡️] MISO BLACK-BOX DIAGNOSTIC: STARTING...")
    
    if not os.path.exists(BUFFER):
        print("[❌] FATAL: Mainframe Buffer missing. Reconnect immediately.")
        sys.exit(1)

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    total_nodes = len([k for k in brain.keys() if k.startswith("HLE_") or k.startswith("SOC_") or k.startswith("HBS_")])
    corrupted = 0
    verified = 0

    print(f"[📊] SCANNING {total_nodes} ANCHORED NODES...")

    for node_id, data in brain.items():
        if not isinstance(data, dict): continue
        
        # Check 1: Evidence Grounding Presence
        if "derivation" not in data or len(data["derivation"]) < 10:
            print(f"  [!] Node {node_id}: Missing First-Principles Derivation.")
            corrupted += 1
            continue
            
        # Check 2: Domain Integrity (e.g., Ensuring HBS nodes have 'Business' logic)
        if node_id.startswith("HBS_") and "business" not in str(data).lower() and "ai" not in str(data).lower():
            print(f"  [!] Node {node_id}: Domain Mismatch. Non-business logic found in HBS cluster.")
            corrupted += 1
            continue

        verified += 1

    health_score = (verified / total_nodes) * 100 if total_nodes > 0 else 0
    
    print("-" * 60)
    print(f"[✅] DIAGNOSTIC COMPLETE")
    print(f"    - Nodes Verified: {verified}")
    print(f"    - Nodes Flagged : {corrupted}")
    print(f"    - Health Score  : {health_score:.2f}%")
    print("-" * 60)

    if health_score < 95:
        print("[⚠️] WARNING: Logic Drift exceeds safety thresholds. Run 'miso_reconnect.py'.")
    else:
        print("[🚀] STATUS: APEX-SOVEREIGN MAINTAINED. Ready for offline execution.")

if __name__ == "__main__":
    run_diagnostic()
