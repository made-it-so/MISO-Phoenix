import os
import os
import time
import json
import redis
import random
from datetime import datetime

# --- BIOLOGICAL ECONOMICS ---
# "Neurophysiological homeostasis... maintained by energy constraints."
# The Sovereign ensures the system does not burn out (hallucinate) or starve.

REDIS_HOST = os.getenv("REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# METABOLIC RATES (Cost per action)
COST_PULSE = 0.01       # Cost of existing (Backbone heartbeat)
COST_DREAM = 0.05       # Cost of "Scientist" experiments
INCOME_TASK = 5.00      # Revenue from completing a user task

class TheSovereign:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.wallet_key = "miso:sovereign:wallet"
        self.backbone_key = "miso:backbone:state"
        self.log_key = "miso:sovereign:logs"
        
        # Initialize Genesis Wallet if empty
        if not self.r.exists(self.wallet_key):
            genesis_state = {
                "address": "0xMISO_GENESIS_" + str(int(time.time())),
                "balance": 100.00,  # Starting Energy (ATP)
                "status": "SOLVENT"
            }
            self.r.set(self.wallet_key, json.dumps(genesis_state))

    def get_wallet_state(self):
        return json.loads(self.r.get(self.wallet_key))

    def update_balance(self, amount, reason):
        """
        Adjusts the crypto-economic state.
        """
        wallet = self.get_wallet_state()
        wallet["balance"] = round(wallet["balance"] + amount, 4)
        
        # Criticality Check: Starvation
        if wallet["balance"] <= 0:
            wallet["balance"] = 0
            wallet["status"] = "INSOLVENT"
            self.trigger_hibernation()
        else:
            wallet["status"] = "SOLVENT"
            
        self.r.set(self.wallet_key, json.dumps(wallet))
        return wallet

    def trigger_hibernation(self):
        """
        Forces the Backbone to shut down to save energy.
        """
        log = f"[{datetime.now().strftime('%H:%M:%S')}][SOVEREIGN] CRITICAL: WALLET EMPTY. INITIATING HIBERNATION."
        print(log)
        self.r.rpush(self.log_key, log)
        # In a real scenario, this would kill the Docker container or stop the loop
        # For simulation, we set a flag that the Backbone listens to

    def tax_the_system(self):
        """
        The Metabolic Cycle.
        Reads the logs to see what happened, and charges for it.
        """
        # 1. Charge for Time (The Backbone Pulse)
        self.update_balance(-COST_PULSE, "Metabolic Basal Rate")

        # 2. Charge for Thought (The Scientist)
        # We check if the Scientist performed an experiment recently
        scientist_logs = self.r.lrange("miso:scientist:experiments", -1, -1)
        if scientist_logs:
            last_log = scientist_logs[0]
            # Simple simulation: if log is fresh (< 2s), charge for it
            # (In production, we'd use timestamps or log IDs)
            pass 

        # 3. Log Status
        wallet = self.get_wallet_state()
        if random.random() > 0.8 or wallet["status"] == "INSOLVENT":
            print(f"[{datetime.now().strftime('%H:%M:%S')}][SOVEREIGN] Balance: {wallet['balance']} MISO | Status: {wallet['status']}")

    def main_loop(self):
        print("--- THE SOVEREIGN (METABOLIC REGULATOR) ONLINE ---")
        while True:
            try:
                self.tax_the_system()
                time.sleep(2.0) # Matches Backbone Tick Rate
            except Exception as e:
                print(f"SOVEREIGN ERROR: {e}")
                time.sleep(5)

if __name__ == "__main__":
    sovereign = TheSovereign()
    sovereign.main_loop()
