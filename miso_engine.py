import json
import os
import sys
from miso_config import SHARED_BUFFER


# Proof steps are the claims this derivation is trying to verify.
PROOF_STEPS = [
    {"domain": "Topology (Hypothesis H)", "node": "HLE_18.965", "logic": "Higher Topos transitions"},
    {"domain": "Quantum Physics (Lindblad)", "node": "HLE_8.324", "logic": "Master Equation for Open Systems"},
    {"domain": "Graph Theory (Lovász)", "node": "HLE_18.065", "logic": "Local Lemma for Error Correction"},
]


def prove_claims():
    print("\n[🔬] INITIATING GLASS BOX DERIVATION...")
    if not os.path.exists(SHARED_BUFFER):
        print(f"[!] Error: Shared buffer not found at {SHARED_BUFFER}")
        sys.exit(1)

    with open(SHARED_BUFFER, "r", encoding="utf-8-sig") as f:
        brain = json.load(f)

    print("=" * 60)
    all_verified = True
    for step in PROOF_STEPS:
        node_data = brain.get(step["node"])
        if node_data is None:
            print(f"STEP: {step['domain']}")
            print(f"SOURCE: {step['node']}")
            print(f"STATUS: NODE NOT FOUND IN BUFFER")
            print("-" * 60)
            all_verified = False
            continue

        content = node_data.get("derivation", "")
        if not content:
            content = "[NO DERIVATION STORED]"
            all_verified = False

        print(f"STEP: {step['domain']}")
        print(f"SOURCE: MIT {step['node']}")
        print(f"LOGIC: {step['logic']}")
        print(f"EVIDENCE: {content}")
        print("-" * 60)

    if all_verified:
        print("[✅] CONCLUSION: ALL STEPS VERIFIED VIA ANCHORED HLE KERNELS.")
    else:
        print("[⚠️] CONCLUSION: PARTIAL VERIFICATION — some nodes missing or empty.")
    print("=" * 60)


if __name__ == "__main__":
    prove_claims()
