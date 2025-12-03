import os

# Ensure directory exists
os.makedirs("src/modules/gan", exist_ok=True)

# We construct the fence string to avoid UI truncation issues
fence = "`" * 3

code = f'''import logging
import os
import ast
import subprocess
import json
import google.generativeai as genai

# Setup Logging
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
        self.history = []

    def _generate(self, prompt):
        if not self.model: return "ERROR: No API Key"
        try:
            response = self.model.generate_content(prompt)
            # Clean up markdown code blocks if the LLM adds them
            return response.text.replace("{fence}python", "").replace("{fence}", "").strip()
        except Exception as e:
            logger.error(f"Generation failed: {{e}}")
            return ""

    def syntax_check(self, code):
        try:
            ast.parse(code)
            return True, "Valid Syntax"
        except SyntaxError as e:
            return False, f"Syntax Error: {{e}}"

    def run_test(self, solution_code, test_code):
        # Write temp files
        with open("temp_solution.py", "w") as f: f.write(solution_code)
        with open("temp_test.py", "w") as f: 
            # Inject import path so the test can find the solution
            f.write("import sys\\nsys.path.append('.')\\nimport temp_solution\\n")
            f.write(test_code)
        
        try:
            # Run with timeout to prevent infinite loops
            result = subprocess.run(["python3", "temp_test.py"], capture_output=True, text=True, timeout=5)
            
            # Cleanup
            if os.path.exists("temp_solution.py"): os.remove("temp_solution.py")
            if os.path.exists("temp_test.py"): os.remove("temp_test.py")

            if result.returncode == 0:
                return True, f"PASSED: {{result.stdout}}"
            else:
                return False, f"CRASHED: {{result.stderr}}"
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT: Test took too long."
        except Exception as e:
            return False, f"EXECUTION ERROR: {{e}}"

    def fight(self, user_request, max_rounds=3):
        logger.info(f"⚔️ GLADIATOR ARENA OPENED: {{user_request}}")
        
        # Round 0: Initial Generation
        current_solution = self._generate(f"Write Python code for: {{user_request}}. Output ONLY code.")
        
        for round_id in range(1, max_rounds + 1):
            # Gate 1: Syntax
            valid, msg = self.syntax_check(current_solution)
            if not valid:
                current_solution = self._generate(f"Fix this Syntax Error: {{msg}}\\n\\nCODE:\\n{{current_solution}}")
                continue

            # Gate 2: The Red Team
            breaker_script = self._generate(f"ROLE: Red Team QA.\\nTARGET CODE:\\n{{current_solution}}\\nTASK: Write a Python script to break this. Output ONLY code.")

            # Gate 3: The Fight
            survived, battle_log = self.run_test(current_solution, breaker_script)

            if survived:
                return f"## 🛡️ GLADIATOR VERIFIED SOLUTION\\n\\n{fence}python\\n{{current_solution}}\\n{fence}\\n\\n**Verified Against:**\\n{fence}python\\n{{breaker_script}}\\n{fence}"
            
            else:
                current_solution = self._generate(f"ROLE: Blue Team Engineer.\\nYOUR CODE FAILED:\\n{{breaker_script}}\\nERROR:\\n{{battle_log}}\\nTASK: Fix the code. Output ONLY code.")

        return f"## ⚠️ GLADIATOR TIMEOUT\\nBest effort solution:\\n{fence}python\\n{{current_solution}}\\n{fence}"
'''

with open("src/modules/gan/gladiator.py", "w") as f:
    f.write(code)

print("✅ SUCCESS: src/modules/gan/gladiator.py created.")
