import os
import redis
import json
import sys

r = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=6379, db=0, decode_responses=True)

if len(sys.argv) < 2:
    print('Usage: python3 inject_task.py "Write a function..."')
    sys.exit(1)

task = sys.argv[1]
payload = json.dumps({'task': task, 'sender': 'CLI_USER'})

r.rpush('miso:tasks', payload)
print(f'>> Task Injected: {task}')
print(f'>> Queue Length: {r.llen("miso:tasks")}')