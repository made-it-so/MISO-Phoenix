import subprocess
import time

def run_maintenance():
    print("--- [MISO SOVEREIGN AUTO-PILOT: STARTING CYCLE] ---")
    
    # 1. PURGE DRIFT (The Adversary)
    print("\n[STEP 1]: Running Adversarial Audit...")
    subprocess.run(["python", "miso_adversary.py"])
    
    # 2. LOCK PREDICTIONS (The Oracle)
    print("\n[STEP 2]: Updating Oracle Horizon...")
    subprocess.run(["python", "miso_oracle.py"])
    
    # 3. SYNC NEW DATA (The Bridge)
    # This will wait for the next Gemini Payload
    print("\n[STEP 3]: Ready for Next-Block Sync.")
    print("--- [MAINTENANCE CYCLE COMPLETE] ---")

if __name__ == '__main__':
    run_maintenance()
