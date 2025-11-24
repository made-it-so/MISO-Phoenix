# Gauntlet Level 7: The "Swarm Test" (DE-SIMULATED ASYNC)
# 1. Clean up ALL old gauntlet files.
# 2. Create the 10 buggy/TDD files.
# 3. Run mypy to get the batch error log.
# 4. Call 'asyncio.run()' on the TriageAgent's 'coordinate_fix_swarm' method.
# 5. VERIFY: The async swarm fixes all 10 files in parallel.
# 6. VERIFY: All TDD tests pass.
# 7. Report the final (minimal) cost and *total time*.

import subprocess
import sys
import os
import asyncio  # <-- NEW: Import the asyncio library
import time     # <-- NEW: We will time the swarm
from miso_triage import MisoTriageAgent

NUM_FILES_IN_SWARM = 10
FILE_PREFIX = "g7_buggy"
TEST_PREFIX = "g7_test"

# This is the simple "bug" we will create 10 times.
BUGGY_CODE_TEMPLATE = """
def get_name(name):
    # This function is missing type hints
    return f"Hello, {name}"
"""

# This is the simple test we will create 10 times.
TEST_CODE_TEMPLATE = """
from {buggy_filename} import get_name

def test_get_name():
    assert get_name("MISO") == "Hello, MISO"
"""

def run_command(command):
    """Helper to run shell commands and return output."""
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout + result.stderr

def cleanup_old_files():
    """Cleans up files from all previous gauntlets."""
    print("[RUNNER]: Cleaning up old gauntlet files...")
    files_to_remove = [
        "buggy_module.py", "test_buggy_module.py",
        "stats.py", "test_stats.py",
        "broken_math.py", "test_broken_math.py",
        "unit_test_bug.py" # <-- NEW: Clean up Phase 1 file
    ]
    for f in files_to_remove:
        if os.path.exists(f):
            os.remove(f)
            
    # Also remove any g7 files from a previous run
    for i in range(NUM_FILES_IN_SWARM):
        buggy_file = f"{FILE_PREFIX}_{i}.py"
        test_file = f"{TEST_PREFIX}_{i}.py"
        if os.path.exists(buggy_file):
            os.remove(buggy_file)
        if os.path.exists(test_file):
            os.remove(test_file)

def create_swarm_files():
    """Factory to create all 10 buggy files and 10 test files."""
    print(f"[RUNNER]: Creating {NUM_FILES_IN_SWARM} buggy files and TDD tests...")
    for i in range(NUM_FILES_IN_SWARM):
        buggy_filename = f"{FILE_PREFIX}_{i}"
        buggy_filepath = f"{buggy_filename}.py"
        test_filepath = f"{TEST_PREFIX}_{i}.py"
        
        with open(buggy_filepath, "w") as f:
            f.write(BUGGY_CODE_TEMPLATE)
            
        with open(test_filepath, "w") as f:
            f.write(TEST_CODE_TEMPLATE.format(buggy_filename=buggy_filename))
    print("[RUNNER]: File factory complete.")

def run_gauntlet():
    print("--- GAUNTLET LEVEL 7: 'THE ASYNC SWARM TEST' INITIATED ---")
    print("This test will verify MISO's *parallel* horizontal scaling.\n")
    
    # --- STEP 1: Setup ---
    cleanup_old_files()
    create_swarm_files()
    triage_agent = MisoTriageAgent()

    # --- STEP 2: Initial Mypy Run (Expecting Swarm of Failures) ---
    print(f"\n[GAUNTLET]: Running mypy on all {NUM_FILES_IN_SWARM} files...")
    mypy_error_log = run_command(f"mypy --disallow-untyped-defs {FILE_PREFIX}_*.py")
    
    if "Found" not in mypy_error_log:
        print("[GAUNTLET]: ERROR! Mypy did not find any errors. Test is invalid.")
        sys.exit(1)

    print("[GAUNTLET]: Confirmed. Swarm of mypy failures detected.")

    # --- STEP 3: MISO Triage Coordinator Analyzes Batch ---
    print("\n[GAUNTLET]: Sending entire error log to Async Triage Coordinator...")
    
    # --- NEW: Time the swarm execution ---
    start_time = time.time()
    
    # --- NEW: Use 'asyncio.run()' to call the async coordinator ---
    try:
        total_cost, tasks_fixed = asyncio.run(
            triage_agent.coordinate_fix_swarm(mypy_error_log)
        )
    except Exception as e:
        print(f"[GAUNTLET]: *** TEST FAILED (Async Runner) ***")
        print(f"[GAUNTLET]: The asyncio.run() call failed: {e}")
        sys.exit(1)
        
    end_time = time.time()
    total_time = end_time - start_time
    
    # --- STEP 4: VERIFY Coordinator Success ---
    if tasks_fixed != NUM_FILES_IN_SWARM:
        print(f"[GAUNTLET]: *** TEST FAILED (Step 4) ***")
        print(f"[GAUNTLET]: Coordinator only fixed {tasks_fixed}/{NUM_FILES_IN_SWARM} files.")
        sys.exit(1)

    print(f"\n[GAUNTLET]: *** TEST PASSED (Step 4) ***")
    print(f"[GAUNTLET]: Coordinator successfully fixed all {tasks_fixed} files.")

    # --- STEP 5: VERIFY TDD Pass ---
    print(f"\n[GAUNTLET]: Verifying all fixes... running pytest on all {NUM_FILES_IN_SWARM} TDD files...")
    pytest_fix_result = run_command(f"pytest {TEST_PREFIX}_*.py")
    
    if "failed" in pytest_fix_result or "errors" in pytest_fix_result:
        print("[GAUNTLET]: *** TEST FAILED (Step 5) ***")
        print("[GAUNTLET]: TDD still fails after swarm fix:")
        print(pytest_fix_result)
        sys.exit(1)
        
    print("[GAUNTLET]: *** TEST PASSED (Step 5) ***")
    print(f"[GAUNTLET]: All {NUM_FILES_IN_SWARM} TDD suites passed.\n")

    # --- FINAL REPORT ---
    print("--- GAUNTLET LEVEL 7 (ASYNC): PASSED ---")
    print("SUMMARY (PERFORMANCE):")
    print(f"  - Tasks: {tasks_fixed} simple mypy errors")
    print(f"  - Total Swarm Cost: ${total_cost:.4f}")
    print(f"  - **Total Swarm Time:** {total_time:.2f} seconds")
    print("\n--- MISO ASYNC HORIZONTAL SCALING IS OPERATIONAL ---")

if __name__ == "__main__":
    run_gauntlet()
