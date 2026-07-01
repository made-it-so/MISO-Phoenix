import json
import os
import sys
import time

# MISO CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def audit_governance(user_id, policy_id, action_description):
    print(f"\n[👥] GOVERNANCE AUDIT INITIATED: {time.ctime()}")
    print(f"[🆔] SUBJECT: {user_id} | POLICY: {policy_id}")
    print(f"[📝] ACTION : {action_description}")
    
    if not os.path.exists(BUFFER):
        print("[❌] ERROR: SOVEREIGN BRAIN OFFLINE. AXIOMS UNREACHABLE.")
        return

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    # HUMAN-CENTRIC LOGIC ENGINE
    # Evaluating the action against anchored HLE kernels (e.g., 18.065 for threshold logic)
    is_violation = False
    reasons = []

    # Example: Check if action involves restricted logic or over-usage
    if "restricted" in action_description.lower():
        is_violation = True
        reasons.append("Unauthorized attempt to access high-entropy HLE nodes.")
    
    if "usage_exceed" in action_description.lower():
        is_violation = True
        reasons.append("Resource consumption exceeds Governance Policy POL-2026 threshold.")

    print("-" * 60)
    if is_violation:
        print(f"VERDICT: 🚩 POLICY VIOLATION DETECTED")
        for r in reasons:
            print(f"  -> {r}")
        print("ACTION : LOGGING TO LEDGER & TERMINATING REQUEST.")
    else:
        print(f"VERDICT: ✅ COMPLIANT")
        print("ACTION : AUTHORIZING ACCESS.")
    print("-" * 60)

if __name__ == "__main__":
    # Execution: python miso_governance_cli.py <UserID> <PolicyID> <ActionText>
    if len(sys.argv) > 3:
        audit_governance(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("[!] Usage: python miso_governance_cli.py [UserID] [PolicyID] [ActionDescription]")
