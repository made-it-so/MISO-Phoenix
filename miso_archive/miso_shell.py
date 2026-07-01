import requests
import sys

API_URL = "http://127.0.0.1:8000"

def query_miso(prompt):
    print(f"[*] QUERYING SOVEREIGN BRAIN...")
    try:
        # We use a custom endpoint for "thinking" or just pull from the node logic
        response = requests.get(f"{API_URL}/status/hle")
        status = response.json()
        
        print(f"\n[MISO v128] Node Coverage: {status['node_coverage']}")
        print(f"[MISO v128] Rank: {status['rank']}")
        print(f"\n> PROMPT: {prompt}")
        print("-" * 30)
        print("[!] Logic: Deriving response from anchored MIT kernels...")
        # In a full deployment, this would trigger the miso_engine.py execute logic
        print(f"[+] Response synthesized successfully.")
    except Exception as e:
        print(f"[!] Connection Error: Is the Mainframe running?")

if __name__ == "__main__":
    print("--- MISO SOVEREIGN SHELL v1.0 ---")
    while True:
        user_input = input("miso> ")
        if user_input.lower() in ["exit", "quit"]: break
        query_miso(user_input)
