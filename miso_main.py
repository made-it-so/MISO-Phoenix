#
# MISO MAIN APPLICATION - "PHOENIX" PHASE 4b (FINAL - SECURED)
# This is the final, autonomous, and SECURE application.
# It checks for a secret 'Authorization' header before running.
#

import os
import json
import asyncio
import subprocess
import time
from flask import Flask, request, jsonify
from miso_triage import MisoTriageAgent
from dotenv import load_dotenv

# --- 1. Initialize the Application ---
print("[MISO_APP]: Initializing Flask server...")
app = Flask(__name__)

# --- 2. Load Secrets ---
load_dotenv()
try:
    # Load the new Webhook Secret
    MISO_SECRET = os.environ['MISO_WEBHOOK_SECRET']
    if len(MISO_SECRET) < 16:
        print("[MISO_APP]: WARNING! MISO_WEBHOOK_SECRET is weak. Please set a strong password in .env")
except KeyError:
    print("[MISO_APP]: CRITICAL: 'MISO_WEBHOOK_SECRET' not found in .env file. Server will not be secure.")
    MISO_SECRET = None # This will fail all auth checks

# --- 3. Instantiate MISO ---
print("[MISO_APP]: Initializing MisoTriageAgent (Tiers 0-6)...")
try:
    triage_agent = MisoTriageAgent()
    print("[MISO_APP]: Triage Agent is hot. MISO is operational.")
except Exception as e:
    print(f"[MISO_APP]: CRITICAL: Failed to initialize MisoTriageAgent: {e}")
    triage_agent = None

# --- 4. Git Helper Functions (Unchanged) ---
def _run_git_command(command: list[str]) -> (bool, str):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=os.path.dirname(__file__))
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[MISO_GIT_ERROR]: Command '{' '.join(command)}' failed.")
        return False, e.stderr
    except FileNotFoundError:
        return False, "ERROR: 'git' command not found."

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

    print(f"[MISO_GIT]: Creating new branch: {branch_name}")
    success, output = _run_git_command(["git", "checkout", "-b", branch_name])
    if not success:
        return False, f"Failed to create new branch. Is the repo clean? {output}"

    print(f"[MISO_GIT]: Committing fix for {target_file}...")
    success, output = _run_git_command(["git", "add", target_file])
    if not success:
        return False, f"Failed to 'git add' file: {output}"
        
    success, output = _run_git_command(["git", "commit", "-m", commit_message])
    if not success:
        return False, f"Failed to 'git commit': {output}"

    print(f"[MISO_GIT]: Pushing new branch to origin...")
    success, output = _run_git_command(["git", "push", "origin", branch_name])
    if not success:
        return False, f"Failed to 'git push'. Check server's SSH keys/permissions. {output}"

    _run_git_command(["git", "checkout", "main"])
    
    print(f"[MISO_GIT]: Successfully pushed branch {branch_name} to origin.")
    return True, f"Successfully pushed to branch: {branch_name}"

# --- 5. Define the Webhook Endpoint (NOW SECURED) ---
@app.route('/miso/trigger', methods=['POST'])
def handle_miso_trigger():
    print("\n--- [MISO_APP]: New Webhook Trigger Received ---")
    
    # --- NEW: SECURITY CHECK ---
    if not MISO_SECRET:
        return jsonify({"status": "error", "message": "MISO server is not configured with a WEBHOOK_SECRET."}), 500
        
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {MISO_SECRET}":
        print("[MISO_APP]: **AUTH FAILED.** Rejecting request with invalid or missing token.")
        return jsonify({"status": "error", "message": "Invalid or missing Authorization token."}), 403

    print("[MISO_APP]: **AUTH SUCCESSFUL.** Payload accepted.")
    
    if not triage_agent:
        return jsonify({"status": "error", "message": "MISO TriageAgent is not initialized."}), 500

    # --- 6. Parse the Request ---
    try:
        data = request.json
        error_log = data['error_log']
        target_file = data['target_file']
        
        if not os.path.exists(target_file):
            return jsonify({"status": "error", "message": f"Target file not found: {target_file}"}), 404
            
        print(f"[MISO_APP]: Received job for file: {target_file}")
        with open(target_file, 'r') as f:
            original_code = f.read()
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid payload: {e}"}), 400

    # --- 7. Run the Triage & Fix Loop (Unchanged) ---
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

        # --- 8. Commit and Push the Fix ---
        commit_success, git_output = _commit_and_push_fix(
            target_file, chosen_brain.name, fixed_code
        )
        
        if not commit_success:
            return jsonify({"status": "error", "message": f"Git integration failed: {git_output}"}), 500

        # --- 9. Return Final Success ---
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
    print("[MISO_APP]: Ensuring git is in a clean state...")
    _run_git_command(["git", "checkout", "main"]) 
    _run_git_command(["git", "pull"]) 
    
    app.run(host='0.0.0.0', port=5000, debug=False)
