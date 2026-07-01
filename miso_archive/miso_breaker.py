import time
import os
import json
from datetime import datetime, timedelta

# 1. Configuration: The "Burnout Threshold"
MAX_COMMITS_PER_HOUR = 5
LOCK_DURATION_MINUTES = 5
TRACKER_FILE = "miso_brain_load.json"

def check_cognitive_load():
    now = datetime.now()
    
    # Load or create the interaction ledger
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as f:
            data = json.load(f)
            # Convert strings back to datetime
            timestamps = [datetime.fromisoformat(ts) for ts in data["commits"]]
    else:
        timestamps = []

    # Filter for commits within the last hour
    hour_ago = now - timedelta(hours=1)
    recent_commits = [ts for ts in timestamps if ts > hour_ago]

    print(f"\n[MISO-BREAKER] Prefrontal Cadence: {len(recent_commits)} commits/hr")

    # 2. Trigger the Temporal Breaker
    if len(recent_commits) >= MAX_COMMITS_PER_HOUR:
        wait_time = (recent_commits[0] + timedelta(hours=1)) - now
        print("\n--- !!! COGNITIVE OVERLOAD DETECTED !!! ---")
        print(f"Vahe, your creative prefrontal cortex is in a high-beta 'Always-On' state.")
        print(f"To prevent burnout and 'MISO Fatigue,' a mandatory Incubation Phase is active.")
        print(f"The 'Make It SO' button is locked for {int(wait_time.total_seconds()/60)} more minutes.")
        print("\nACTION SUGGESTED: Stand up. Walk. Mediate. Let the machine process the logic.")
        return False

    # 3. Log the current commit
    timestamps.append(now)
    with open(TRACKER_FILE, "w") as f:
        json.dump({"commits": [ts.isoformat() for ts in timestamps]}, f)
    
    print("[SUCCESS] Cognition within safe limits. Substrate access granted.")
    return True

if __name__ == "__main__":
    if check_cognitive_load():
        print("-> Executing MISO Phase 3 Logic...")
        # (This is where the actual data work would happen)
    else:
        # Prevent execution
        exit(1)
