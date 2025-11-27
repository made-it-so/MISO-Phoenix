import requests
import time
import sys
import json
import uuid

# --- CONFIGURATION ---
# UPDATED URL
API_URL = "https://tucson-entities-and-toys.trycloudflare.com"

# Endpoint for job ingestion
TRIGGER_ENDPOINT = f"{API_URL}/miso/trigger"

def submit_job(api_key, task_description):
    """
    Submits a natural language task to the MISO Autonomous Cloud.
    """
    print(f"\n🚀 Connecting to MISO Core at: {API_URL}...")
    
    # Generate a unique session ID for tracking
    session_id = f"CLIENT_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "session_id": session_id,
        "api_key": api_key,
        "description": task_description,
        # 'feature_hash' is optional, used for caching optimization
        "feature_hash": str(hash(task_description)) 
    }
    
    try:
        # 1. Send Request
        print(f"   📤 Transmitting Payload ({len(task_description)} chars)...")
        start_time = time.time()
        
        response = requests.post(TRIGGER_ENDPOINT, json=payload, timeout=10)
        
        duration = time.time() - start_time
        
        # 2. Handle Response
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ SUCCESS! Job Accepted.")
            print(f"   🆔 Job ID: {data.get('job_id', 'Unknown')}")
            print(f"   ⏱️  Network Latency: {duration:.2f}s")
            print(f"   🤖 Status: {data.get('status', 'Queued')}")
            print("\n   Check the MISO Dashboard for real-time execution logs.")
            
        elif response.status_code == 401 or response.status_code == 403:
            print(f"   ⛔ ACCESS DENIED: Invalid API Key or Insufficient Funds.")
            
        elif response.status_code == 404:
             print(f"   ❌ ENDPOINT NOT FOUND. Check your API_URL setting.")
             
        elif response.status_code == 502:
            print(f"   ☁️  BAD GATEWAY. The Tunnel is up, but MISO API is down.")
            
        else:
            print(f"   ⚠️  SERVER ERROR ({response.status_code}): {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"   💀 CONNECTION FAILED. Is the Cloudflare Tunnel running?")
    except Exception as e:
        print(f"   ❌ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    print("========================================")
    print("   🧠 MISO PHOENIX CLIENT INTERFACE")
    print("========================================")
    
    user_key = input("🔑 Enter your API Key: ").strip()
    
    # 2. Get Task
    print("\n📝 Describe your task below (e.g., 'Write a python script to parse CSV files'):")
    user_task = input("   > ").strip()
    
    if user_key and user_task:
        submit_job(user_key, user_task)
    else:
        print("❌ Aborted: Key and Task are required.")
