import redis
import json
import time
import random
import os

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
QUEUE = "miso:tasks"

tasks = [
    # TYPE 1: Crystal (Free/Instant) - We use your new tool!
    {"type": "CRYSTAL", "payload": "Convert 100 Celsius to Fahrenheit"},
    {"type": "CRYSTAL", "payload": "Convert 0 Celsius to Fahrenheit"},
    
    # TYPE 2: Flash (Cheap/Fast) - Simple geography/facts
    {"type": "FLASH", "payload": "Capital of Spain?"},
    {"type": "FLASH", "payload": "What is 2+2?"},
    
    # TYPE 3: Pro (Expensive/Slow) - Creative coding
    {"type": "PRO", "payload": "Write a Python haiku generator."},
    {"type": "PRO", "payload": "Explain quantum entanglement like I'm 5."}
]

print(f"--- 🌊 INJECTING STRESS TEST (20 Tasks) ---")
for i in range(20):
    task = random.choice(tasks)
    # Add unique ID to track in logs
    payload = {"id": f"stress_{i}_{task['type']}", "payload": task['payload']}
    r.rpush(QUEUE, json.dumps(payload))
    print(f">> 📨 Sent [{task['type']}]: {task['payload'][:30]}...")
    time.sleep(0.1)

print(">> ✅ FIREHOSE COMPLETE. Watch the Dashboard!")
