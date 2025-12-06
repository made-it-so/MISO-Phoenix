import os
import redis
import json
import base64
import os
import time

REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

# --- EMBEDDED SOURCE CODE ---
GLADIATOR_CODE = r'''import logging
import os
import ast
import subprocess
import json
import google.generativeai as genai

logger = logging.getLogger("Gladiator")
logger.setLevel(logging.INFO)

class GladiatorArena:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None

    def _generate(self, prompt):
        if not self.model: return "ERROR: No API Key"
        try:
            response = self.model.generate_content(prompt)
            return response.text.replace("```python", "").replace("```", "").strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ""

    def syntax_check(self, code):
        try:
            ast.parse(code)
            return True, "Valid Syntax"
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"

    def run_test(self, solution_code, test_code):
        with open("temp_solution.py", "w") as f: f.write(solution_code)
        with open("temp_test.py", "w") as f: 
            f.write("import sys\nsys.path.append('.')\nimport temp_solution\n")
            f.write(test_code)
        try:
            result = subprocess.run(["python3", "temp_test.py"], capture_output=True, text=True, timeout=5)
            if os.path.exists("temp_solution.py"): os.remove("temp_solution.py")
            if os.path.exists("temp_test.py"): os.remove("temp_test.py")
            if result.returncode == 0: return True, f"PASSED: {result.stdout}"
            else: return False, f"CRASHED: {result.stderr}"
        except Exception as e: return False, f"EXECUTION ERROR: {e}"

    def fight(self, user_request, max_rounds=3):
        logger.info(f"⚔️ GLADIATOR ARENA OPENED: {user_request}")
        current_solution = self._generate(f"Write Python code for: {user_request}. Output ONLY code.")
        
        for round_id in range(1, max_rounds + 1):
            valid, msg = self.syntax_check(current_solution)
            if not valid:
                current_solution = self._generate(f"Fix this Syntax Error: {msg}\n\nCODE:\n{current_solution}")
                continue

            breaker_script = self._generate(f"ROLE: Red Team QA.\nTARGET CODE:\n{current_solution}\nTASK: Write a Python script to break this. Output ONLY code.")
            survived, battle_log = self.run_test(current_solution, breaker_script)

            if survived:
                return f"## 🛡️ GLADIATOR VERIFIED SOLUTION\n\n
