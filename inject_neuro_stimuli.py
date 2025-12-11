import redis
import json
import time
import os

# Connect to the Brain's Input Channel
r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, decode_responses=True)
TASK_QUEUE = "miso:tasks"

# --- STIMULI PACKETS ---
stimuli = [
    # TYPE A: BACKBONE TRIGGER (Rigid, Fast, "Gladiator")
    {
        "id": "stimulus_001_BACKBONE",
        "type": "SECURITY_EVENT",
        "payload": "CRITICAL: Detect infinite loop in sub-routine A." 
    },
    # TYPE B: NON-RIGID TRIGGER (Flexible, Slow, "Standard LLM")
    {
        "id": "stimulus_002_CORTEX",
        "type": "CREATIVE_TASK",
        "payload": "Describe the concept of 'Nested Learning' in a haiku."
    },
    # TYPE A: BACKBONE TRIGGER (Rigid)
    {
        "id": "stimulus_003_BACKBONE",
        "type": "SECURITY_EVENT",
        "payload": "CRITICAL: Validate AWS credentials format."
    }
]

print("--- 🧠 INJECTING NEURO-STIMULI ---")

for task in stimuli:
    # 1. Push to Hippocampus (Redis)
    r.rpush(TASK_QUEUE, json.dumps(task))
    
    # 2. Log for the User
    category = "⚔️  BACKBONE (Gladiator)" if "CRITICAL" in task['payload'] else "🌊 CORTEX (LLM)"
    print(f">> 💉 Injecting {task['id']} -> Routing expectation: {category}")
    time.sleep(1) # simulate synaptic delay

print("\n--- 👁️  MONITORING BRAIN RESPONSE (miso_brain.log) ---")
print("(Press Ctrl+C to stop watching)\n")
