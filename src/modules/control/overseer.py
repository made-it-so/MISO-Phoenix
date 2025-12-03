import redis
import json
import time
import logging
import sys
import os
from datetime import datetime

# --- PATH FIX ---
if os.getcwd() not in sys.path: sys.path.append(os.getcwd())

from src.modules.gan.gladiator import GladiatorArena, BuilderAgent, CriticAgent, broadcast

logger = logging.getLogger('MISO')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# --- CONFIGURATION ---
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
TASK_QUEUE = 'miso:tasks'

def main():
    # 1. Connect to Nervous System
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        r.ping()
        logger.info('OVERSEER: Connected to Redis. Watching for tasks...')
        broadcast('OVERSEER', 'IDLE', 'Waiting for Task', 'Hive Mind active. monitoring queue...')
    except Exception as e:
        logger.error(f'Redis Connection Failed: {e}')
        return

    # 2. Initialize Agents
    builder = BuilderAgent()
    critic = CriticAgent()
    arena = GladiatorArena(builder, critic)

    # 3. The Infinite Loop
    while True:
        try:
            # Blocking Pop: Waits here until a task arrives (0 = wait forever)
            # Returns tuple: ('miso:tasks', '{"task": "..."}')
            queue, payload = r.blpop(TASK_QUEUE, timeout=0)
            
            if payload:
                task_data = json.loads(payload)
                problem = task_data.get('task')
                sender = task_data.get('sender', 'Unknown')
                
                logger.info(f'OVERSEER: Received task from {sender}: {problem}')
                broadcast('OVERSEER', 'RECEIVED', 'Processing', f'Task received: {problem[:30]}...')
                
                # 4. Unleash the Gladiator
                start_time = time.time()
                result = arena.fight(rounds=3, problem=problem)
                duration = time.time() - start_time
                
                # 5. Report Success
                broadcast('OVERSEER', 'COMPLETE', f'{duration:.2f}s', 'Task resolved. Returning to slumber.')
                logger.info('OVERSEER: Task Complete. Sleeping.')
                
        except Exception as e:
            logger.error(f'Overseer Error: {e}')
            time.sleep(5) # Prevent CPU spin on error

if __name__ == '__main__':
    main()