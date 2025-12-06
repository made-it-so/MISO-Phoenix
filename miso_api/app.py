import os
import logging
import json
import boto3
from flask import Flask, request, jsonify

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [MISO_API_V2]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Environment Variables ---
EXPECTED_SECRET_ARN = os.environ.get('MISO_WEBHOOK_SECRET_ARN')
SQS_QUEUE_URL = os.environ.get('MISO_SQS_QUEUE_URL')

if not EXPECTED_SECRET_ARN:
    logging.critical("MISO_WEBHOOK_SECRET_ARN env var not set.")
if not SQS_QUEUE_URL:
    logging.critical("MISO_SQS_QUEUE_URL env var not set.")

# --- Clients ---
app = Flask(__name__)
sqs_client = boto3.client('sqs')
secrets_client = boto3.client('secretsmanager')

# --- Load Secret ---
try:
    logging.info(f"Loading webhook secret from ARN: {EXPECTED_SECRET_ARN}...")
    secret_val = secrets_client.get_secret_value(SecretId=EXPECTED_SECRET_ARN)
    EXPECTED_SECRET = secret_val['SecretString']
    logging.info("Webhook secret loaded successfully.")
except Exception as e:
    logging.critical(f"Failed to load webhook secret: {e}", exc_info=True)
    EXPECTED_SECRET = None

# --- Auth ---
def check_auth():
    if not EXPECTED_SECRET:
        logging.error("Auth check failed: Secret not loaded on startup.")
        return False
        
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f'Bearer {EXPECTED_SECRET}':
        logging.warning("AUTH FAILED. Invalid or missing token.")
        return False
    logging.info("Auth successful.")
    return True

# --- Routes ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/miso/task/ingress', methods=['POST'])
def handle_task_ingress():
    logging.info("Endpoint /miso/task/ingress HIT.")
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload_data = request.data.decode('utf-8')
        payload = json.loads(payload_data)
        
        # Validate the generic task format
        task_type = payload.get("task_type")
        task_payload = payload.get("payload")
        
        if not task_type or not task_payload:
            logging.error("Payload missing 'task_type' or 'payload'.")
            return jsonify({"error": "Invalid task format"}), 400

        logging.info(f"Enqueuing task of type: {task_type}...")
        
        sqs_client.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=payload_data
        )
        
        logging.info(f"Task {task_type} enqueued successfully.")
        return jsonify({"status": "received", "action": "task_enqueued"}), 202

    except Exception as e:
        logging.error(f"FATAL ERROR in /miso/task/ingress: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
