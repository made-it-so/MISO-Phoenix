import requests

# UPDATED TO THE GHOST-RANGE
BASE_URL = "http://127.0.0.1:50005"

def troubleshoot():
    print("--- MISO BRIDGE PROBE (v255.00) ---")
    try:
        r = requests.get(f"{BASE_URL}/api/status", timeout=2)
        print(f"PHYSICAL LINK: SUCCESS")
        print(f"SERVER DATA:   {r.json()}")
    except Exception as e:
        print(f"PHYSICAL LINK: FAILED")
        print(f"REASON: {e}")

if __name__ == '__main__':
    troubleshoot()
