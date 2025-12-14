import os
import json
import redis
import time
import sys
from dotenv import load_dotenv
sys.path.append(os.getcwd())
from src.utils.model_factory import get_best_model

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class HiveManager:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        self.model = get_best_model(GEMINI_API_KEY)

    def run(self):
        print(">> 👑 HIVE MANAGER: Online. Waiting for complex projects...")
        while True:
            # Check for high-level projects
            project_json = self.r.lpop("miso:projects")
            
            if project_json:
                try:
                    project = json.loads(project_json)
                    print(f">> 👑 Received Project: {project['prompt']}")
                    self.delegate(project['prompt'])
                except Exception as e:
                    print(f">> ⚠️ Manager Error: {e}")
            
            time.sleep(5)

    def delegate(self, goal):
        # The prompt that forces MISO to become an Architect
        delegation_prompt = f"""
        GOAL: {goal}
        ROLE: You are a Senior Software Architect. Break this goal into 3-5 distinct, atomic coding tasks.
        CONSTRAINTS:
        1. Each task must be a single, standalone Python tool or script.
        2. Format each task as a command: "Create a tool that..."
        3. Ensure the tools can work together (e.g., one saves a file, the other reads it).
        
        OUTPUT FORMAT: JSON list of strings.
        Example: ["Create a tool that scrapes X", "Create a tool that analyzes X", "Create a tool that graphs X"]
        """
        
        try:
            response = self.model.generate_content(delegation_prompt)
            # clean response
            text = response.text.replace("```json", "").replace("```", "").strip()
            tasks = json.loads(text)
            
            print(f">> 👑 Strategy Formulated: {len(tasks)} sub-tasks found.")
            
            for i, task_str in enumerate(tasks):
                # Add context to the prompt so the worker knows the bigger picture
                full_prompt = f"Project Context: {goal}. Task {i+1}/{len(tasks)}: {task_str}"
                
                payload = {
                    "timestamp": time.time(),
                    "prompt": full_prompt,
                    "result": "PENDING"
                }
                # Push to the Worker's Queue
                self.r.rpush("miso:queue", json.dumps(payload))
                print(f">> 📤 Delegated: {task_str[:40]}...")
                
        except Exception as e:
            print(f">> ❌ Delegation Failed: {e}")

if __name__ == "__main__":
    HiveManager().run()
