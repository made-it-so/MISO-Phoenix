import urllib.request
import json
import sys

# 1. The Mutation (Code + Self-Verification Test)
# We include a test function so the Immune System (pytest) gives it a Green Pass (Exit Code 0)
mutation_code = """
from datetime import datetime

def get_system_time():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Self-Test for Ouroboros Verification
def test_system_time_format():
    t = get_system_time()
    assert ":" in t
    assert "-" in t
"""

# 2. Package the Payload
payload_str = f"miso_project/utils/time_tool.py|||{mutation_code}"

data = {
    "type": "evolve",
    "payload": payload_str
}

# 3. Transmit to Cortex
req = urllib.request.Request(
    "http://localhost:8000/process",
    data=json.dumps(data).encode('utf-8'),
    headers={'Content-Type': 'application/json'}
)

print(">>> INJECTING MUTATION VECTOR...")
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"CRITICAL FAILURE: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"TRANSMISSION ERROR: {e}")
