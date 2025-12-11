#!/bin/bash
WORKER_COUNT=3
LOG_FILE="miso_hive.log"

echo "--- 🚀 LAUNCHING MISO HIVE ($WORKER_COUNT WORKERS) ---"

# Kill old
pkill -f "miso-worker"
pkill -f "streamlit"

# 1. Launch Workers
for i in $(seq 1 $WORKER_COUNT); do
    python3 miso-worker/app/architect.py >> "$LOG_FILE" 2>&1 &
    echo ">> Spawning Worker $i (PID $!)"
done

# 2. Launch Visual Cortex
streamlit run dashboard.py --server.port 8501 > /dev/null 2>&1 &
echo ">> 👁️  Visual Cortex live on Port 8501"

# 3. Launch Sleep Cycle (The Overlord)
(
    while true; do
        sleep 300
        python3 miso-worker/app/sleep_cycle.py >> "$LOG_FILE" 2>&1
    done
) &

echo ">> ✅ HIVE DEPLOYED. Monitor at http://YOUR_IP:8501"
echo ">> Tailing logs..."
tail -f "$LOG_FILE"
