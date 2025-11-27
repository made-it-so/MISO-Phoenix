import redis
import json
import os

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

task_payload = {
    "id": "task_exodus_01",
    "type": "ARCHITECTURAL",
    "payload": """
    Analyze your own source code structure.
    Write a production-ready 'Dockerfile' for the MISO Phoenix system.
    Requirements:
    - Base image: python:3.11-slim
    - Install dependencies: redis, google-generativeai, chromadb, web3.
    - Copy the 'miso-worker' directory.
    - Set the entrypoint to run 'architect.py'.
    
    Output ONLY the JSON to write the file: {"filename": "Dockerfile", "content": "..."}
    """
}

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
r.rpush("miso:tasks", json.dumps(task_payload))
print("Injecting Task: SELF-ENCAPSULATION (Dockerfile)...")
