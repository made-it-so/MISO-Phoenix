#!/bin/bash

# --- SYSTEMD CONFIGURATION ---
PROJECT_DIR="/home/ubuntu/MISO-Phoenix"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
LOG_FILE="$PROJECT_DIR/miso_brain.log"
SLEEP_INTERVAL=300

# Ensure we are in the right directory
cd "$PROJECT_DIR" || exit 1

# Environment Toggles (CPU Optimization)
export CUDA_VISIBLE_DEVICES=""
export ONNXRUNTIME_EXECUTION_PROVIDERS='["CPUExecutionProvider"]'
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

echo "--- 🧠 MISO SYSTEMD SERVICE STARTING ---" >> "$LOG_FILE"
# RESURRECTION PROTOCOL 
$VENV_PYTHON src/utils/s3_state.py pull >> "$LOG_FILE" 2>&1 


# 1. START ARCHITECT (Fast Loop)
# We use the absolute path to the virtualenv python
nohup $VENV_PYTHON miso-worker/app/architect.py >> "$LOG_FILE" 2>&1 &
ARCHITECT_PID=$!

# 2. START SLEEP CYCLE (Slow Loop)
(
    while true; do
        sleep "$SLEEP_INTERVAL"
        echo ">> [$(date +%T)] 💤 TRIGGERING SLEEP CYCLE..." >> "$LOG_FILE"
        # Optional: signal architect to pause if needed, but for now we let them run concurrently
        # to maximize throughput as per the 'Parallelizing Linear Transformers' paper concepts.
        $VENV_PYTHON miso-worker/app/sleep_cycle.py >> "$LOG_FILE" 2>&1
    done
) > /dev/null 2>&1 &
SCHEDULER_PID=$!

echo ">> 🚀 SERVICE LIVE. PIDs: $ARCHITECT_PID, $SCHEDULER_PID" >> "$LOG_FILE"

# 3. KEEP ALIVE
# This allows systemd to monitor the main process.
wait $ARCHITECT_PID
