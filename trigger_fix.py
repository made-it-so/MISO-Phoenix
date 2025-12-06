import os
import redis
import json
import os

REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

payload = {
  "meta": { "timestamp": "2025-12-01T08:00:00Z", "origin": "ORCHESTRATOR_INTEL", "trace_id": "sec-patch-01" },
  "task": {
    "id": "TASK-SEC-PATCH-01",
    "type": "SELF_HEALING",
    "priority": 1,
    "context": { 
        "problem": "Trivy identified vulnerable Flask version (2.3.3).", 
        "solution": "Upgrade Flask to latest secure version and push PR." 
    },
    "directives": [
      {
        "action": "MODIFY",
        "file_path": "miso_api/requirements.txt",
        "spec": {
            "target_line": "Flask==2.3.3",
            "replacement": "Flask>=3.0.0"
        }
      },
      {
        "action": "EXECUTE_SCRIPT",
        "script_content": """
from src.modules.archivist.safe_git_sync import GitArchivist
archivist = GitArchivist()
# This creates a branch named 'evolution/...' and pushes it to GitHub
branch = archivist.sync_state("SECURITY: Upgraded Flask to patch vulnerability")
print(f"PATCH DEPLOYED. Branch: {branch}")
"""
      }
    ]
  }
}

try:
    print("--- TRIGGERING AUTO-REMEDIATION ---")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.rpush('miso:tasks', json.dumps(payload))
    print("TASK QUEUED. MISO should now commit the security fix.")
except Exception as e:
    print(f"ERROR: {e}")
