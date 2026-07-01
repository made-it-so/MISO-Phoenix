import subprocess
import time
import sys

def main():
    print("=== MISO MAINFRAME v1301.5 (RECURSIVE SELF-IMPROVEMENT) ===")
    
    # 1. Start API and Autopilot
    api = subprocess.Popen([sys.executable, "miso_api.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    pilot = subprocess.Popen([sys.executable, "miso_autopilot_v4.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)

    try:
        while True:
            # 2. RUN AUTONOMOUS AUDIT
            subprocess.run([sys.executable, "miso_conflict_detector.py"])
            
            # 3. RUN SELF-EVOLUTION UPDATE (Nodes 4001+)
            subprocess.run([sys.executable, "miso_self_updater.py"])
            
            print(f"[❤] Heartbeat: {time.ctime()} | System: SELF-CORRECTING")
            time.sleep(600)
    except KeyboardInterrupt:
        api.terminate()
        pilot.terminate()
        print("[+] Sovereign Shutdown.")

if __name__ == "__main__":
    main()
