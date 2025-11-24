import os

print("[BUILDER]: Starting sterile file creation...")

# --- File 1: buggy_module.py ---
# This is the sterile, 100% ASCII content.
buggy_code = """# This file contains a simple mypy error
# MISO should be able to fix this easily.

def add_numbers(a, b):
    # This function is missing type hints
    return a + b

def concatenate_strings(s1, s2):
    # This one is also missing type hints
    return s1 + s2

if __name__ == "__main__":
    print(f"Adding: {add_numbers(10, 5)}")
    print(f"Concatenating: {concatenate_strings('hello', 'world')}")
"""

# --- File 2: run_gauntlet_4.py ---
# This is the sterile, 100% ASCII content with the mypy fix.
gauntlet_code = """# Gauntlet Level 4: The Cost vs. Quality Test
# 1. Run mypy on buggy code, confirm it fails.
# 2. Feed the error to the Triage Agent.
# 3. VERIFY: The Triage Agent chooses the "Lizard" (cheap) brain.
# 4. The Lizard brain applies the fix.
# 5. VERIFY: mypy now passes.
# 6. VERIFY: pytest (TDD) still passes.

import subprocess
import sys
from miso_triage import MisoTriageAgent

TARGET_FILE = "buggy_module.py"
TEST_FILE = "test_buggy_module.py"

def run_command(command):
    \"\"\"Helper to run shell commands and return output.\"\"\"
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    # Return a combined string of stdout and stderr
    return result.stdout + result.stderr

def run_gauntlet():
    print("--- GAUNTLET LEVEL 4: INITIATED ---")
    print("This test will verify MISO's cost-saving triage logic.\\n")
    
    total_cost = 0
    triage_agent = MisoTriageAgent()

    # --- STEP 1: Confirm initial failure ---
    print(f"[GAUNTLET]: Running mypy on {TARGET_FILE} (expecting failure)...")
    # THE FIX IS HERE: Added --check-untyped-defs
    mypy_error = run_command(f"mypy --check-untyped-defs {TARGET_FILE}")
    
    if "Success" in mypy_error:
        print("[GAUNTLET]: ERROR! Code is already clean. Test is invalid.")
        print("[DEBUG]: Mypy output was:")
        print(mypy_error)
        sys.exit(1)
    
    print("[GAUNTLET]: Confirmed. Mypy failure detected.")
    
    # --- STEP 2: MISO Triage Agent Analyzes Error ---
    original_code = open(TARGET_FILE, 'r').read()
    chosen_brain = triage_agent.decide_brain(mypy_error)
    
    # --- STEP 3: VERIFY Brain Choice ---
    if chosen_brain.name != "Lizard (Cheap)":
        print(f"[GAUNTLET]: *** TEST FAILED ***")
        print(f"[GAUNTLET]: Triage Agent chose the '{chosen_brain.name}'!")
        print(f"[GAUNTLET]: It should have chosen the 'Lizard (Cheap)' brain to save cost.")
        sys.exit(1)
        
    print(f"[GAUNTLET]: *** TEST PASSED (Step 3) ***")
    print(f"[GAUNTLET]: Triage Agent correctly chose: {chosen_brain.name}\\n")
    
    # --- STEP 4: Brain Applies Fix ---
    print(f"[GAUNTLET]: {chosen_brain.name} is attempting the fix...")
    fixed_code, cost = chosen_brain.fix(original_code, mypy_error)
    total_cost += cost
    
    if fixed_code is None:
        print("[GAUNTLET]: *** TEST FAILED ***")
        print("[GAUNTLET]: The brain failed to provide a fix.")
        sys.exit(1)

    print("[GAUNTLET]: Fix generated. Writing to disk...")
    open(TARGET_FILE, 'w').write(fixed_code)
    
    # --- STEP 5: VERIFY Mypy Pass ---
    print(f"[GAUNTLET]: Verifying fix... running mypy on {TARGET_FILE} (expecting success)...")
    # THE FIX IS ALSO HERE: Added --check-untyped-defs
    mypy_fix_result = run_command(f"mypy --check-untyped-defs {TARGET_FILE}")
    
    if "Success: no issues found" not in mypy_fix_result:
        print("[GAGAUNTLET]: *** TEST FAILED (Step 5) ***")
        print("[GAUNTLET]: Mypy still fails after the fix:")
        print(mypy_fix_result)
        sys.exit(1)
        
    print("[GAUNTLET]: *** TEST PASSED (Step 5) ***")
    print("[GAUNTLET]: Mypy now passes.\\n")

    # --- STEP 6: VERIFY TDD (Pytest) Pass ---
    print(f"[GAUNTLET]: Verifying logic... running pytest {TEST_FILE} (expecting pass)...")
    pytest_result = run_command(f"pytest {TEST_FILE}")

    if "passed" not in pytest_result:
        print("[GAUNTLET]: *** TEST FAILED (Step 6) ***")
        print("[GAUNTLET]: TDD FAILED! The fix broke the application logic.")
        print(pytest_result)
        sys.exit(1)
        
    print("[GAUNTLET]: *** TEST PASSED (Step 6) ***")
    print("[GAUNTLET]: TDD suite passed. Logic is intact.\\n")
    
    # --- FINAL REPORT ---
    print("--- GAUNTLET LEVEL 4: PASSED ---")
    print("SUMMARY:")
    print("  - Triage Agent CORRECTLY routed to: Lizard (Cheap)")
    print("  - Mypy errors: FIXED")
    print("  - TDD tests: PASSED")
    print(f"  - Total simulated cost: ${total_cost:.4f}")
    print("--- MISO ELASTIC INTELLIGENCE IS OPERATIONAL ---")

if __name__ == "__main__":
    run_gauntlet()
"""

try:
    with open("buggy_module.py", "w") as f:
        f.write(buggy_code)
    print("[BUILDER]: Wrote sterile buggy_module.py")

    with open("run_gauntlet_4.py", "w") as f:
        f.write(gauntlet_code)
    print("[BUILDER]: Wrote sterile run_gauntlet_4.py")
    
    print("[BUILDER]: All files created successfully.")

except Exception as e:
    print(f"[BUILDER]: FAILED to build files: {e}")
    print("This may be an indentation or paste error in the builder script itself.")

