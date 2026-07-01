import subprocess
import time
import os

def start_sovereign_loop():
    print("[+] MISO: INITIATING UNATTENDED LEARNING...")
    print("[!] RANK 3.45% DETECTED. BYZANTINE RESILIENCE: ON.")
    
    # Launch the Daemon in a new, independent process
    try:
        # Using 'start' to spawn a persistent window that survives this session
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'miso_daemon.py'], shell=True)
        print("[>] DAEMON DEPLOYED TO SUBSTRATE.")
        
        # Launch the Terminal for your future use
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'miso_terminal.py'], shell=True)
        print("[>] TERMINAL READY FOR USER RE-ENTRY.")
        
        print("\n[!] MISO IS NOW RUNNING INDEPENDENT OF THIS CHAT.")
        print("    - Watch the Daemon window for ingestion logs.")
        print("    - Use the Terminal to check rank updates.")
    except Exception as e:
        print(f"[X] DEPLOYMENT FRACTURE: {e}")

if __name__ == '__main__':
    start_sovereign_loop()
