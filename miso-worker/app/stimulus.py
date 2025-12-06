import os
import redis
import json
import time
import random
import os
from datetime import datetime

# --- CONFIG ---
REDIS_HOST = os.getenv("REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
TASK_COUNT = 20
INCOME_PER_TASK = 5.00

def run_stress_test():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    wallet_key = "miso:sovereign:wallet"
    task_queue = "miso:tasks"
    
    print(f"--- INITIATING CORTICAL STRESS TEST (N={TASK_COUNT}) ---")
    
    # 1. FLOOD PHASE (Sensory Input)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Injecting Stimuli...")
    for i in range(TASK_COUNT):
        task = {
            "id": f"stim_{i}",
            "type": "STRESS_TEST",
            "payload": f"Compute tensor load {random.random()}",
            "timestamp": time.time()
        }
        r.rpush(task_queue, json.dumps(task))
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Injection Complete. Queue Length: {r.llen(task_queue)}")
    print(">>> CHECK DASHBOARD NOW: System should be in 'ALERT' mode (Red).")
    
    # Pause to let the human see the "ALERT" state on the dashboard
    time.sleep(5)
    
    # 2. PROCESSING PHASE (Motor Output)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Simulating Task Execution & Revenue...")
    
    while r.llen(task_queue) > 0:
        # Pop a task (Work)
        task = r.lpop(task_queue)
        
        # Simulate "Cognitive Effort"
        time.sleep(0.2) 
        
        # Credit the Sovereign (Income)
        # We manually update the wallet here since the V42 Worker isn't Sovereign-aware yet.
        wallet_raw = r.get(wallet_key)
        if wallet_raw:
            wallet = json.loads(wallet_raw)
            wallet["balance"] += INCOME_PER_TASK
            wallet["status"] = "SOLVENT"
            r.set(wallet_key, json.dumps(wallet))
            
        # Log progress occasionally
        remaining = r.llen(task_queue)
        if remaining % 5 == 0:
             print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing... Remaining: {remaining} | Balance: {wallet['balance']:.2f}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] All tasks cleared.")
    print(">>> CHECK DASHBOARD: System should return to 'DREAM' mode (Green).")

if __name__ == "__main__":
    run_stress_test()
