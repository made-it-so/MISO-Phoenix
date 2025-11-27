import redis
import json
import time
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

def inject():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    # Task 1: The Original Experience
    task_a = {
        "id": "mem_test_A",
        "type": "CODING",
        "payload": "Write a Python script to calculate the Fibonacci sequence."
    }
    
    # Task 2: The Recall Trigger (Semantically similar, not identical)
    task_b = {
        "id": "mem_test_B",
        "type": "CODING",
        "payload": "Generate code for Fibonacci numbers."
    }
    
    print(f"Injecting Task A (Experience)...")
    r.rpush("miso:tasks", json.dumps(task_a))
    
    # Wait for A to be processed and consolidated
    print("Waiting 10s for consolidation...")
    time.sleep(10)
    
    print(f"Injecting Task B (Recall)...")
    r.rpush("miso:tasks", json.dumps(task_b))
    print("Done. Check architect.log for 'MEMORY RECALL'.")

if __name__ == "__main__":
    inject()
