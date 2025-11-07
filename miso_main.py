#
# MISO MAIN APPLICATION - "PHOENIX" (FINAL, AUTONOMOUS, GIT-ENABLED)
# This is the final, persistent, webhook-driven application.
# It listens, authenticates, runs the AI loop, and
# autonomously commits and pushes the fix to Git.
#

import os
import json
import asyncio
import subprocess
import time
from flask import Flask, request, jsonify
from miso_triage import MisoTriageAgent
from dotenv import load_dotenv

print("[MISO_APP]: Initializing Flask server...")
app = Flask(__name__)

# --- 1. Load Secrets ---
load_dotenv()
try:
    MISO_SECRET = os.environ['MISO_WEBHOOK_SECRET']
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    # --- NEW: Get the GitHub PAT ---
    MISO_GITHUB_PAT = os.environ['MISO_GITHUB_PAT']
except KeyError as e:
    print(f"[MISO_APP]: CRITICAL: Missing a secret key in .env or Task Definition! {e}")
    MISO_SECRET = None
    triage_agent = None

# --- 2. NEW: Git Helper Functions ---
def _run_git_command(command: list[str]) -> (bool, str):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(__file__))
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[MISO_GIT_ERROR]: Command '{' '.join(command)}' failed.")
        return False, e.stderr
    except FileNotFoundError:
        return False, "ERROR: 'git' command not found."

def _configure_git():
    """Injects the PAT into the git config for this container."""
    print("[MISO_GIT]: Configuring git credentials for container...")
    # This is the "Aha!" moment. We build the authenticated URL.
    repo_url = f"https://{MISO_GITHUB_PAT}@github.com/made-it-so/MISO-Phoenix.git"
    success, out = _run_git_command(["git", "remote", "set-url", "origin", repo_url])
    if not success:
        return False, out
    
    # Set a user for the commits
    _run_git_command(["git", "config", "--global", "user.email", "miso@autonomous-agent.ai"])
    _run_git_command(["git", "config", "--global", "user.name", "MISO Agent"])
    return True, "Git configured successfully."

def _commit_and_push_fix(target_file: str, brain_name: str, file_content: str) -> (bool, str):
    print(f"[MISO_GIT]: Writing fix for {target_file} to disk...")
    try:
        with open(target_file, 'w') as f:
            f.write(file_content)
    except Exception as e:
        return False, f"Failed to write file: {e}"

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    sanitized_name = brain_name.lower().replace(" ", "-").replace("(", "").replace(")", "")
    branch_name = f"miso-fix/{sanitized_name}-{timestamp}"
    commit_message = f"MISO [{brain_name}]: Autonomous fix for {target_file}"

    # We must pull the latest main to avoid conflicts
    print("[MISO_GIT]: Pulling latest 'main' branch...")
    _run_git_command(["git", "checkout", "main"])
    _run_git_command(["git", "pull", "origin", "main"])

    print(f"[MISO_GIT]: Creating new branch: {branch_name}")
    success, output = _run_git_command(["git", "checkout", "-b", branch_name])
    if not success:
        return False, f"Failed to create new branch. Is the repo clean? {output}"

    print(f"[MISO_GIT]: Committing fix for {target_file}...")
    _run_git_command(["git", "add", target_file])
    _run_git_command(["git", "commit", "-m", commit_message])

    print(f"[MISO_GIT]: Pushing new branch to origin...")
    success, output = _run_git_command(["git", "push", "origin", branch_name])
    if not success:
        return False, f"Failed to 'git push'. Check PAT scope. {output}"

    _run_git_command(["git", "checkout", "main"])
    return True, f"Successfully pushed to branch: {branch_name}"

# --- 3. Instantiate MISO ---
if MISO_SECRET: # Only init if we have secrets
    print("[MISO_APP]: Initializing MisoTriageAgent (Tiers 0-6)...")
    try:
        triage_agent = MisoTriageAgent()
        print("[MISO_APP]: Triage Agent is hot. MISO is operational.")
    except Exception as e:
        print(f"[MISO_APP]: CRITICAL: Failed to initialize MisoTriageAgent: {e}")
        triage_agent = None

# --- 4. Define the Webhook Endpoint (Final Version) ---
@app.route('/miso/trigger', methods=['POST'])
def handle_miso_trigger():
    print("\n--- [MISO_APP]: New Webhook Trigger Received ---")
    
    if not MISO_SECRET or not triage_agent:
        return jsonify({"status": "error", "message": "MISO server is not configured."}), 500
        
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {MISO_SECRET}":
        print("[MISO_APP]: **AUTH FAILED.** Rejecting request.")
        return jsonify({"status": "error", "message": "Invalid or missing Authorization token."}), 403

    print("[MISO_APP]: **AUTH SUCCESSFUL.** Payload accepted.")

    # --- 5. Parse the Request ---
    try:
        data = request.json
        error_log = data['error_log']
        target_file = data['target_file']
        
        # We now *must* read the file from disk. We are stateful.
        with open(target_file, 'r') as f:
            original_code = f.read()
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid payload: {e}"}), 400

    # --- 6. Run the Triage & Fix Loop ---
    try:
        chosen_brain = triage_agent.decide_brain(error_log)
        
        if not chosen_brain:
            return jsonify({"status": "error", "message": "Triage Agent returned no brain."}), 500

        print(f"[MISO_APP]: Handing job to {chosen_brain.name}...")
        if asyncio.iscoroutinefunction(chosen_brain.fix):
            fixed_code, cost = asyncio.run(chosen_brain.fix(original_code, error_log))
        else:
            fixed_code, cost = chosen_brain.fix(original_code, error_log)

        if fixed_code is None or "def" not in fixed_code:
            return jsonify({"status": "failure", "message": "AI brain failed to generate a valid fix."}), 200

        # --- 7. Commit and Push the Fix (This is now our job) ---
        commit_success, git_output = _commit_and_push_fix(
            target_file, chosen_brain.name, fixed_code
        )
        
        if not commit_success:
            return jsonify({"status": "error", "message": f"Git integration failed: {git_output}"}), 500

        # --- 8. Return Final Success ---
        return jsonify({
            "status": "success",
            "brain_used": chosen_brain.name,
            "cost": cost,
            "git_result": git_output
        }), 200

    except Exception as e:
        print(f"[MISO_APP]: CRITICAL FAILURE during Triage/Fix loop: {e}")
        return jsonify({"status": "error", "message": f"Internal MISO error: {e}"}), 500

# --- 9. Run the Server ---
if __name__ == '__main__':
    # --- NEW: We must configure git *before* starting the server ---
    success, msg = _configure_git()
    if not success:
        print(f"[MISO_APP]: CRITICAL: Failed to configure git: {msg}")
        sys.exit(1)
        
    app.run(host='0.0.0.0', port=5000, debug=False)
