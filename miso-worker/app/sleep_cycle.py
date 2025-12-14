import os
import json
import redis
import sys
import subprocess
import time
from dotenv import load_dotenv
sys.path.append(os.getcwd())
from src.utils.model_factory import get_best_model
from src.utils.s3_state import push_state
from src.utils.github_interface import create_pr

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
TOOLS_DIR = "miso-worker/app/tools"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class HiveMindOptimizer:
    def __init__(self):
        # Connect to the new database
        self.r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        self.model = get_best_model(GEMINI_API_KEY)

    def process_queue(self):
        # Check the queue for new tasks (Non-blocking)
        task_json = self.r.lpop("miso:queue")
        
        if not task_json:
            return # Queue is empty

        try:
            task_data = json.loads(task_json)
            print(f">> 🧠 Pulled Task from Redis: {task_data['prompt'][:40]}...")
            
            # Crystallize (Write Code)
            success = self.crystallize(task_data)
            
            if success:
                # Move to Long-Term Memory (History)
                task_data["result"] = "COMPLETED"
                task_data["completed_at"] = time.time()
                self.r.lpush("miso:history", json.dumps(task_data))
                self.r.ltrim("miso:history", 0, 99)
                print(f">> ✅ Task Archived in Redis History.")
            else:
                print(">> ⚠️ Task Failed. Dropping.")
                
        except Exception as e:
            print(f">> ⚠️ Redis Processing Error: {e}")

    def crystallize(self, task):
        prompt = task.get("prompt")
        
        analysis_prompt = f"""
        TASK: {prompt}
        OUTPUT JSON: {{"found": bool, "task_name": "str", "python_code": "str", "test_input": "str"}}
        REQUIREMENTS: 
        1. Code MUST contain a function named `solve(input_str)`.
        2. Code must be robust and self-contained.
        """
        
        try:
            response = self.model.generate_content(analysis_prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            plan = json.loads(text)
        except:
            print(">> ❌ Model Generation Failed")
            return False

        if not plan.get("found"): return False

        safe_name = plan['task_name'].replace(' ', '_').lower()
        tool_name = f"tool_{safe_name}"
        tool_path = f"{TOOLS_DIR}/{tool_name}.py"
        
        # 1. Create Branch
        branch_name = f"feat/miso-{safe_name}-{int(time.time())}"
        subprocess.run(["git", "checkout", "-b", branch_name])

        # 2. Write Code
        with open(tool_path, "w") as f: f.write(plan['python_code'])

        # 3. Sandbox Test
        print(f">> 🧪 TESTING: {tool_name}...")
        tester_code = f"""
import sys
import os
sys.path.append(os.path.abspath('{TOOLS_DIR}'))
import {tool_name}
try:
    print({tool_name}.solve('{plan['test_input']}'))
except Exception as e:
    print(f'FAIL: {{e}}')
"""
        with open("temp_test.py", "w") as f: f.write(tester_code)
        result = subprocess.run([sys.executable, "temp_test.py"], capture_output=True, text=True)
        os.remove("temp_test.py")

        if "FAIL:" in result.stdout or result.returncode != 0:
            print(f">> ❌ TEST FAILED. Reverting...")
            os.remove(tool_path)
            subprocess.run(["git", "checkout", "main"])
            return False

        print(f">> ✅ CRYSTALLIZED: {tool_name}")
        
        # 4. Push & PR
        subprocess.run(["git", "add", tool_path])
        subprocess.run(["git", "commit", "-m", f"Feat(Miso): Created {safe_name} tool"])
        subprocess.run(["git", "push", "origin", branch_name])
        
        create_pr(branch_name, f"Miso Auto-Tool: {plan['task_name']}", f"Automated PR.\nTask: {prompt}")
        
        # 5. Return to base
        subprocess.run(["git", "checkout", "main"])
        return True

    def run(self):
        print(">> 💎 HIVE MIND (REDIS ENABLED): Checking queue...")
        self.process_queue()
        push_state()

if __name__ == "__main__":
    HiveMindOptimizer().run()
