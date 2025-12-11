import os
import json
import glob
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
REGISTRY_PATH = f"{TOOLS_DIR}/registry.json"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class HiveMindOptimizer:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
        self.model = get_best_model(GEMINI_API_KEY)

    def read_hive_memories(self):
        all_memories = []
        for fpath in glob.glob("miso_memory_*.json"):
            try:
                with open(fpath, "r") as f: all_memories.extend(json.load(f))
            except: pass
        all_memories.sort(key=lambda x: x['timestamp'])
        return all_memories[-50:]

    def crystallize(self, memories):
        memory_str = "\n".join([f"IN: {m['prompt']}" for m in memories])
        analysis_prompt = f"""
        ANALYZE logs. Identify ONE repetitive task for Python automation.
        LOGS: {memory_str}
        OUTPUT JSON: {{"found": bool, "task_name": "str", "regex_trigger": "str", "python_code": "str", "test_input": "str"}}
        REQUIREMENTS: 
        1. Code MUST contain a function named `solve(input_str)` that returns the result.
        2. Code must be robust and self-contained.
        """
        try:
            response = self.model.generate_content(analysis_prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            plan = json.loads(text)

            if not plan.get("found"): return

            # Sanitize name
            safe_name = plan['task_name'].replace(' ', '_').lower()
            tool_name = f"tool_{safe_name}_{int(os.getpid())}"
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
                print(f">> ❌ TEST FAILED.\nOUTPUT: {result.stdout}\nERROR: {result.stderr}")
                os.remove(tool_path)
                subprocess.run(["git", "checkout", "main"]) # Revert branch
                return

            print(f">> ✅ CRYSTALLIZED: {tool_name}")
            
            # 4. Commit and Push Branch
            subprocess.run(["git", "add", tool_path])
            subprocess.run(["git", "commit", "-m", f"Feat(Miso): Created {safe_name} tool"])
            subprocess.run(["git", "push", "origin", branch_name])
            
            # 5. Open PR
            create_pr(branch_name, f"Miso Auto-Tool: {plan['task_name']}", f"Miso created this tool based on repetitive memory patterns.\n\nTest Input: {plan['test_input']}")
            
            # 6. Return to base
            subprocess.run(["git", "checkout", "main"])

        except Exception as e:
            print(f">> ⚠️ Optimizer Error: {e}")
            subprocess.run(["git", "checkout", "main"]) # Safety net

    def run(self):
        print(">> 💎 HIVE MIND OPTIMIZER: Syncing Collective Intelligence...")
        memories = self.read_hive_memories()
        if memories and self.model:
            self.crystallize(memories)
        push_state()

if __name__ == "__main__":
    HiveMindOptimizer().run()
