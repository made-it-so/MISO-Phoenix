import time
import random
import os
import logging
import sys
import subprocess

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CHAOS] %(message)s')
logger = logging.getLogger(__name__)

class ChaosMonkey:
    def __init__(self):
        self.attacks = [
            self.kill_redis_connection,
            self.corrupt_config,
            self.poison_pill
        ]

    def kill_redis_connection(self):
        logger.info("🔥 ATTACK: Simulating Network Partition (Blocking Redis Port)")
        # In a real env, we'd use iptables. 
        # Here, we will rename the config variable in memory or environment to break it.
        # Simulating by deleting the config file temporarily
        if os.path.exists(CONFIG_FILE):
            os.rename(CONFIG_FILE, CONFIG_FILE + ".bak")
            logger.info("   -> Config file kidnapped.")

    def corrupt_config(self):
        logger.info("🔥 ATTACK: Corrupting Hyperparameters")
        with open(CONFIG_FILE + ".bak" if os.path.exists(CONFIG_FILE + ".bak") else CONFIG_FILE, 'w') as f:
            f.write('{"EPSILON": "INVALID_JSON", "MODE": "CHAOS"}') 
        logger.info("   -> Config poisoned.")

    def poison_pill(self):
        logger.info("🔥 ATTACK: Injecting Malformed Data")
        # This relies on the worker running to process it
        pass

    def restore_order(self):
        """Reset environment so we don't permanently brick the system"""
        if os.path.exists(CONFIG_FILE + ".bak"):
            os.rename(CONFIG_FILE + ".bak", CONFIG_FILE)
        
        # Restore valid config
        with open(CONFIG_FILE, 'w') as f:
            f.write('{"EPSILON": 0.15}')
        logger.info("🕊️  Peace restored (for now).")

    def unleash(self):
        attack = random.choice(self.attacks)
        attack()
        
        # Let the system suffer for 10 seconds
        time.sleep(10)
        
        self.restore_order()

if __name__ == "__main__":
    monkey = ChaosMonkey()
    logger.info("👹 CHAOS AGENT LISTENING...")
    while True:
        time.sleep(15) # Attack every 15 seconds
        monkey.unleash()
