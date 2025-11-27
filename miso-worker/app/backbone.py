import os
import time
import json
import redis
import random
from datetime import datetime

# --- INDUSTRIAL CONFIG ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# METABOLIC RATES
PULSE_FAST = 2.0   # Active State (High Performance)
PULSE_SLOW = 60.0  # Torpor State (Cost Saving)
IDLE_TIMEOUT = 300 # Seconds before entering Torpor

class DigitalBackbone:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.state_key = "miso:backbone:state"
        self.log_key = "miso:backbone:logs"
        self.task_queue = "miso:tasks"
        self.last_activity = time.time()

    def get_intrinsic_mode(self):
        try:
            queue_len = self.r.llen(self.task_queue)
            if queue_len > 0:
                self.last_activity = time.time()
                return "ALERT", queue_len, PULSE_FAST
            
            # Check if we should hibernate
            time_since_active = time.time() - self.last_activity
            if time_since_active > IDLE_TIMEOUT:
                return "TORPOR", 0, PULSE_SLOW
            
            return "DREAM", 0, PULSE_FAST
        except:
            return "DISCONNECTED", 0, PULSE_SLOW

    def pulse(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] BACKBONE V46 (INDUSTRIAL) ONLINE")
        
        while True:
            try:
                mode, load, tick_rate = self.get_intrinsic_mode()
                
                # Update State Manifold
                current_state = {
                    "timestamp": datetime.now().isoformat(),
                    "unixtime": time.time(),
                    "mode": mode,
                    "load": load,
                    "metabolism": "HIGH" if tick_rate == PULSE_FAST else "LOW"
                }
                self.r.set(self.state_key, json.dumps(current_state))
                
                # Efficient Logging (Only log changes or interactions)
                if mode == "ALERT":
                    print(f"[{datetime.now().strftime('%H:%M:%S')}][ALERT] Processing {load} tasks...")
                elif mode == "TORPOR" and random.random() > 0.9:
                    # Heartbeat rarely in Torpor
                    print(f"[{datetime.now().strftime('%H:%M:%S')}][TORPOR] Saving energy...")

                time.sleep(tick_rate)

            except Exception as e:
                print(f"BACKBONE ERROR: {e}")
                time.sleep(10)

if __name__ == "__main__":
    DigitalBackbone().pulse()
