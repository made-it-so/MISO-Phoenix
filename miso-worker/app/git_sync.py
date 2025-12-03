import os
import subprocess
from datetime import datetime

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"GIT ERROR: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"GIT EXCEPTION: {e}")
        return False

def auto_save():
    print("--- INITIATING AUTONOMOUS BACKUP ---")
    
    # 1. Configure Identity (If not set)
    run_command('git config --global user.email "miso@autonomous.ai"')
    run_command('git config --global user.name "MISO Phoenix"')
    
    # 2. Add All Changes
    if not run_command('git add .'): return
    
    # 3. Commit with Timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    commit_msg = f"MISO AUTO-SAVE: Skill Acquisition {timestamp}"
    if not run_command(f'git commit -m "{commit_msg}"'):
        print("Nothing to commit.")
        return

    # 4. Push to Remote
    # Note: This requires the container to have SSH keys or a token.
    # For this V53 implementation, we assume the volume is mounted 
    # or the token is in the remote URL.
    if run_command('git push origin main'):
        print(f"✅ BACKUP COMPLETE: {timestamp}")
    else:
        print("❌ PUSH FAILED (Check Credentials)")

if __name__ == "__main__":
    auto_save()
