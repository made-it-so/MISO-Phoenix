import boto3
import json

QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
sqs = boto3.client('sqs', region_name="us-east-1")

# Get Key
with open("keys.json") as f:
    keys = f.read()
    # Hacky parse because previous output was text not pure json
    import re
    match = re.search(r'miso_sk_[a-f0-9]*', keys)
    if match:
        key = match.group(0)
        print(f"🔑 Using Key: {key}")
        
        payload = {
            "session_id": "FINANCE_FINAL", 
            "api_key": key, 
            "description": "Calculate the 1000th prime number"
        }
        
        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(payload))
        print("🚀 Financial Payload Sent via SDK.")
    else:
        print("❌ Could not find key.")
