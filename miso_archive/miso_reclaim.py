import subprocess
import os

def reclaim_port(port):
    print(f"[🛡️] RECLAIMING PORT {port}...")
    try:
        # Find the Process ID (PID) using the port
        result = subprocess.check_output(f"netstat -ano | findstr :{port}", shell=True).decode()
        if result:
            pids = set([line.strip().split()[-1] for line in result.splitlines() if "LISTENING" in line])
            for pid in pids:
                print(f"[⚔️] TERMINATING GHOST PROCESS: PID {pid}")
                os.system(f"taskkill /F /PID {pid}")
            print(f"[✅] PORT {port} RECLAIMED.")
        else:
            print(f"[!] No processes found on Port {port}.")
    except Exception as e:
        print(f"[?] Port {port} appears clear or access denied.")

if __name__ == "__main__":
    reclaim_port(8000)
