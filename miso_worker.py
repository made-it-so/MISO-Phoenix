#
# MISO "WORKER" SCRIPT (EPHEMERAL TIER 2 LIZARD)
# This script is run by the ephemeral Fargate "swarm" tasks.
# Its job: Fix ONE bug and push ONE commit.
#

import sys
import os
import asyncio
import subprocess
import time
from miso_brains import LizardBrain # Only import the brain we need
from dotenv import load_dotenv

# --- 1. Load Secrets (from Fargate Task Definition) ---
load_dotenv() 
try:
    MISO_GITHUB_PAT = os.environ['MISO_GITHUB_PAT']
except KeyError:
    print("[WORKER]: CRITICAL: 'MISO_GITHUB_PAT' not found in environment.")
    sys.exit(1)

# --- 2. Git Helper Functions (Copied from miso_main) ---
def _run_git_command(command: list[str]) -> (bool, str):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd="/app")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[WORKER_GIT_ERROR]: Command '{' '.join(command)}' failed.")
        return False, e.stderr

def _configure_git():
    """Injects the PAT into the git config for this container."""
    print("[WORKER_GIT]: Configuring git credentials for container...")
    repo_url = f"https://{MISO_GITHUB_PAT}@github.com/made-it-so/MISO-Phoenix.git"
    success, out = _run_git_command(["git", "remote", "set-url", "origin", repo_url])
    if not success: return False, out
    _run_git_command(["git", "config", "--global", "user.email", "miso-lizard@autonomous-agent.ai"])
    _run_git_command(["git", "config", "--global", "user.name", "MISO Lizard Worker"])
    return True, "Git configured successfully."

def _commit_and_push_fix(target_file: str, brain_name: str, file_content: str) -> (bool, str):
    print(f"[WORKER_GIT]: Writing fix for {target_file} to disk...")
    try:
        with open(target_file, 'w') as f:
            f.write(file_content)
    except Exception as e:
        return False, f"Failed to write file: {e}"

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    sanitized_name = brain_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
    branch_name = f"miso-fix/{sanitized_name}-{target_file}-{timestamp}"
    commit_message = f"MISO [{brain_name}]: Autonomous fix for {target_file}"

    print("[WORKER_GIT]: Pulling latest 'main' branch...")
    _run_git_command(["git", "checkout", "main"])
    _run_git_command(["git", "pull", "origin", "main"])

    print(f"[WORKER_GIT]: Creating new branch: {branch_name}")
    success, output = _run_git_command(["git", "checkout", "-b", branch_name])
    if not success:
        print(f"[WORKER_GIT]: Failed to create new branch. Retrying pull... {output}")
        _run_git_command(["git", "pull", "origin", "main"])
        success, output = _run_git_command(["git", "checkout", "-b", branch_name])
        if not success:
            return False, f"Failed to create new branch on retry. {output}"

    print(f"[WORKER_GIT]: Committing fix for {target_file}...")
    _run_git_command(["git", "add", target_file])
    _run_git_command(["git", "commit", "-m", commit_message])

    print(f"[WORKER_GIT]: Pushing new branch to origin...")
    success, output = _run_git_command(["git", "push", "origin", branch_name])
    if not success:
        return False, f"Failed to 'git push'. Check PAT scope. {output}"

    _run_git_command(["git", "checkout", "main"])
    return True, f"Successfully pushed to branch: {branch_name}"

# --- 3. The Main Worker Logic ---
def run_fix(target_file: str, error_log: str):
    """
    The main "worker" function.
    """
    print(f"--- MISO WORKER (LIZARD TIER 2) ---")
    print(f"Job: Fix {target_file}")
    print(f"Error: {error_log}")

    # --- 1. Configure Git ---
    success, msg = _configure_git()
    if not success:
        print(f"[WORKER]: CRITICAL: Failed to configure git: {msg}")
        sys.exit(1)

    # --- 2. Read the Buggy Code ---
    try:
        with open(target_file, 'r') as f:
            original_code = f.read()
    except Exception as e:
        print(f"[WORKER]: CRITICAL: Failed to read {target_file}: {e}")
        sys.exit(1)

    # --- 3. Call the Lizard Brain ---
    print("[WORKER]: Initializing LizardBrain...")
    lizard = LizardBrain()
    
    print("[WORKER]: Calling LizardBrain to generate fix...")
    try:
        fixed_code, cost = asyncio.run(
            lizard.fix(original_code, error_log)
        )
    except Exception as e:
        print(f"[WORKER]: CRITICAL: LizardBrain.fix() call failed: {e}")
        sys.exit(1)
        
    if fixed_code is None or "def" not in fixed_code:
        print("[WORKER]: FIX FAILED. Lizard brain returned invalid code.")
        sys.exit(1)

    # --- 4. Commit and Push ---
    print("[WORKER]: Fix generated. Committing to git...")
    success, msg = _commit_and_push_fix(
        target_file, lizard.name, fixed_code
    )
    
    if not success:
        print(f"[WORKER]: CRITICAL: Git push failed: {msg}")
        sys.exit(1)
        
    print(f"[WORKER]: Job complete. {msg}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python miso_worker.py <target_file> <error_message>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    error_message = sys.argv[2]
    run_fix(target_file, error_message)
