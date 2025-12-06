import json
import os
import logging
import time
from librarian import Librarian

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEDGER_FILE = os.path.join(BASE_DIR, "ledger.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CFO-V22.3] %(message)s')
logger = logging.getLogger(__name__)

class CFO:
    def __init__(self):
        self.load_ledger()
        self.librarian = Librarian()

    def load_ledger(self):
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, 'r') as f: self.data = json.load(f)
        else: self.data = {"hurdle_rate": 0.05, "investments": {}}

    def save_ledger(self):
        with open(LEDGER_FILE, 'w') as f: json.dump(self.data, f, indent=2)

    def approve_budget(self, agent_name, cost):
        advice = self.librarian.consult_archives(f"Create and run {agent_name}")
        logger.info(f"📜 Risk Assessment: {advice}")
        
        # STRICT TAG CHECKING
        if "[BLOCK]" in advice:
            logger.warning(f"⛔ Budget Denied: {advice}")
            return False
            
        if "[ALLOW]" in advice:
            logger.info(f"💰 Budget Approved: {agent_name}")
            return True
            
        # Fallback for ambiguous LLM output
        logger.info(f"💰 Budget Approved (Ambiguous Advice): {agent_name}")
        return True

    def audit_performance(self, agent_name, improvement):
        hurdle = self.data["hurdle_rate"]
        if improvement >= hurdle:
            logger.info(f"✅ PROFIT: {agent_name} (+{improvement:.2%})")
            self.librarian.archive_case_study(agent_name, "SUCCESS", f"ROI {improvement:.2%}")
            self.data["hurdle_rate"] *= 1.05 
        else:
            logger.warning(f"📉 LOSS: {agent_name}. Hurdle: {hurdle:.2%}")
            self.terminate_agent(agent_name, improvement)
        self.save_ledger()

    def terminate_agent(self, agent_name, score):
        logger.info(f"🪓 LIQUIDATING: {agent_name}")
        os.system(f"pkill -f {agent_name}")
        path = os.path.join(BASE_DIR, agent_name)
        if os.path.exists(path): os.remove(path)
        self.librarian.archive_case_study(agent_name, "FAILURE", f"Failed hurdle. Score: {score:.2%}")

if __name__ == "__main__":
    cfo = CFO()
