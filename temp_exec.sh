#!/bin/

# MISO V19: Swarm Intelligence Simulation
# This script demonstrates a decentralized system of agents working collaboratively.
# The swarm's task is to increment a number in a shared file up to a target value.
# Each agent follows a simple local rule: only increment the number if it's their "turn".
# A "killer" process randomly terminates agents to demonstrate the system's robustness.
# The swarm succeeds if the target is reached, even with failing nodes.

# --- Configuration ---
NUM_AGENTS=10
TARGET_COUNT=100
KILL_INTERVAL_SEC=4 # How often to terminate a random agent

# --- Safe Setup with Trap for Cleanup ---
# Use mktemp to create a unique, secure directory for the simulation
SWARM_DIR=$(mktemp -d swarm_simulation_XXXXXX)
# Change to the new directory and handle potential errors
cd "$SWARM_DIR" || { echo "ERROR: Could not change to temp directory '$SWARM_DIR'"; exit 1; }

# This trap ensures that cleanup runs when the script exits for any reason (success, error, or Ctrl+C).
trap cleanup EXIT

# Global variables to hold PIDs for the trap
KILLER_PID=""
AGENT_PIDS=()

cleanup() {
    echo # Newline for cleaner exit
    echo "INFO: Cleaning up processes and files in '${SWARM_DIR}'."
    # Use pkill to terminate all child processes of this script's process group.
    # This is more robust than relying on a potentially stale PID file.
    # The 'kill 0' command sends a signal to all processes in the current process group.
    kill 0 2>/dev/null
    
    # Go back to the original directory before removing the temp one
    cd ..
    rm -rf "$SWARM_DIR"
    echo "INFO: Simulation cleanup complete."
}

echo "INFO: Setting up swarm simulation environment in ./${SWARM_DIR}"

# Initialize the shared state file
echo 0 > count.txt
touch pids.txt # Still used by killer, but not for primary cleanup

# --- Create Agent Script (agent.py) ---
# This script represents a single agent in the swarm.
# It uses file locking to prevent race conditions on the shared 'count.txt' file.
cat <<EOF > agent.py
import sys
import time
import random
import fcntl
import os

if len(sys.argv) != 4:
    print(f"Usage: python3 {sys.argv[0]} <agent_id> <total_agents> <target_count>")
    sys.exit(1)

agent_id = int(sys.argv[1])
num_agents = int(sys.argv[2])
target = int(sys.argv[3])
count_file = 'count.txt'
log_file = f"agent_{agent_id}.log"

def log(message):
    with open(log_file, 'a') as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Agent {agent_id}: {message}\\n")

log("Starting up.")

while True:
    try:
        # Stagger agents to reduce initial contention
        time.sleep(random.uniform(0.1, 0.5))

        with open(count_file, 'r+') as f:
            # Acquire an exclusive lock on the file. This is a critical step
            # for decentralized coordination, ensuring only one agent modifies the state at a time.
            fcntl.flock(f, fcntl.LOCK_EX)

            try:
                current_count_str = f.read().strip()
                if not current_count_str:
                    continue
                
                current_count = int(current_count_str)

                # Check if the collective goal has been reached
                if current_count >= target:
                    log(f"Target of {target} reached. Shutting down.")
                    break

                # LOCAL RULE: Agent only acts if the current count matches its turn
                if current_count % num_agents == agent_id:
                    new_count = current_count + 1
                    f.seek(0)
                    f.truncate()
                    f.write(str(new_count))
                    log(f"Incremented count to {new_count}")
            finally:
                # Ensure unlock happens even if errors occur inside the locked block.
                fcntl.flock(f, fcntl.LOCK_UN)

    except (IOError, ValueError) as e:
        log(f"File access error: {e}. Retrying.")
        time.sleep(1)
    except Exception as e:
        log(f"An unexpected error occurred: {e}")
        break
EOF

