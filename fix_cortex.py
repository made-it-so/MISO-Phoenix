import os
content = """from flask import Flask, request, jsonify
from flask_cors import CORS
import redis
import json
import logging

app = Flask(__name__)
CORS(app)

# Connect to Redis
try:
    r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0, decode_responses=True)
    r.ping()
except:
    r = None

@app.route('/miso/trigger', methods=['POST'])
def trigger():
    if not r: 
        return jsonify({'status': 'error', 'msg': 'Redis Dead'}), 500
    
    data = request.json
    command = data.get('command')
    
    # Push to Hive Mind
    r.rpush('miso:tasks', json.dumps({'task': command, 'sender': 'WEB'}))
    
    # Log to terminal so we can see it working
    print(f"COMMAND RECEIVED: {command}")
    
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("CORTEX LISTENING ON PORT 5000...")
    app.run(host='0.0.0.0', port=5000)
"""

with open("cortex_api.py", "w") as f:
    f.write(content)

print("SUCCESS: Cortex API repaired.")
