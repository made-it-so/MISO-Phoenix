#
# MISO MAIN APPLICATION - "PHOENIX" PHASE 7 (ELASTIC INFRASTRUCTURE)
# This is the final, production-ready "Master Coordinator" server.
# It has TWO webhook endpoints:
# 1. /miso/trigger: For single, complex bugs (Tier 5/6)
# 2. /miso/swarm_trigger: For parallel swarms (Tier 2)
#

import os
import json
import asyncio
import subprocess
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# We import the brains AND the swarm launcher
from miso_triage import MisoTriageAgent
from miso_brains import LizardBrain, HumanBrain, EinsteinBrain

print("[MISO_APP]: Initializing Flask server...")
app = Flask(__name__)

# --- 1. Load Secrets ---
load_dotenv()
try:
    MISO_SECRET = os.environ['MISO_WEBHOOK_SECRET']
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    MISO_GITHUB_PAT = os.environ['MISO_GITHUB_PAT']
except KeyError as e:
    print(f"[MISO_APP]: CRITICAL: Missing a secret key! {e}")
    MISO_SECRET = None
    triage_agent = None

# --- 2. Instantiate ALL MISO Components ---
if MISO_SECRET:
    print("[MISO_APP]: Initializing MisoTriageAgent (Swarm Launcher)...")
    try:
        # This is now *just* the swarm launcher
        swarm_launcher = MisoTriageAgent()
        
        # We also need the specialist brains for single tasks
        human_brain = HumanBrain()
        einstein_brain = EinsteinBrain()
        # We don't need Lizard, as it only runs in the swarm
        
        print("[MISO_APP]: All brains are hot. MISO is operational.")
    except Exception as e:
        print(f"[MISO_APP]: CRITICAL: Failed to initialize brains: {e}")
        swarm_launcher = None
        human_brain = None
        einstein_brain = None

# --- 3. Git Helper Functions (Unchanged) ---
def _run_git_command(command: list[str]) -> (bool, str):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd="/app")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"[MISO_GIT_ERROR]: Command '{' '.join(command)}' failed: {e.stderr}")
        return False, e.stderr

def _configure_git():
    print("[MISO_GIT]: Configuring git credentials for container...")
    repo_url = f"https://{MISO_GITHUB_PAT}@github.com/made-it-so/MISO-Phoenix.git"
    success, out = _run_git_command(["git", "remote", "set-url", "origin", repo_url])
    if not success: return False, out
    _run_git_command(["git", "config", "--global", "user.email", "miso@autonomous-agent.ai"])
    _run_git_command(["git", "config", "--global", "user.name", "MISO Agent"])
    return True, "Git configured successfully."

def _commit_and_push_fix(target_file: str, brain_name: str, file_content: str) -> (bool, str):
    # This function is now only used by the "Human" and "Einstein" brains
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

    print("[MISO_GIT]: Pulling latest 'main' branch...")
    _run_git_command(["git", "checkout", "main"])
    _run_git_command(["git", "pull", "origin", "main"])

    print(f"[MISO_GIT]: Creating new branch: {branch_name}")
    success, output = _run_git_command(["git", "checkout", "-b", branch_name])
    if not success: return False, f"Failed to create new branch: {output}"

    print(f"[MISO_GIT]: Committing fix for {target_file}...")
    _run_git_command(["git", "add", target_file])
    _run_git_command(["git", "commit", "-m", commit_message])

    print(f"[MISO_GIT]: Pushing new branch to origin...")
    success, output = _run_git_command(["git", "push", "origin", branch_name])
    if not success: return False, f"Failed to 'git push': {output}"

    _run_git_command(["git", "checkout", "main"])
    return True, f"Successfully pushed to branch: {branch_name}"

