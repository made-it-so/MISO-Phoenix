cat <<'EOF' > patch_gladiator.py
import os

# HARDENED GLADIATOR LOGIC
CODE = r'''import logging
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
            self.model = self._init_model()
        else:
            self.model = None

    def _init_model(self):
        try:
            # Fallback priority: Flash is fastest/cheapest
            for m in ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
                try: return genai.GenerativeModel(m)
                except: continue
            return None
        except: return None

    def _generate(self, prompt):
        if not self.model: return "!!! ERROR: No API Key !!!"
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```python", "").replace("```", "").strip()
            if len(text) < 10: return "!!! ERROR: Too Short !!!"
            return text
        except Exception as e:
            return f"!!! ERROR: {e} !!!"

    def syntax_check(self, code):
        # FAIL if code starts with error bang or comment
        if not code or code.startswith("!!!") or code.strip().startswith("#"): 
            return False, "Invalid Code / Error State"
        try:
            ast.parse(code)
            return True, "Valid"
        except SyntaxError as e: return False, f"{e}"

    def run_test(self, sol, test):
        if not sol or code.startswith("!!!") or code.strip().startswith("#"): return False, "No Code"
        
        with open("ts.py", "w") as f: f.write(sol)
        with open("tt.py", "w") as f: 
            f.write("import sys\nsys.path.append('.')\nimport ts\n" + test)
        try:
            res = subprocess.run(["python3", "tt.py"], capture_output=True, text=True, timeout=5)
            if os.path.exists("ts.py"): os.remove("ts.py")
            if os.path.exists("tt.py"): os.remove("tt.py")
            
            if res.returncode == 0: return True, res.stdout
            return False, f"CRASH: {res.stderr}"
        except Exception as e: return False, str(e)

    def fight(self, prompt, max_rounds=3):
        logger.info(f"⚔️ DUEL: {prompt}")
        sol = self._generate(f"Write Python code for: {prompt}. Output CODE ONLY.")
        
        for i in range(1, max_rounds + 1):
            valid, msg = self.syntax_check(sol)
            if not valid:
                sol = self._generate(f"Previous attempt failed: {msg}\nWrite Python code for: {prompt}")
                continue

            breaker = self._generate(f"ROLE: Red Team.\nTARGET:\n{sol}\nTASK: Write a unit test that fails. Output CODE ONLY.")
            survived, log = self.run_test(sol, breaker)

            if survived:
                return f"## 🛡️ VERIFIED\n
http://googleusercontent.com/immersive_entry_chip/0

* **If you see "AIza...":** The Key is there. The "Empty Code" was just the logic bug we just patched.
* **If you see "MISSING" or file not found:** You **must** perform the `inject_brain.py` step (Step 1 from the previous turn) with your actual API key.
