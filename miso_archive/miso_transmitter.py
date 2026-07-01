import urllib.request
import json

TARGET_IP = '159.223.186.21'
URL = f'http://{TARGET_IP}:8080/crucible/roadmap'

print('\033[90m[+] Hypercritic offline synthesis complete. Formatting Next-Gen Roadmap...\033[0m')

# The Evolutionary Directives
roadmap_payload = {
    "generation": "Alpha-1",
    "target_architecture": "Data Ingestion Agent",
    "directives": [
        "1. Eradicate all synchronous blocking I/O calls.",
        "2. Replace lazy bytearray allocation with streaming generators.",
        "3. Achieve zero-dependency standard library execution."
    ],
    "cages_enforced": ["memory_256M", "cpu_0.25", "network_none"]
}

data = json.dumps(roadmap_payload).encode('utf-8')
req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'})

print('\033[93m[+] Firing transmission across the neural link to the Ubuntu Crucible...\033[0m')

try:
    with urllib.request.urlopen(req, timeout=10) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f'\n\033[92m[+] TRANSMISSION SUCCESSFUL:\033[0m {result["status"]}\n')
except Exception as e:
    print(f'\n\033[91m[-] TRANSMISSION FAILED:\033[0m {e}')
    print('\033[90mEnsure the IP is correct and port 8080 is open on the Ubuntu firewall.\033[0m\n')
