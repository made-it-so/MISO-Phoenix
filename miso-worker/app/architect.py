import os
import json
import redis
import re
import sys
import importlib.util
from datetime import datetime
from memory import Hippocampus
from dotenv import load_dotenv
sys.path.append(os.getcwd())
from src.utils.model_factory import get_model_arsenal

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOOLS_DIR = "miso-worker/app/tools"
REGISTRY_PATH = f"{TOOLS_DIR}/registry.json"
TASK_QUEUE = "miso:tasks"

class SovereignArchitect:
    def __init__(self):
        print("--- ARCHITECT V68 (MERCENARY ROUTER) ---")
        self.r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        self.hippocampus = Hippocampus()
        self.arsenal = get_model_arsenal(GEMINI_API_KEY)

    def check_crystal_tools(self, prompt):
        if not os.path.exists(REGISTRY_PATH): return None
        try:
            with open(REGISTRY_PATH, "r") as f: registry = json.load(f)
            for tool in registry:
                if re.search(tool["pattern"], prompt, re.IGNORECASE):
                    print(f" >> 💎 CRYSTAL MATCH: Using {tool['module']} (Zero Cost)")
                    spec = importlib.util.spec_from_file_location(tool["module"], f"{TOOLS_DIR}/{tool['module']}.py")
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module.solve(prompt)
        except: pass
        return None

    def route_task(self, prompt):
        # HEURISTIC ROUTING (The "Value-Added" Decision)
        
        # 1. Complexity Check
        complexity_signals = ["code", "python", "function", "analyze", "why", "reason", "json"]
        is_complex = any(sig in prompt.lower() for sig in complexity_signals) or len(prompt) > 200
        
        if is_complex:
            print(f" >> 🚦 ROUTING: High Complexity -> PRO Model")
            return self.arsenal.get("pro")
        else:
            print(f" >> 🚦 ROUTING: Low Complexity -> FLASH Model (Cost Saving)")
            return self.arsenal.get("flash")

    def execute(self, task):
        prompt = task.get("payload", "")
        
        # 1. ZERO COST (Tools)
        res = self.check_crystal_tools(prompt)
        if res:
            print(f" >> ⚡ RESULT: {res}")
            self.hippocampus.remember(prompt, f"TOOL: {res}")
            return

        # 2. ZERO COST (Backbone)
        if "CRITICAL" in prompt:
            print(" >> ⚔️  Gladiator Engaged.")
            return

        # 3. VARIABLE COST (Mercenary Routing)
        model = self.route_task(prompt)
        if model:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 Cortex Thinking...")
            try:
                response = model.generate_content(prompt)
                print(f" >> 🗣️  CORTEX: {response.text[:100]}...")
                self.hippocampus.remember(prompt, response.text)
            except Exception as e:
                print(f" >> 💥 Execution Error: {e}")

    def loop(self):
        while True:
            task = self.r.blpop(TASK_QUEUE, timeout=5)
            if task: self.execute(json.loads(task[1]))

if __name__ == "__main__":
    SovereignArchitect().loop()
