#!/bin/bash
echo "### MISO RESEARCH LAB: HIERARCHICAL AGENT TEST ###"

# Cleanup old runs
rm -f deliberative.py reactive.py executive.py plan.txt danger.tmp

# --- 1. DELIBERATIVE LAYER (The Slow Brain) ---
# Generates a high-level plan. Simulates 2s of "Thinking".
cat <<PY > deliberative.py
import sys, time
def plan(goal):
    print(f"[BRAIN] Thinking about goal: {goal}...", flush=True)
    time.sleep(2) # Simulate heavy compute (LLM Latency)
    # Plan: Go to A -> Go to B -> Go to C -> Finish
    with open("plan.txt", "w") as f:
        f.write("NAVIGATE_POINT_A\nNAVIGATE_POINT_B\nNAVIGATE_POINT_C\nCAPTURE_FLAG")
    print("[BRAIN] Plan generated and saved.", flush=True)

if __name__ == "__main__":
    plan(sys.argv[1] if len(sys.argv) > 1 else "DEFAULT_MISSION")
PY

# --- 2. REACTIVE LAYER (The Fast Reflex) ---
# Runs in background. Randomly creates "Obstacles" (danger.tmp).
cat <<PY > reactive.py
import time, random, os
print("[REFLEX] Sensors Active. Monitoring for obstacles...", flush=True)
# Run for 20 cycles (approx 10 seconds)
for _ in range(20):
    # 30% chance of detecting an obstacle
    if random.random() < 0.3:
        if not os.path.exists("danger.tmp"):
            with open("danger.tmp", "w") as f: f.write("STOP")
            # print("[REFLEX] !!! OBSTACLE DETECTED !!!", flush=True)
    else:
        if os.path.exists("danger.tmp"):
            os.remove("danger.tmp")
            # print("[REFLEX] Path Clear.", flush=True)
    time.sleep(0.5)
print("[REFLEX] Sensors Deactivating.", flush=True)
PY

# --- 3. EXECUTIVE LAYER (The Manager) ---
# Orchestrates the plan but pauses if Reflex detects danger.
cat <<PY > executive.py
import time, os, subprocess, sys

print("[EXEC] Requesting Plan from Brain...", flush=True)
# Call the Deliberative Layer
subprocess.run(["python3", "deliberative.py", "RETRIEVE_ARTIFACT"])

if not os.path.exists("plan.txt"):
    print("[EXEC] No plan found. Aborting.", flush=True)
    sys.exit(1)

steps = open("plan.txt").read().splitlines()
print(f"[EXEC] Received {len(steps)} steps. Starting execution.", flush=True)

for step in steps:
    # Safety Check Loop
    while os.path.exists("danger.tmp"):
        print(f"[EXEC] ⚠️  HALT! Reflex layer reports danger. Pausing '{step}'...", flush=True)
        time.sleep(0.5)
    
    print(f"[EXEC] ✅ Executing Step: {step}", flush=True)
    # Simulate Action Duration
    time.sleep(1.0)

print("[EXEC] Mission Complete.", flush=True)
PY

# --- EXECUTION ORCHESTRATION ---
chmod +x *.py

# Start Reflex in Background
nohup python3 reactive.py > /dev/null 2>&1 &
REACTIVE_PID=$!

# Run Executive in Foreground
python3 executive.py

# Cleanup
kill $REACTIVE_PID 2>/dev/null
rm -f deliberative.py reactive.py executive.py plan.txt danger.tmp
echo "### TEST COMPLETE ###"
