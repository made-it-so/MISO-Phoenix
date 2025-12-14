#!/bin/bash
cd /home/ubuntu/MISO-Phoenix
source venv/bin/activate

# Kill old processes to be safe
pkill -f streamlit
pkill -f run_daemon
pkill -f hive_manager

# Start the Hive
nohup streamlit run streamlit/app.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
nohup ./run_daemon.sh > daemon.log 2>&1 &
nohup python3 miso-worker/app/hive_manager.py > manager.log 2>&1 &