# --- 4. Authentication Check (Helper) ---
def _check_auth():
    if not MISO_SECRET:
        return False, (jsonify({"status": "error", "message": "MISO server not configured."}), 500)
    auth_header = request.headers.get('Authorization')
    if auth_header != f"Bearer {MISO_SECRET}":
        print("[MISO_APP]: **AUTH FAILED.** Rejecting request.")
        return False, (jsonify({"status": "error", "message": "Invalid or missing Authorization token."}), 403)
    print("[MISO_APP]: **AUTH SUCCESSFUL.** Payload accepted.")
    return True, None

# --- 5. ENDPOINT 1: Single-Task Trigger (Human/Einstein) ---
@app.route('/miso/trigger', methods=['POST'])
def handle_miso_trigger():
    print("\n--- [MISO_APP]: New SINGLE-TASK Webhook Received ---")
    
    is_authed, error_response = _check_auth()
    if not is_authed: return error_response
    
    if not human_brain or not einstein_brain:
        return jsonify({"status": "error", "message": "MISO specialist brains not initialized."}), 500

    try:
        data = request.json
        error_log = data['error_log']
        target_file = data['target_file']
        with open(target_file, 'r') as f:
            original_code = f.read()
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid payload: {e}"}), 400

    # --- THIS IS THE "FAST" IF/ELIF ROUTER ---
    print(f"[MISO_APP]: Routing job (fast, direct-route)...")
    chosen_brain = None
    if "ImportError" in error_log or "AttributeError" in error_log:
        print("[MISO_APP]: Detected New Feature Request. Routing to EINSTEIN.")
        chosen_brain = einstein_brain
    else:
        print("[MISO_APP]: Detected complex runtime bug. Routing directly to HUMAN.")
        chosen_brain = human_brain
    
    # --- Run the Fix Loop ---
    try:
        print(f"[MISO_APP]: Handing job to {chosen_brain.name}...")
        fixed_code, cost = chosen_brain.fix(original_code, error_log)

        if fixed_code is None or "def" not in fixed_code:
            return jsonify({"status": "failure", "message": "AI brain failed to generate a valid fix."}), 200

        commit_success, git_output = _commit_and_push_fix(
            target_file, chosen_brain.name, fixed_code
        )
        if not commit_success:
            return jsonify({"status": "error", "message": f"Git integration failed: {git_output}"}), 500

        return jsonify({"status": "success", "brain_used": chosen_brain.name, "git_result": git_output}), 200

    except Exception as e:
        print(f"[MISO_APP]: CRITICAL FAILURE during Triage/Fix loop: {e}")
        return jsonify({"status": "error", "message": f"Internal MISO error: {e}"}), 500

# --- 6. ENDPOINT 2: Swarm-Task Trigger (Lizard) ---
@app.route('/miso/swarm_trigger', methods=['POST'])
def handle_swarm_trigger():
    print("\n--- [MISO_APP]: New SWARM Webhook Received ---")
    
    is_authed, error_response = _check_auth()
    if not is_authed: return error_response
    
    if not swarm_launcher:
        return jsonify({"status": "error", "message": "MISO swarm launcher not initialized."}), 500

    try:
        data = request.json
        error_log = data['error_log']
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid payload: {e}"}), 400

    # --- THIS IS THE "ELASTIC INFRASTRUCTURE" CALL ---
    print(f"[MISO_APP]: Calling Swarm Launcher (Fargate-on-Fargate)...")
    try:
        tasks_launched = swarm_launcher.launch_fix_swarm(error_log)
        
        return jsonify({
            "status": "success",
            "message": f"MISO Swarm launched. {tasks_launched} Fargate workers dispatched."
        }), 200
        
    except Exception as e:
        print(f"[MISO_APP]: CRITICAL FAILURE during Swarm Launch: {e}")
        return jsonify({"status": "error", "message": f"Internal MISO error: {e}"}), 500

# --- 7. Run the Server ---
if __name__ == '__main__':
    success, msg = _configure_git()
    if not success:
        print(f"[MISO_APP]: CRITICAL: Failed to configure git: {msg}")
        sys.exit(1)
        
    app.run(host='0.0.0.0', port=5000, debug=False)
