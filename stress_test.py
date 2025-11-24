import boto3
import json
import random
import time
import uuid

# Configuration
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
sqs = boto3.client('sqs', region_name="us-east-1")

VENDORS = ["GCP", "AZURE"]
VECTORS = ["VEC_A", "VEC_B", "VEC_C", "VEC_D", "VEC_E"] # Limited set to force CACHE HITS

def generate_traffic(count=50):
    print(f"🚀 INJECTING {count} MARKET ORDERS...")
    
    for i in range(count):
        session_id = f"HFT_ORDER_{uuid.uuid4().hex[:8]}"
        target = random.choice(VENDORS)
        vector = random.choice(VECTORS)
        
        payload = {
            "session_id": session_id,
            "cloud_target": target,
            "feature_hash": vector
        }
        
        sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=json.dumps(payload)
        )
        print(f"   -> Sent {session_id} [{target}]")
        time.sleep(0.1) # 100ms delay (High Frequency)

if __name__ == "__main__":
    generate_traffic(50)
    print("✅ BATCH COMPLETE.")
