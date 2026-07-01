import json
import os
import sys

# MISO CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def audit_governance(policy_id, system_state):
    print(f"\n[⚖️] ENFORCEMENT ACTION: POLICY {policy_id}")
    print(f"[🔍] ANALYZING STATE: {system_state}")
    
    if not os.path.exists(BUFFER):
        print("[❌] ERROR: SOVEREIGN BRAIN OFFLINE.")
        return

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    # AXIOMATIC CROSS-REFERENCE
    # Mapping system_state against HLE_18.065 (Matrix Stability)
    foundation = brain.get("HLE_18.065", {}).get("derivation", "Stability Axiom")
    
    # ENFORCEMENT LOGIC
    is_violation = "unstable" in system_state.lower() or "fail" in system_state.lower()
    
    print("-" * 50)
    if is_violation:
        print(f"VERDICT: 🚩 VIOLATION DETECTED")
        print(f"REASON : State contradicts Axiom 18.065 ({foundation[:50]}...)")
        print(f"ACTION : LOCKDOWN INITIATED.")
    else:
        print(f"VERDICT: ✅ COMPLIANT")
        print(f"ACTION : PROCEED WITH SOVEREIGN EXECUTION.")
    print("-" * 50)

if __name__ == "__main__":
    # If variables are passed via CLI: python miso_enforcer.py <policy> <state>
    if len(sys.argv) > 2:
        audit_governance(sys.argv[1], sys.argv[2])
    else:
        print("[!] Usage: python miso_enforcer.py [PolicyID] [SystemState]")
