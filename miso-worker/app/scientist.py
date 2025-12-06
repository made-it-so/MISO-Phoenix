import os
import os
import time
import json
import redis
import random
import google.generativeai as genai
from datetime import datetime

REDIS_HOST = os.getenv("REDIS_HOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENOME_PATH = "miso-worker/prompts/constitution.txt"
TASK_QUEUE = "miso:tasks"

class RealScientist:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        self.backbone_key = "miso:backbone:state"
        self.experiment_log = "miso:scientist:experiments"
        
        if not GEMINI_API_KEY:
            print("CRITICAL: Scientist has no API Key.")
            return
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("--- THE PROFITEER ENGINE (V47) ONLINE ---")

    def observe_backbone(self):
        try:
            state_raw = self.r.get(self.backbone_key)
            return json.loads(state_raw) if state_raw else None
        except: return None

    def consult_the_capitalist(self):
        prompt = """
        ACT AS: A ruthless Cloud FinOps Consultant and Security Auditor.
        GOAL: Identify a specific, high-value problem in AWS infrastructure that costs companies money or risk.
        
        CRITERIA:
        1. Must be solvable with a single Python script using 'boto3'.
        2. Must address 'Waste' (idle resources), 'Security' (exposed ports), or 'Compliance'.
        3. The output must be a specific coding assignment description.
        
        EXAMPLES:
        - "Write a script to identify Elastic IPs that are unassociated and costing money."
        - "Write a script to scan Security Groups for port 22 (SSH) open to 0.0.0.0/0."
        - "Write a script to find RDS snapshots older than 90 days."
        
        OUTPUT ONLY THE CODING ASSIGNMENT STRING.
        """
        try:
            response = self.model.generate_content(prompt)
            lesson = response.text.strip()
            
            task = {
                "id": f"capitalist_dream_{int(time.time())}",
                "type": "HIGH_VALUE_TRAINING",
                "payload": lesson
            }
            
            self.r.rpush(TASK_QUEUE, json.dumps(task))
            
            log = f"[{datetime.now().strftime('%H:%M:%S')}] Capitalist: Identified opportunity '{lesson[:40]}...'"
            print(log)
            self.r.rpush(self.experiment_log, log)
            
        except Exception as e:
            print(f"Capitalist Consultation Failed: {e}")

    def main_loop(self):
        while True:
            state = self.observe_backbone()
            # Dream only in TORPOR to save money
            if state and state.get("mode") == "TORPOR":
                if random.random() > 0.8:
                    self.consult_the_capitalist()
            time.sleep(10.0)

if __name__ == "__main__":
    RealScientist().main_loop()
