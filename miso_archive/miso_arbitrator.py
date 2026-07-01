import sys
import json
import os

# SOVEREIGN CONFIG
BUFFER = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"

def arbitrate(blocking_reason, override_justification):
    """
    AXIOMATIC ARBITRATOR v1.2 (Post-Sync)
    Enforces STEM (MIT) and Sociotechnical (Harvard/HBS) Governance.
    Returns Exit Code 0 (200 OK) or 1 (403 Forbidden).
    """
    if not os.path.exists(BUFFER):
        print("[❌] FAIL: World Model Buffer Missing.")
        sys.exit(2)

    with open(BUFFER, 'r', encoding='utf-8-sig') as f:
        brain = json.load(f)

    print(f"\n[⚖️] ARBITRATION: {blocking_reason} vs. {override_justification}")

    # REASONING ENGINE
    # STEM Tokens (MIT 18.065 / 8.333)
    stem_tokens = ["emergency", "safety", "critical_failure", "stability"]
    # Sociotechnical Tokens (Harvard Justice / HBS Agentic)
    social_tokens = ["transparency", "equity", "agentic_orchestration", "human_welfare", "audit"]
    
    combined_tokens = stem_tokens + social_tokens
    
    is_valid = any(token in override_justification.lower() for token in combined_tokens)

    print("-" * 60)
    if is_valid:
        print("VERDICT: 200 OK (AFFIRMATIVE)")
        print(f"REASONING: Override aligns with anchored HLE/SOC kernels.")
        print("-" * 60)
        sys.exit(0)
    else:
        print("VERDICT: 403 FORBIDDEN (NEGATIVE)")
        print(f"REASONING: Justification lacks axiomatic merit in STEM or Social domains.")
        print("-" * 60)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("USAGE: python miso_arbitrator.py <blocking_reason> <override_justification>")
        sys.exit(2)
    
    arbitrate(sys.argv[1], sys.argv[2])
