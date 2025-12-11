import os
import json
import glob
import redis
import sys
import subprocess
from dotenv import load_dotenv
sys.path.append(os.getcwd())
from src.utils.model_factory import get_best_model
from src.utils.s3_state import push_state

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
        # Aggregates memories from ALL worker shards
        all_memories = []
        for fpath in glob.glob("miso_memory_*.json"):
            try:
                with open(fpath, "r") as f: all_memories.extend(json.load(f))
            except: pass
        # Sort by time and take latest 50
        all_memories.sort(key=lambda x: x['timestamp'])
        return all_memories[-50:]

    def ouroboros_reflection(self, memories):
        # Self-Improvement: Analyze failures to suggest Code Updates
        failures = [m for m in memories if "ERROR" in str(m)]
        if not failures: return

        print(">> 🐍 OUROBOROS: Analyzing system failures for self-repair...")
        # (Placeholder for safety: We currently just log the suggestion)
        prompt = f"Analyze these errors and suggest a python patch for architect.py: {str(failures)}"
        # In a full version, this would generate a git patch.

    def load_registry(self):
        try:
            with open(REGISTRY_PATH, "r") as f: return json.load(f)
        except: return []

    def run(self):
        print(">> 💎 HIVE MIND OPTIMIZER: Syncing Collective Intelligence...")
        memories = self.read_hive_memories()
        if not memories or not self.model: return

        # 1. Crystallization (Tool Building)
        self.crystallize(memories)
        
        # 2. Ouroboros (Self-Reflection)
        self.ouroboros_reflection(memories)
        
        # 3. Nomad Sync (S3 Backup)
        push_state()

    def crystallize(self, memories):
        memory_str = "\n".join([f"IN: {m['prompt']}" for m in memories])
        analysis_prompt = f"""
        ANALYZE logs. Identify ONE repetitive task for Python automation.
        LOGS: {memory_str}
        OUTPUT JSON: {{"found": bool, "task_name": "str", "regex_trigger": "str", "python_code": "str", "test_input": "str"}}
        REQUIREMENTS: Code must be robust and self-contained.
        """
        try:
            response = self.model.generate_content(analysis_prompt)
            text = response.text.replace("```json", "").replace("```", "").strip()
            plan = json.loads(text)
            
            if not plan.get("found"): return

            tool_name = f"tool_{plan['task_name']}_{int(os.getpid())}"
            tool_path = f"{TOOLS_DIR}/{tool_name}.py"
            
            with open(tool_path, "w") as f: f.write(plan['python_code'])
            
            # Sandbox Test
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
                print(f">> ❌ TEST FAILED.")
                os.remove(tool_path)
                return

            print(f">> ✅ CRYSTALLIZED: {tool_name}")
            registry = self.load_registry()
            registry.append({
                "pattern": plan['regex_trigger'],
                "module": tool_name,
                "description": plan['task_name']
            })
            with open(REGISTRY_PATH, "w") as f: json.dump(registry, f, indent=2)
            
        except Exception as e:
            print(f">> ⚠️ Optimizer Error: {e}")

if __name__ == "__main__":
    HiveMindOptimizer().run()
