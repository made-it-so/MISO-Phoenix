import os
import redis
import json
import time
import os

REDIS_HOST = os.getenv("REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# The "Sensory Input"
task_payload = {
    "id": f"task_audit_{int(time.time())}",
    "type": "COMPLEX_CODING",
    "payload": """
    Write a Python script named 'audit_survival.py' that does the following:
    1. Scans the current directory (.).
    2. Counts how many lines of code are in all .py files.
    3. Calculates the 'Survival Score' (Total Lines * 0.01).
    4. Saves a report to 'survival_report.txt' with a sovereign tone.
    
    Output ONLY the Python code for this script. Do not explain.
    """
}

def inject():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.rpush("miso:tasks", json.dumps(task_payload))
    print(f"Injecting Stimulus: {task_payload['id']}")

if __name__ == "__main__":
    inject()
