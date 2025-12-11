import redis
import json
import time
import os

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
QUEUE = "miso:tasks"

# The "Lesson Plan" - A repetitive task that requires simple logic
# We use temperature conversion because it has a strict formula (C * 9/5 + 32)
tasks = [
    "Convert 0 Celsius to Fahrenheit",
    "Convert 100 Celsius to Fahrenheit",
    "Convert 25 Celsius to Fahrenheit",
    "Convert -40 Celsius to Fahrenheit"
]

print(f"--- 🏫 CLASS IS IN SESSION: Teaching Miso {len(tasks)} examples ---")

for t in tasks:
    payload = {"id": f"train_{time.time()}", "payload": t}
    r.rpush(QUEUE, json.dumps(payload))
    print(f">> 📤 Sent: {t}")
    time.sleep(2) # Give the Cortex time to "think" expensively

print(">> ✅ Training data injected. Waiting for Cortex processing...")
time.sleep(5) # Buffer for async processing
