import socket

def verify_port_8001():
    ip = "192.168.1.152"
    port = 8001
    print(f"\n[📡] DIAGNOSING PORT {port} ON {ip}...")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        result = s.connect_ex((ip, port))
        if result == 0:
            print(f"[✅] SUCCESS: MISO is listening on Port {port}.")
            print("[!] Postman should be able to reach this address.")
        else:
            print(f"[❌] FAIL: Port {port} is closed or blocked.")
            print("[💡] FIX: Re-run 'python .\miso_hybrid_bot.py' in a separate terminal.")

if __name__ == "__main__":
    verify_port_8001()
