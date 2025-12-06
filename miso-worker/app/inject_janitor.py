import os
import redis
import json
import os

# Default to Cloud Redis if not set locally
DEFAULT_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_HOST = os.getenv("REDIS_HOST", DEFAULT_HOST)

task = {
    "id": "TASK_COMMERCIAL_SRE_01",
    "type": "INFRASTRUCTURE_AUDIT",
    "payload": """
    ACT AS: Senior Cloud Reliability Engineer.
    GOAL: Audit the AWS account you are running in.
    
    SCRIPT REQUIREMENTS:
    1. Import boto3.
    2. List all ECS Clusters and their running task counts.
    3. List all S3 Buckets.
    4. Check for any CloudWatch Log Groups larger than 100MB (Waste).
    5. Generate a 'cost_savings_report.md' with your findings.
    6. Print the report content to STDOUT so I can see it in the logs.
    
    Output ONLY the JSON to write this script: {"filename": "aws_audit.py", "content": "..."}
    """
}

def inject():
    print(f"Connecting to Synapse: {REDIS_HOST}...")
    try:
        r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        r.rpush("miso:tasks", json.dumps(task))
        print("✅ COMMERCIAL PAYLOAD INJECTED: SRE AUDIT")
    except Exception as e:
        print(f"❌ INJECTION FAILED: {e}")

if __name__ == "__main__":
    inject()
