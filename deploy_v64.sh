#!/bin/bash
set -e

echo "--- STARTING MISO V64 (GLADIATOR) DEPLOYMENT ---"

# 1. PATCH THE ARCHITECT (Python Script)
# We create a temp python script to safely inject the routing logic
cat <<'EOF' > patch_architect_safe.py
import os

ARCHITECT_PATH = "miso-worker/app/architect.py"
ROUTING_LOGIC = """
            # GLADIATOR ROUTING
            if "CRITICAL" in task.get("payload", ""):
                from src.modules.gan.gladiator import GladiatorArena
                result = GladiatorArena().fight(prompt)
                self.post_to_chat("assistant", result)
                return
"""

try:
    with open(ARCHITECT_PATH, "r") as f:
        content = f.read()

    TARGET_MARKER = 'if task.get("type") == "CHAT_COMMAND":'
    
    if "GladiatorArena" in content:
        print("⚠️ Architect already wired.")
    elif TARGET_MARKER in content:
        # Insert routing logic BEFORE the chat command check
        new_content = content.replace(TARGET_MARKER, ROUTING_LOGIC + "            " + TARGET_MARKER)
        with open(ARCHITECT_PATH, "w") as f:
            f.write(new_content)
        print("✅ SUCCESS: Architect wired to Gladiator Arena.")
    else:
        print("❌ ERROR: Could not find injection point in architect.py")
        exit(1)

except FileNotFoundError:
    print(f"❌ ERROR: Could not find {ARCHITECT_PATH}")
    exit(1)
EOF

echo "1. Applying Code Patch..."
python3 patch_architect_safe.py

echo "2. Building Docker Image (V64)..."
docker build -t miso-v64-gladiator .

echo "3. Pushing to AWS ECR..."
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 356206423360.dkr.ecr.us-east-1.amazonaws.com
docker tag miso-v64-gladiator:latest 356206423360.dkr.ecr.us-east-1.amazonaws.com/miso-worker:latest
docker push 356206423360.dkr.ecr.us-east-1.amazonaws.com/miso-worker:latest

echo "4. Forcing Fargate Deployment..."
aws ecs update-service --cluster MISO-Cluster-Elastic --service miso-worker-service-iac --force-new-deployment

echo "--- DEPLOYMENT INITIATED ---"
echo "Wait approx 60 seconds for the new task to start."
