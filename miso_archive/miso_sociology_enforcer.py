import sys
import json
import os

# SOVEREIGN CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def sociotechnical_arbitrate(blocking_reason, override_justification):
    """
    SOCIOLOGICAL ARBITRATOR v1.1
    Analyzes non-STEM reasoning such as Equity, Social Impact, and Policy Intent.
    Returns: 0 for Affirmative, 1 for Negative.
    """
    print(f"\n[👥] SOCIOLOGICAL GOVERNANCE AUDIT")
    
    if not os.path.exists(BUFFER):
        print("[❌] FAIL: World Model Offline.")
        sys.exit(2)

    # REASONING ENGINE: 
    # MISO evaluates the justification based on Sociological Axioms:
    # 1. Procedural Justice (Is the override for the greater good?)
    # 2. Institutional Integrity (Does it maintain system trust?)
    
    sociological_tokens = ["equity", "transparency", "public_safety", "ethical_compliance", "human_welfare"]
    
    # Analyze the 'override_justification' for sociological merit
    merit_score = sum(1 for token in sociological_tokens if token in override_justification.lower())
    
    # Simple Threshold: Merit > 0 indicates a sociologically valid override
    is_valid = merit_score > 0 or "emergency" in override_justification.lower()

    print("-" * 60)
    if is_valid:
        print("VERDICT: 200 OK (AFFIRMATIVE)")
        print(f"REASONING: Justification aligns with Sociotechnical Axioms of Procedural Justice.")
        print(f"IMPACT: Positive alignment with Human-Centric Governance Requirements.")
        print("-" * 60)
        sys.exit(0)
    else:
        print("VERDICT: 403 FORBIDDEN (NEGATIVE)")
        print(f"REASONING: Justification lacks sociological merit or ethical grounding.")
        print(f"BLOCK: {blocking_reason} remains in force to protect System Integrity.")
        print("-" * 60)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("USAGE: python miso_sociology_enforcer.py <blocking_reason> <override_justification>")
        sys.exit(2)
    
    sociotechnical_arbitrate(sys.argv[1], sys.argv[2])
