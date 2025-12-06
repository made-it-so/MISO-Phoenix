import os
import redis
import json
import os

# TARGET: LIVE CONTROL PLANE
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

payload = {
  "meta": { "timestamp": "2025-12-01T02:00:00Z", "origin": "ORCHESTRATOR_INTEL", "trace_id": "phase2-trivy-init" },
  "task": {
    "id": "TASK-SEC-PHASE2-01",
    "type": "SELF_EVOLUTION",
    "priority": 1,
    "context": { 
        "problem": "Blind to dependencies vulnerabilities.", 
        "solution": "Integrate Trivy Scanner into Dockerfile and create Python wrapper." 
    },
    "directives": [
      {
        "action": "MODIFY",
        "file_path": "Dockerfile",
        "spec": {
            "injection_point": "apt-get install -y",
            "code_change": """    wget \\
    apt-transport-https \\
    gnupg \\
    lsb-release \\"""
        }
      },
      {
        "action": "APPEND",
        "file_path": "Dockerfile",
        "spec": {
            "injection_point": "after_apt_install",
            "code_change": """
# INSTAL TRIVY (SECURITY SCANNER)
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - \\
    && echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | tee -a /etc/apt/sources.list.d/trivy.list \\
    && apt-get update && apt-get install -y trivy
"""
        }
      },
      {
        "action": "CREATE",
        "file_path": "src/modules/security/scanner.py",
        "spec": {
          "class_name": "SecurityScanner",
          "method_signature": "def scan_filesystem(self) -> dict:",
          "logic_requirements": [
            "Run shell command: trivy fs . --format json --output /tmp/scan_results.json",
            "Read /tmp/scan_results.json",
            "Parse JSON and return a list of HIGH/CRITICAL vulnerabilities",
            "Filter out OS-level vulnerabilities (focus on python packages first)"
          ]
        }
      },
      {
        "action": "EXECUTE_SCRIPT",
        "script_content": """
from src.modules.archivist.safe_git_sync import GitArchivist
archivist = GitArchivist()
branch = archivist.sync_state("Phase 2: Added Trivy Security Scanner")
print(f"EVOLUTION BRANCH CREATED: {branch}")
"""
      }
    ]
  }
}

try:
    print("--- INJECTING PHASE 2 EVOLUTION ---")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.rpush('miso:tasks', json.dumps(payload))
    print("TASK QUEUED. MISO will now attempt to rewrite its own DNA.")
except Exception as e:
    print(f"ERROR: {e}")
