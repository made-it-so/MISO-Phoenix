import os
import logging
from flask import Flask, request, jsonify

# --- Configuration & Logging ---

# Set up logging to output to stdout (which Fargate/CloudWatch will capture)
# This format makes logs easy to read.
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [MISO_APP]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# Get the secret from environment variables.
# Your Fargate Task Definition MUST provide this.
EXPECTED_SECRET = os.environ.get('MISO_WEBHOOK_SECRET')

if not EXPECTED_SECRET:
    logging.critical("CRITICAL_FAILURE: MISO_WEBHOOK_SECRET env var not set. Auth will fail.")

app = Flask(__name__)

# --- Health Check Route ---

@app.route('/health', methods=['GET'])
def health_check():
    """A simple health check endpoint for Fargate/AWS to ping."""
    return jsonify({"status": "healthy"}), 200

# --- Bare-Bones Webhook Route ---

@app.route('/miso/trigger', methods=['POST'])
def handle_webhook():
    """
    STEP 1: "Hello, World!" Test.
    - Checks auth.
    - Logs success.
    - Immediately returns 200 OK.
    """
    logging.info("Webhook /miso/trigger endpoint hit.")

    # 1. Authorization Check
    auth_header = request.headers.get('Authorization')
    
    # Check for the secret's existence and value
    if not EXPECTED_SECRET:
        logging.error("Auth check failed: Server secret is not configured.")
        return jsonify({"error": "Server configuration error"}), 500

    if not auth_header or auth_header != f'Bearer {EXPECTED_SECRET}':
        logging.warning("AUTH FAILED. Invalid or missing token.")
        return jsonify({"error": "Unauthorized"}), 401

    # 2. Log Success (as requested)
    logging.info("**AUTH SUCCESSFUL.**")

    # 3. Immediately Return "Hello World"
    # This response is sent *before* any other processing.
    return jsonify({"status": "success, hello world"}), 200

# --- Production Server Runner ---

# The 'if __name__ == "__main__":' block is NOT used by a production
# WSGI server like Gunicorn. Fargate will use the CMD in your Dockerfile.
# We leave it out to avoid confusion.
