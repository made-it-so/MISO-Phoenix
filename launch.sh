#!/bin/bash
echo "--- KILLING OLD PROCESSES ---"
sudo fuser -k 5000/tcp || true
echo "--- STARTING API ---"
nohup python3 -u src/modules/control/cortex_api.py > cortex.log 2>&1 &
echo "--- WAITING FOR STARTUP (3s) ---"
sleep 3
echo "--- LOG OUTPUT ---"
tail -n 5 cortex.log
echo "--- NETWORK CHECK ---"
sudo netstat -tulnp | grep 5000
