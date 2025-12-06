import time
import json
import boto3
import random
from datetime import datetime

# Configure S3
s3 = boto3.client('s3')
BUCKET = "miso-application-forge-ui-oxvkhfa8"
KEY = "status.json"

print(f"Initializing MISO Uplink to {BUCKET}...")

logs = []

def push_state(module, status, metric, new_log=None):
    if new_log:
        timestamp = datetime.now().strftime("%H:%M:%S")
        logs.insert(0, {"time": timestamp, "type": "INFO", "msg": new_log})
        # Keep only last 15 logs
        if len(logs) > 15: logs.pop()

    state = {
        "status": status,
        "module": module,
        "metric": metric,
        "logs": logs
    }
    
    # Upload to S3 with public read permissions
    try:
        s3.put_object(
            Bucket=BUCKET,
            Key=KEY,
            Body=json.dumps(state),
            ContentType='application/json',
            ACL='public-read',
            CacheControl='max-age=0' # Prevent caching
        )
        print(f"Uplink Pulse: {new_log if new_log else '...'}")
    except Exception as e:
        print(f"Transmission Error: {e}")

# Simulation Loop (Replace this with Gladiator hooks later)
count = 0
while True:
    count += 1
    
    if count % 5 == 0:
        push_state("ARCHITECT", "OPTIMIZING", f"Iter: {count}", "Analyzing GAN output weights...")
    elif count % 3 == 0:
        push_state("GLADIATOR", "FIGHTING", f"Score: {random.random():.2f}", "Running syntax validation on generated code.")
    else:
        push_state("SYSTEM", "ONLINE", "Idle", None)
        
    time.sleep(1)
