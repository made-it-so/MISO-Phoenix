import os
import logging
from flask import Flask, request, jsonify

# --- REQUIRED IMPORTS (Fixes ModuleNotFoundError) ---
# These must match requirements.txt
import boto3
import google.generativeai
import ollama
import git

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [MISO_APP]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Get the secret from environment variables (provided by Fargate Task Def)
EXPECTED_SECRET = os.environ.get('MISO_WEBHOOK_SECRET')

if not EXPECTED_SECRET:
    logging.critical("CRITICAL_FAILURE: MISO_WEBHOOK_SECRET env var not set. Auth will fail.")

app = Flask(__name__)

# --- ALB HEALTH CHECK ---
# This endpoint is CRITICAL. The ALB pings this.
# If it fails, the task is marked Unhealthy (503 error).
@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint for the ALB."""
    # This proves the Flask app is running.
    return jsonify({"status": "healthy"}), 200

# --- AUTHENTICATION CHECK (Helper Function) ---
def check_auth():
    """Checks the 'Authorization' header for the MISO secret."""
    auth_header = request.headers.get('Authorization')
    
    if not EXPECTED_SECRET:
        logging.error("Auth check failed: Server secret is not configured.")
        return False

    if not auth_header or auth_header != f'Bearer {EXPECTED_SECRET}':
        logging.warning("AUTH FAILED. Invalid or missing token.")
        return False
        
    logging.info("**AUTH SUCCESSFUL.**")
    return True

# --- MISO CI ENDPOINT ---
@app.route('/miso/trigger', methods=['POST'])
def handle_ci_webhook():
    """Receives the main trigger from the GHA pytest failure."""
    logging.info("Endpoint /miso/trigger HIT.")
    
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # data = request.json
        logging.info(f"Received payload: {request.data[:200]}...") # Log snippet

        # --- TODO: PASTE YOUR TRIAGE / AI / GIT LOGIC HERE ---
        # 1. Parse the pytest failure from 'data'.
        # 2. Call Gemini (HumanBrain) API.
        # 3. Call git.Repo() to clone, commit, and push the fix.
        #    (Ensure your Fargate Task Role 'ecsTaskRole' has CodeCommit/GitHub permissions)
        # --- END OF LOGIC ---

        # IMPORTANT: You must return 200 OK *fast* or the GHA will time out.
        # If your AI/Git logic takes > 2 minutes, run it in a background thread.
        
        logging.info("/miso/trigger execution complete.")
        return jsonify({"status": "received", "action": "fix_in_progress"}), 200

    except Exception as e:
        logging.error(f"FATAL ERROR in /miso/trigger: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

# --- MISO SWARM ENDPOINT ---
@app.route('/miso/swarm_trigger', methods=['POST'])
def handle_swarm_webhook():
    """Receives the trigger from the swarm test workflow."""
    logging.info("Endpoint /miso/swarm_trigger HIT.")
    
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # --- TODO: PASTE YOUR SWARM LOGIC HERE ---
        # 1. Parse payload.
        # 2. Execute swarm/agent logic.
        # --- END OF LOGIC ---

        logging.info("/miso/swarm_trigger execution complete.")
        return jsonify({"status": "received", "action": "swarm_task_initiated"}), 200

    except Exception as e:
        logging.error(f"FATAL ERROR in /miso/swarm_trigger: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
