import requests
import json

def inject_axiom():
    url = "http://127.0.0.1:8000/sse"
    
    # Perfectly rigid JSON-RPC payload
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "update_manifold",
            "arguments": {
                "axiom": "AXIOM: Intelligence requires an ORB-equivalent filter to dampen high-contrast noise. Enhancement without Pruning leads to system-state collapse.",
                "rigidity": 0.85  # Forced numerical float
            }
        },
        "id": 100
    }

    print("[+] INJECTING AXIOM INTO MANIFOLD...")
    try:
        # Note: MCP SSE typically uses a POST to a session endpoint, 
        # but we can trigger a tool call via standard POST if the server allows.
        r = requests.post("http://127.0.0.1:8000/tools/call", json=payload, timeout=10)
        print(f"\n--- SERVER_RESPONSE: {r.text} ---")
    except Exception as e:
        print(f"[X] INJECTION FRACTURE: {e}")

if __name__ == '__main__':
    inject_axiom()
