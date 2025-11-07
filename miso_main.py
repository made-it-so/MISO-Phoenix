#
# MISO MAIN APPLICATION - "PHOENIX" PHASE 5 (FINAL)
# This is the CONTAINERIZED "AI BRAIN" server.
# Its ONLY job is to receive a bug, run the AI loop,
# and RETURN THE FIXED CODE in its JSON response.
# It no longer handles git operations.
#

import os
import json
import asyncio
from flask import Flask, request, jsonify
from miso_triage import MisoTriageAgent
from dotenv import load_dotenv

print("[MISO_APP]: Initializing Flask server...")
app = Flask(__name__)

load_dotenv()
try:
    MISO_SECRET = os.environ['MISO_WEBHOOK_SECRET']
except KeyError:
    print("[MISO_APP]: CRITICAL: 'MISO_WEBHOOK_SECRET' not found. Auth will fail.")
    MISO_SECRET = None

print("[MISO_APP]: Initializing MisoTriageAgent (Tiers 0-6)...")
try:
    triage_agent = MisoTriageAgent()
    print("[MISO_APP]: Triage Agent is hot. MISO is operational.")
except Exception as e:
    print(f"[MISO_APP]: CRITICAL: Failed to initialize MisoTriageAgent: {e}")
    triage_agent = None

@app.route('/miso/trigger', methods=['POST'])
def handle_miso_trigger():
    print("\n--- [MISO_APP]: New Webhook Trigger Received ---")
    
    # --- 1. SECURITY CHECK ---
    if not MISO_SECRET:
        return jsonify({"status": "error", "message": "MISO server not configured."}), 500
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f"Bearer {MISO_SECRET}":
        print("[MISO_APP]: **AUTH FAILED.** Rejecting request.")
        return jsonify({"status": "error", "message": "Invalid or missing Authorization token."}), 403

    print("[MISO_APP]: **AUTH SUCCESSFUL.** Payload accepted.")
    if not triage_agent:
        return jsonify({"status": "error", "message": "MISO TriageAgent is not initialized."}), 500

    # --- 2. Parse the Request ---
    try:
        data = request.json
        error_log = data['error_log']
        target_file = data['target_file']
        
        # We NO LONGER check if the file exists. The container doesn't
        # need the file, it just needs the *content*.
        original_code = data['original_code']
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid payload: {e}"}), 400

    # --- 3. Run the Triage & Fix Loop ---
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
            print("[MISO_APP]: FIX FAILED. Brain returned None or invalid code.")
            return jsonify({"status": "failure", "message": "AI brain failed to generate a valid fix."}), 200

        # --- 4. Return the Fix (NEW) ---
        print(f"[MISO_APP]: FIX SUCCESS. Returning fixed code in JSON response.")
        return jsonify({
            "status": "success",
            "brain_used": chosen_brain.name,
            "cost": cost,
            "target_file": target_file,
            "fixed_code": fixed_code
        }), 200

    except Exception as e:
        print(f"[MISO_APP]: CRITICAL FAILURE during Triage/Fix loop: {e}")
        return jsonify({"status": "error", "message": f"Internal MISO error: {e}"}), 500

if __name__ == '__main__':
    # NOTE: This container NO LONGER needs git commands to start.
    app.run(host='0.0.0.0', port=5000, debug=False)
