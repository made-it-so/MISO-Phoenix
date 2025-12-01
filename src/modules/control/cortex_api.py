from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import logging
import sys

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CORTEX')

app = Flask(__name__)
CORS(app)

# Connect to Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()
    logger.info("Connected to Redis.")
except Exception as e:
    logger.error(f"Redis Connection Failed: {e}")
    r = None

@app.route('/miso/trigger', methods=['POST'])
def trigger_task():
    if not r:
        return jsonify({'status': 'error', 'msg': 'Redis Offline'}), 500
    
    data = request.json
    task = data.get('command')
    sender = data.get('sender', 'WEB_UI')
    
    if not task:
        return jsonify({'status': 'error', 'msg': 'No command provided'}), 400
        
    # Push to Hive Mind
    payload = json.dumps({'task': task, 'sender': sender})
    r.rpush('miso:tasks', payload)
    
    logger.info(f"Task Injected: {task}")
    return jsonify({'status': 'success', 'msg': 'Task Injected'})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'module': 'CORTEX'})

if __name__ == '__main__':
    print("CORTEX ONLINE: Listening on Port 5000...")
    app.run(host='0.0.0.0', port=5000)
