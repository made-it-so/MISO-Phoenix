#!/bin/bash
echo "🚀 LAUNCHING MISO CORPORATION..."

# 1. Kill everything
pkill -f python3
pkill cloudflared

# 2. Start The Board (High Level)
nohup python3 miso-worker/app/board.py > board.log 2>&1 &
echo "🏛️  Board of Directors Seated."

# 3. Start The Executives (Middle Management)
# We assume executive.py handles calling CTO/CFO internally as libraries or sub-processes
nohup python3 miso-worker/app/executive.py > executive.log 2>&1 &
echo "👔 CEO & Executive Staff Online."

# 4. Start The Workforce (Production)
nohup python3 miso-worker/app/worker.py > worker.log 2>&1 &
echo "👷 Worker Swarm Active."

# 5. Start The UI (Control Plane)
nohup python3 -m streamlit run miso-worker/app/admin_console.py     --server.port 8501     --server.address 0.0.0.0     --server.headless true     > dashboard.log 2>&1 &
echo "🎨 Admin Console Rendered."

# 6. Open Tunnel
nohup ./miso-api/cloudflared tunnel --url http://localhost:8501 > tunnel.log 2>&1 &
echo "🚇 Secure Uplink Established."

sleep 8
echo "-------------------------------------------------------"
echo "👇 CORPORATE HQ LINK:"
grep -o 'https://.*\.trycloudflare.com' tunnel.log | head -n 1
echo "-------------------------------------------------------"