# --- Create Killer Script (killer.py) ---
# This script simulates random node failure to test swarm robustness.
# *** FIX: Added file locking to prevent race conditions on pids.txt ***
cat <<EOF > killer.py
import time
import random
import os
import sys
import fcntl

if len(sys.argv) != 3:
    print(f"Usage: python3 {sys.argv[0]} <pid_file> <kill_interval_sec>")
    sys.exit(1)

pid_file = sys.argv[1]
kill_interval_sec = int(sys.argv[2])
log_file = "killer.log"

def log(message):
    with open(log_file, 'a') as f:
        f.write(f"{time.strftime('%H:%M:%S')} - Killer: {message}\\n")

log(f"Process started. Will terminate a random agent every {kill_interval_sec} seconds.")

while True:
    time.sleep(kill_interval_sec)
    try:
        # Use 'r+' to allow reading and writing while holding the lock
        with open(pid_file, 'r+') as f:
            # Acquire exclusive lock to ensure atomic read-modify-write
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                pids = [pid.strip() for pid in f.readlines() if pid.strip()]

                if not pids:
                    log("No agents left to terminate. Exiting.")
                    break

                pid_to_kill = random.choice(pids)
                
                try:
                    os.kill(int(pid_to_kill), 9) # Use SIGKILL for forceful termination
                    log(f"SUCCESS: Terminated agent with PID {pid_to_kill}.")
                except ProcessLookupError:
                    log(f"INFO: Agent with PID {pid_to_kill} was already gone.")
                except Exception as e:
                    log(f"ERROR: Failed to kill PID {pid_to_kill}: {e}")

                # Atomically update the PID file
                remaining_pids = [p for p in pids if p != pid_to_kill]
                f.seek(0)
                f.truncate()
                for pid in remaining_pids:
                    f.write(f"{pid}\\n")
            finally:
                # Ensure unlock happens even if errors occur
                fcntl.flock(f, fcntl.LOCK_UN)

    except FileNotFoundError:
        log(f"ERROR: PID file '{pid_file}' not found. Stopping.")
        break
    except Exception as e:
        log(f"An unexpected error occurred: {e}")
EOF

# --- Deployment ---
echo "INFO: Deploying ${NUM_AGENTS} agents in the background."
for i in $(seq 0 $((NUM_AGENTS - 1))); do
    nohup python3 agent.py "$i" "$NUM_AGENTS" "$TARGET_COUNT" > /dev/null 2>&1 &
    AGENT_PID=$!
    echo "$AGENT_PID" >> pids.txt
done
echo "INFO: All agents deployed."

echo "INFO: Deploying killer agent to test swarm robustness."
nohup python3 killer.py pids.txt "$KILL_INTERVAL_SEC" > /dev/null 2>&1 &
KILLER_PID=$!

# --- Monitoring ---
echo "INFO: Monitoring progress. Target is ${TARGET_COUNT}. Press Ctrl+C to stop."
CURRENT_COUNT=0
while [ "$CURRENT_COUNT" -lt "$TARGET_COUNT" ]; do
    # Check if count.txt exists and is not empty before reading
    if [ -s count.txt ]; then
        CURRENT_COUNT=$(cat count.txt)
        # Progress bar
        PERCENT=$((CURRENT_COUNT * 100 / TARGET_COUNT))
        BAR=$(printf "%0.s#" $(seq 1 $((PERCENT / 2))))
        printf "\rProgress: [%-50s] %d%% (%d/%d)" "$BAR" "$PERCENT" "$CURRENT_COUNT" "$TARGET_COUNT"
    else
        printf "\rWaiting for swarm to initialize..."
    fi
    sleep 1
done

echo # Newline after progress bar
echo "--------------------------------------------------"
echo "SUCCESS: Swarm has reached the target count of ${TARGET_COUNT}!"
echo "This demonstrates robustness, as the goal was achieved despite random agent failures."
echo "INFO: Simulation complete. Log files are in '${SWARM_DIR}' directory."

# The 'trap cleanup EXIT' will handle all final cleanup automatically.