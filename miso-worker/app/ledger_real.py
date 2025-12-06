import json
import os
import time
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_FILE = os.path.join(BASE_DIR, "central_bank.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [BANK] %(message)s')
logger = logging.getLogger(__name__)

class CentralBank:
    def __init__(self, initial_funding=2.00):
        self.load_bank(initial_funding)

    def load_bank(self, initial_funding):
        if os.path.exists(BANK_FILE):
            with open(BANK_FILE, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "balance": initial_funding,
                "total_spend": 0.00,
                "history": []
            }
            self.save_bank()

    def save_bank(self):
        with open(BANK_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)

    def authorize_transaction(self, agent_name, estimated_cost):
        if self.data["balance"] >= estimated_cost:
            self.data["balance"] -= estimated_cost
            self.data["total_spend"] += estimated_cost
            self.save_bank()
            return True
        else:
            logger.critical(f"💸 INSOLVENCY EVENT: {agent_name} requested ${estimated_cost}. Balance: ${self.data['balance']:.4f}")
            return False

    def get_status(self):
        return self.data["balance"], self.data["total_spend"]

if __name__ == "__main__":
    bank = CentralBank()
    print(f"Current Balance: ${bank.data['balance']:.4f}")
