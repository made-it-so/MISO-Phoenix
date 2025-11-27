import boto3
import json
import os

# CONFIG
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
TENANT_FILE = "app/tenants.json"

def inject():
    # 1. Get the Key
    if not os.path.exists(TENANT_FILE):
        print(f"❌ Error: {TENANT_FILE} not found. Cannot find API Key.")
        return

    with open(TENANT_FILE) as f:
        tenants = json.load(f)
        # Get the last key generated
        api_key = list(tenants.keys())[-1]
        client_name = tenants[api_key]['name']

    print(f"🔑 Using Key for: {client_name} ({api_key})")

    # 2. Construct Payload
    payload = {
        "session_id": "PYTHON_INJECT_1",
        "api_key": api_key,
        "description": "Calculate the 100th Fibonacci number, then write a poem about it."
    }

    # 3. Send via Boto3 (Bypasses broken CLI)
    sqs = boto3.client('sqs', region_name="us-east-1")
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(payload)
    )
    print("🚀 Payload sent successfully to SQS.")

if __name__ == "__main__":
    inject()
