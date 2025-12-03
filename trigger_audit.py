import redis
import json
import os

# TARGET: LIVE CONTROL PLANE
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

payload = {
  "meta": { "timestamp": "2025-12-01T03:00:00Z", "origin": "ORCHESTRATOR_INTEL", "trace_id": "sec-audit-01" },
  "task": {
    "id": "TASK-SEC-SCAN-01",
    "type": "SECURITY_AUDIT",
    "priority": 1,
    "context": { 
        "problem": "Unknown vulnerability posture.", 
        "solution": "Execute Trivy FS scan via new SecurityScanner module." 
    },
    "directives": [
      {
        "action": "EXECUTE_SCRIPT",
        "script_content": """
from src.modules.security.scanner import SecurityScanner
import json

scanner = SecurityScanner()
report = scanner.run_scan()

# Print summary to logs (MISO will ingest this)
print(f"AUDIT COMPLETE. FOUND {report.get('count', 0)} ISSUES.")
if report.get('issues'):
    print(f"TOP RISK: {report['issues'][0]['pkg']} ({report['issues'][0]['severity']})")
"""
      }
    ]
  }
}

try:
    print("--- TRIGGERING SELF-AUDIT ---")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.rpush('miso:tasks', json.dumps(payload))
    print("TASK QUEUED. MISO is now scanning itself.")
except Exception as e:
    print(f"ERROR: {e}")
