import os

# 1. Create Control Directory
os.makedirs("src/modules/control", exist_ok=True)
with open("src/modules/control/__init__.py", "w") as f: pass

# 2. Create the Overseer (The Daemon)
overseer_code = [
    "import redis",
    "import json",
    "import time",
    "import logging",
    "import sys",
    "import os",
    "from datetime import datetime",
    "",
    "# --- PATH FIX ---",
    "if os.getcwd() not in sys.path: sys.path.append(os.getcwd())",
    "",
    "from src.modules.gan.gladiator import GladiatorArena, BuilderAgent, CriticAgent, broadcast",
    "",
    "logger = logging.getLogger('MISO')",
    "logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')",
    "",
    "# --- CONFIGURATION ---",
    "REDIS_HOST = 'localhost'",
    "REDIS_PORT = 6379",
    "TASK_QUEUE = 'miso:tasks'",
    "",
    "def main():",
    "    # 1. Connect to Nervous System",
    "    try:",
    "        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)",
    "        r.ping()",
    "        logger.info('OVERSEER: Connected to Redis. Watching for tasks...')",
    "        broadcast('OVERSEER', 'IDLE', 'Waiting for Task', 'Hive Mind active. monitoring queue...')",
    "    except Exception as e:",
    "        logger.error(f'Redis Connection Failed: {e}')",
    "        return",
    "",
    "    # 2. Initialize Agents",
    "    builder = BuilderAgent()",
    "    critic = CriticAgent()",
    "    arena = GladiatorArena(builder, critic)",
    "",
    "    # 3. The Infinite Loop",
    "    while True:",
    "        try:",
    "            # Blocking Pop: Waits here until a task arrives (0 = wait forever)",
    "            # Returns tuple: ('miso:tasks', '{\"task\": \"...\"}')",
    "            queue, payload = r.blpop(TASK_QUEUE, timeout=0)",
    "            ",
    "            if payload:",
    "                task_data = json.loads(payload)",
    "                problem = task_data.get('task')",
    "                sender = task_data.get('sender', 'Unknown')",
    "                ",
    "                logger.info(f'OVERSEER: Received task from {sender}: {problem}')",
    "                broadcast('OVERSEER', 'RECEIVED', 'Processing', f'Task received: {problem[:30]}...')",
    "                ",
    "                # 4. Unleash the Gladiator",
    "                start_time = time.time()",
    "                result = arena.fight(rounds=3, problem=problem)",
    "                duration = time.time() - start_time",
    "                ",
    "                # 5. Report Success",
    "                broadcast('OVERSEER', 'COMPLETE', f'{duration:.2f}s', 'Task resolved. Returning to slumber.')",
    "                logger.info('OVERSEER: Task Complete. Sleeping.')",
    "                ",
    "        except Exception as e:",
    "            logger.error(f'Overseer Error: {e}')",
    "            time.sleep(5) # Prevent CPU spin on error",
    "",
    "if __name__ == '__main__':",
    "    main()"
]

with open("src/modules/control/overseer.py", "w") as f:
    f.write("\n".join(overseer_code))

# 3. Create the Injector (The Remote Control)",
injector_code = [
    "import redis",
    "import json",
    "import sys",
    "",
    "r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)",
    "",
    "if len(sys.argv) < 2:",
    "    print('Usage: python3 inject_task.py \"Write a function...\"')",
    "    sys.exit(1)",
    "",
    "task = sys.argv[1]",
    "payload = json.dumps({'task': task, 'sender': 'CLI_USER'})",
    "",
    "r.rpush('miso:tasks', payload)",
    "print(f'>> Task Injected: {task}')",
    "print(f'>> Queue Length: {r.llen(\"miso:tasks\")}')"
]

with open("inject_task.py", "w") as f:
    f.write("\n".join(injector_code))

print("SUCCESS: Hive Mind (Overseer + Injector) Installed.")
