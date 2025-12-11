import requests

# URL of your API (bypassing the dashboard)
url = "http://localhost:8000/process"

# The payload (Prompt + Image Flag)
payload = {
    "prompt": "Test connection from host",
    "image": "test_image_data" # Simulating an image
}

print(f"🚀 Sending request to {url}...")

try:
    response = requests.post(url, json=payload, timeout=5)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📜 Response Body: {response.json()}")

except requests.exceptions.ConnectionError:
    print("❌ Connection Refused. Docker is not forwarding port 8000.")
except Exception as e:
    print(f"❌ Error: {e}")
