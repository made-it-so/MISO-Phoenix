import subprocess
import os

def reclaim_8001():
    print("[⚔️] SCANNING FOR GHOST PROCESS ON PORT 8001...")
    try:
        # Find the Process ID (PID)
        result = subprocess.check_output("netstat -ano | findstr :8001", shell=True).decode()
        if result:
            pids = set([line.strip().split()[-1] for line in result.splitlines() if "LISTENING" in line])
            for pid in pids:
                print(f"[💥] TERMINATING GHOST: PID {pid}")
                os.system(f"taskkill /F /PID {pid}")
            print("[✅] PORT 8001 IS NOW CLEAR.")
        else:
            print("[!] Port 8001 is already clear.")
    except Exception:
        print("[?] No active process found on Port 8001.")

if __name__ == "__main__":
    reclaim_8001()
