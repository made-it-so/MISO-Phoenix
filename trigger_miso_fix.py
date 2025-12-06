import os
import sys
import json
import subprocess
import time
import requests # We need to install this

# --- 1. CONFIGURATION ---
TARGET_FILE = "broken_math.py"
TEST_FILE = "test_broken_math.py"
MISO_URL = "http://127.0.0.1:5000/miso/trigger"
MISO_SECRET = "MISO_IS_AUTONOMOUS_PLEASEWORK_123!"

def run_command(command, check=True):
    """Helper to run shell commands."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check, shell=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[CONDUCTOR]: Command failed: {e.stderr}")
        return False, e.stderr

def main():
    print(f"[CONDUCTOR]: Starting MISO fix for {TARGET_FILE}...")
    
    # --- 1. Reset the file to its buggy state ---
    print(f"[CONDUCTOR]: Resetting {TARGET_FILE} to buggy state...")
    buggy_code = (
        "# This file contains a bug\n"
        "def divide_by(a, b):\n"
        "    return a / b # The bug\n"
        "def get_average(numbers):\n"
        "    if not numbers:\n"
        "        return 0\n"
        "    total_sum = sum(numbers)\n"
        "    return divide_by(total_sum, 0) # The trigger\n"
    )
    with open(TARGET_FILE, 'w') as f:
        f.write(buggy_code)
    
    # --- 2. Run Pytest to get the error log ---
    print("[CONDUCTOR]: Running pytest to capture error log...")
    success, pytest_log = run_command(f"pytest {TEST_FILE}", check=False)
    if not "ZeroDivisionError" in pytest_log:
        print(f"[CONDUCTOR]: ERROR! Pytest did not fail as expected.\n{pytest_log}")
        sys.exit(1)
    
    print("[CONDUCTOR]: Pytest failed as expected. Preparing payload...")
    
    # --- 3. Call the MISO AI Brain (Container) ---
    payload = {
        "target_file": TARGET_FILE,
        "original_code": buggy_code,
        "error_log": pytest_log
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MISO_SECRET}"
    }
    
    print(f"[CONDUCTOR]: Sending job to MISO Server at {MISO_URL}...")
    try:
        response = requests.post(MISO_URL, headers=headers, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses
        result = response.json()
    except Exception as e:
        print(f"[CONDUCTOR]: ERROR! MISO API call failed: {e}")
        sys.exit(1)

    # --- 4. Process the AI's Response ---
    if result.get("status") != "success":
        print(f"[CONDUCTOR]: ERROR! MISO Brain failed: {result.get('message')}")
        sys.exit(1)
        
    fixed_code = result["fixed_code"]
    brain_name = result["brain_used"]
    print(f"[CONDUCTOR]: Received successful fix from {brain_name}.")

    # --- 5. Run the Git commands (on the HOST) ---
    print(f"[CONDUCTOR_GIT]: Writing fix to {TARGET_FILE}...")
    with open(TARGET_FILE, 'w') as f:
        f.write(fixed_code)
        
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    sanitized_name = brain_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
    branch_name = f"miso-fix/{sanitized_name}-{timestamp}"
    commit_message = f"MISO [{brain_name}]: Autonomous fix for {TARGET_FILE}"

    print(f"[CONDUCTOR_GIT]: Creating new branch: {branch_name}")
    run_command(f"git checkout main") # Ensure we are on main
    success, out = run_command(f"git checkout -b {branch_name}")
    if not success:
        print("[CONDUCTOR_GIT]: Git checkout failed. Aborting.")
        sys.exit(1)

    print("[CONDUCTOR_GIT]: Committing and pushing fix...")
    run_command(f"git add {TARGET_FILE}")
    run_command(f"git commit -m \"{commit_message}\"")
    success, out = run_command(f"git push origin {branch_name}")
    
    if not success:
        print("[CONDUCTOR_GIT]: Git push failed. Check auth.")
        sys.exit(1)
        
    run_command("git checkout main")
    
    print("\n--- MISO AUTONOMOUS FIX COMPLETE ---")
    print(f"Successfully pushed branch: {branch_name}")
    
if __name__ == "__main__":
    main()
