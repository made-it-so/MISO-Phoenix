#!/bin/bash
echo ">> 🟢 STARTING MISO DAEMON..."
echo ">> ------------------------------------------"

while true; do
    echo ">> [$(date +'%H:%M:%S')] ⏰ Waking Miso..."
    
    # Run the worker and capture exit code
    python3 miso-worker/app/sleep_cycle.py
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -ne 0 ]; then
        echo ">> ⚠️  Miso crashed (Code $EXIT_CODE). Restarting in 10s..."
    else
        echo ">> 💤 Miso is resting for 60 seconds..."
    fi
    
    # Sleep before next cycle
    sleep 60
done
