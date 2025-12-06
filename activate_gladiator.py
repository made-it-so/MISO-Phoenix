import os
import redis
import json
import os

REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

# Read the file we just made in Step 1
try:
    with open("src/modules/gan/gladiator.py", "r") as f:
        gladiator_code = f.read()
except FileNotFoundError:
    print("❌ ERROR: Run make_gladiator.py first!")
    exit(1)

# Construct the Cloud Payload
TASK_PROMPT = f"""
SYSTEM UPGRADE DIRECTIVE.

ACTION 1: INSTALL MODULE (Cloud Side).
Write the following content to 'src/modules/gan/gladiator.py':
```python
{gladiator_code}
```

ACTION 2: WIRE INTERFACE.
Execute this shell command to patch the Architect logic:
sed -i '/if task.get("type") == "CHAT_COMMAND":/i \        # GLADIATOR ROUTING\\n        if "CRITICAL" in task.get("payload", ""):\\n            from src.modules.gan.gladiator import GladiatorArena\\n            return self.post_to_chat("assistant", GladiatorArena().fight(prompt))' src/architect.py
"""

payload = {
    "id": "TASK-ACTIVATE-GLADIATOR",
    "type": "SYSTEM_UPGRADE",
    "payload": TASK_PROMPT
}

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.rpush('miso:tasks', json.dumps(payload))
    print("✅ SUCCESS: Activation Task Queued.")
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")
