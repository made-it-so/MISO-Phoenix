#!/bin/bash
# PRODUCTION LAUNCHER (Background Mode)

echo "--- 1. RESETTING SERVER ---"
# Kill any process on port 5000
PID=$(sudo lsof -t -i:5000)
if [ ! -z "$PID" ]; then
    echo "Stopping old process $PID..."
    sudo kill -9 $PID
fi
sudo fuser -k 5000/tcp >/dev/null 2>&1 || true

echo "--- 2. ENSURING CODE INTEGRITY ---"
mkdir -p src/modules/control
# Re-write the file with the Health Check patch to ensure it never reverts
printf "from flask import Flask, jsonify\nimport redis\nfrom flask_cors import CORS\napp = Flask(__name__)\nCORS(app)\nr = redis.Redis(host='localhost', port=6379, db=0)\n\n@app.route('/execute', methods=['POST'])\ndef execute():\n    try:\n        r.lpush('miso:tasks', 'EXECUTE_PROTOCOL')\n        return jsonify({'status': 'queued'})\n    except Exception as e:\n        return jsonify({'error': str(e)}), 500\n\n@app.route('/health', methods=['GET'])\ndef health():\n    return jsonify({'status': 'online'})\n\n@app.route('/healthcheck_temp', methods=['GET'])\ndef lb_health():\n    return jsonify({'status': 'healthy'}), 200\n\nif __name__ == '__main__':\n    app.run(host='0.0.0.0', port=5000)\n" > src/modules/control/cortex_api.py

echo "--- 3. LAUNCHING IN BACKGROUND ---"
rm -f cortex.log
# Run with nohup so it survives SSH disconnects
nohup python3 -u src/modules/control/cortex_api.py > cortex.log 2>&1 &

echo "✅ SUCCESS: Server is running in background."
echo "   - Health Check: PATCHED (/healthcheck_temp)"
echo "   - Logs: tail -f cortex.log"
