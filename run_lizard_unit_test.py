# MISO "Phoenix" Phase 1: Lizard Brain Unit Test
# 1. Get the 'missing type annotation' error from our buggy file.
# 2. Call the DE-SIMULATED LizardBrain directly.
# 3. Check if the brain returns a fix.
# 4. Apply the fix and run mypy again to verify.

import subprocess
import sys
import os
from miso_brains import LizardBrain

TARGET_FILE = "unit_test_bug.py"

def run_command(command):
    """Helper to run shell commands and return output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout + result.stderr

def run_unit_test():
    print("--- PHOENIX PHASE 1: LIZARD BRAIN UNIT TEST ---")
    
    # --- STEP 1: Confirm initial failure ---
    print(f"[TEST]: Running mypy on {TARGET_FILE} (expecting failure)...")
    mypy_error = run_command(f"mypy --disallow-untyped-defs {TARGET_FILE}")
    
    if "missing a type annotation" not in mypy_error:
        print("[TEST]: ERROR! Buggy file is not failing as expected.")
        print(mypy_error)
        sys.exit(1)
        
    print("[TEST]: Confirmed. Mypy failure detected.")
    
    # --- STEP 2: Call the Lizard Brain ---
    try:
        original_code = open(TARGET_FILE, 'r').read()
        lizard = LizardBrain()
    except Exception as e:
        print(f"[TEST]: FAILED to initialize LizardBrain: {e}")
        sys.exit(1)

    print(f"[TEST]: Calling {lizard.name} (Model: {lizard.model}) to fix...")
    fixed_code, cost = lizard.fix(original_code, mypy_error)
    
    # --- STEP 3: Check the Fix ---
    if fixed_code is None:
        print("[TEST]: *** TEST FAILED (Step 3) ***")
        print("[TEST]: Lizard brain returned None (failed to find a fix).")
        sys.exit(1)
        
    print("[TEST]: Lizard brain returned a potential fix. Writing to disk...")
    open(TARGET_FILE, 'w').write(fixed_code)

    # --- STEP 4: Verify the Fix ---
    print(f"[TEST]: Verifying fix... running mypy on {TARGET_FILE} (expecting success)...")
    mypy_fix_result = run_command(f"mypy --disallow-untyped-defs {TARGET_FILE}")
    
    if "Success: no issues found" not in mypy_fix_result:
        print("[TEST]: *** TEST FAILED (Step 4) ***")
        print("[TEST]: Mypy still fails after the Lizard's fix:")
        print(mypy_fix_result)
        sys.exit(1)
    
    print("[TEST]: *** TEST PASSED (Step 4) ***")
    print("[TEST]: Mypy now passes.\n")
    
    # --- FINAL REPORT ---
    print("--- LIZARD BRAIN UNIT TEST: PASSED ---")
    print("SUMMARY:")
    print("  - Real API call to: Ollama (Lizard Brain)")
    print("  - Mypy error: FIXED")
    print("  - Simulated Cost: $0.0010")
    print("--- LIZARD BRAIN (DE-SIMULATED) IS OPERATIONAL ---")

if __name__ == "__main__":
    run_unit_test()
