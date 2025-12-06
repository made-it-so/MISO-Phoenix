import os

# Ensure directories exist
os.makedirs("src/modules/gan", exist_ok=True)

# THE NEW, SAFE GLADIATOR CODE
# Notice the import of DockerSandbox and the changed run_test method.
NEW_GLADIATOR_CODE = r'''import logging
import os
import ast
import json
import google.generativeai as genai

# IMPORT THE SECURITY SANDBOX
# If this import fails, ensure create_sandbox.py was run!
try:
    from src.modules.safety.sandbox import DockerSandbox
except ImportError:
    # Fallback mock if sandbox isn't ready yet
    class DockerSandbox:
        def run(self, code): return False, "ERROR: Sandbox Module Missing"

logger = logging.getLogger("Gladiator")
logger.setLevel(logging.INFO)

class GladiatorArena:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._init_model()
        else:
            self.model = None

    def _init_model(self):
        try:
            return genai.GenerativeModel('gemini-1.5-flash')
        except: return None

    def _generate(self, prompt):
        if not self.model: return "# ERROR: No API Key"
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```python", "").replace("```", "").strip()
            return text if len(text) > 5 else "# ERROR: Empty"
        except Exception as e: return f"# ERROR: {e}"

    def syntax_check(self, code):
        if not code or code.startswith("#") or "!!!" in code: return False, "Invalid Code"
        try: ast.parse(code); return True, "OK"
        except Exception as e: return False, str(e)

    def run_test(self, sol, test):
        """
        UPDATED: Runs the test inside the Docker Sandbox.
        """
        if not sol or sol.startswith("#"): return False, "No Code"
        
        # Combine Solution and Test into one script for the sandbox
        # We replace imports because they are now in the same file
        combined_script = f"""
# --- SOLUTION CODE ---
{sol}

# --- TEST HARNESS ---
# (Auto-generated header)
import sys
try:
    {test.replace("import temp_solution", "# import temp_solution skipped")}
except Exception as e:
    print(f"TEST CRASHED: {e}")
    exit(1)
"""
        # Initialize the Secure Sandbox
        box = DockerSandbox(timeout=10)
        
        # EXECUTE IN ISOLATION
        success, output = box.run(combined_script)
        
        return success, output

    def fight(self, prompt, max_rounds=3):
        logger.info(f"⚔️ FIGHT: {prompt}")
        sol = self._generate(f"Write Python code for: {prompt}. Output CODE ONLY.")
        for i in range(max_rounds):
            ok, msg = self.check(sol)
            if not ok: 
                sol = self._gen(f"Fix error: {msg}\nCode:\n{sol}"); continue
            
            atk = self._gen(f"Role: QA. Target:\n{sol}\nTask: Write failing test. Output CODE ONLY.")
            win, log = self.run_test(sol, atk)
            
            if win: return f"## 🛡️ VERIFIED (SANDBOXED)\n
