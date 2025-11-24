# Gauntlet Level 5: The "Einstein" Test (DE-SIMULATED)
# 1. Run pytest, confirm it fails with an ImportError/AttributeError.
# 2. Feed the error to the Triage Agent.
# 3. VERIFY: The Triage Agent routes DIRECTLY to "Einstein (Tier 6)".
# 4. The Einstein brain (DE-SIMULATED) generates the new 'calculate_median' function.
# 5. VERIFY: pytest test_stats.py now passes.

import subprocess
import sys
import os
from miso_triage import MisoTriageAgent

# The file Einstein will write to
TARGET_FILE = "stats.py" 
# The TDD test file that defines the new feature
TEST_FILE = "test_stats.py"

def run_command(command):
    """Helper to run shell commands and return output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout + result.stderr

def run_gauntlet():
    print("--- GAUNTLET LEVEL 5: 'THE EINSTEIN TEST' (DE-SIMULATED) ---")
    print("This test will verify MISO's Tier-6 feature generation.\n")
    
    total_cost = 0
    
    # Prerequisite check
    if not os.path.exists("miso_project/personas/einstein_persona.json"):
        print("[GAUNTLET]: ERROR! 'einstein_persona.json' is missing!")
        sys.exit(1)
        
    try:
        triage_agent = MisoTriageAgent()
    except Exception as e:
        print(f"CRITICAL: Failed to initialize MisoTriageAgent. Did you set your GOOGLE_API_KEY in .env?")
        print(f"Error: {e}")
        sys.exit(1)

    # --- STEP 1: Confirm initial TDD failure ---
    print(f"[GAUNTLET]: Running pytest {TEST_FILE} (expecting ImportError/AttributeError)...")
    pytest_error = run_command(f"pytest {TEST_FILE}")
    
    if "failed" not in pytest_error and "error" not in pytest_error:
        print("[GAUNTLET]: ERROR! TDD is already passing. Test is invalid.")
        sys.exit(1)
    
    if "ImportError" not in pytest_error and "AttributeError" not in pytest_error:
        print("[GAUNTLET]: ERROR! Test is failing with an unexpected error.")
        print(pytest_error)
        sys.exit(1)

    print("[GAUNTLET]: Confirmed. TDD failure detected (New Feature Request).")
    original_code = open(TARGET_FILE, 'r').read()
    
    # --- STEP 2: MISO Triage Agent Analyzes Error ---
    chosen_brain = triage_agent.decide_brain(pytest_error)
    
    # --- STEP 3: VERIFY Brain Choice ---
    if not chosen_brain or chosen_brain.name != "Einstein (Tier 6)":
        brain_name = chosen_brain.name if chosen_brain else "None"
        print(f"[GAUNTLET]: *** TEST FAILED (Step 3) ***")
        print(f"[GAUNTLET]: Triage Agent chose the '{brain_name}'!")
        print(f"[GAUNTLET]: It should have chosen 'Einstein (Tier 6)' for a new feature.")
        sys.exit(1)
        
    print(f"[GAUNTLET]: *** TEST PASSED (Step 3) ***")
    print(f"[GAUNTLET]: Triage Agent correctly chose: {chosen_brain.name}\n")
    
    # --- STEP 4: Einstein Brain Generates Feature ---
    print(f"[GAUNTLET]: {chosen_brain.name} (DE-SIMULATED) is attempting new feature generation...")
    # Einstein 'fix' method is NOT async, it's blocking
    fixed_code, cost = chosen_brain.fix(original_code, pytest_error)
    total_cost += cost
    
    if fixed_code is None or "def" not in fixed_code:
        print("[GAGAUNTLET]: *** TEST FAILED (Einstein Failed) ***")
        print("[GAUNTLET]: The DE-SIMULATED Einstein brain failed to provide a valid fix.")
        print(f"[GAUNTLET]: AI RESPONSE: {fixed_code}")
        sys.exit(1)

    print(f"[GAUNTLET]: New feature code generated. Writing to {TARGET_FILE}...")
    open(TARGET_FILE, 'w').write(fixed_code)
    
    # --- STEP 5: VERIFY TDD Pass ---
    print(f"\n[GAUNTLET]: Verifying feature... running pytest {TEST_FILE} (expecting pass)...")
    pytest_fix_result = run_command(f"pytest {TEST_FILE}")
    
    if "passed" not in pytest_fix_result:
        print("[GAUNTLET]: *** TEST FAILED (Step 5) ***")
        print("[GAUNTLET]: TDD still fails after Einstein's fix:")
        print(pytest_fix_result)
        sys.exit(1)
        
    print("[GAUNTLET]: *** TEST PASSED (Step 5) ***")
    print(f"[GAUNTLET]: TDD suite for {TEST_FILE} now passes.\n")

    # --- FINAL REPORT ---
    print("--- GAUNTLET LEVEL 5 (DE-SIMULATED): PASSED ---")
    print("SUMMARY:")
    print("  - Triage Agent CORRECTLY identified a New Feature Request.")
    print("  - Triage Agent CORRECTLY escalated to: Einstein (Tier 6)")
    print("  - Einstein Brain (Gemini) CORRECTLY: GENERATED")
    print("  - TDD tests: PASSED")
    print(f"  - Total simulated cost: ${total_cost:.4f} (High-cost operation)")
    print("--- MISO DE-SIMULATED TIER-6 LOGIC IS OPERATIONAL ---")

if __name__ == "__main__":
    run_gauntlet()
