import os

# PART 1: Imports and Setup
PART_1 = r'''import logging
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
        if not self.model: return "# ERROR: No API Key"
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace("```python", "").replace("```", "").strip()
            if len(text) < 10: return f"# ERROR: Too short: {text}"
            return text
        except Exception as e:
            logger.error(f"Gen Fail: {e}")
            return f"# ERROR: {e}"

    def syntax_check(self, code):
        if not code or "# ERROR" in code: return False, "Invalid Code"
        try:
            ast.parse(code)
            return True, "Valid"
        except SyntaxError as e: return False, f"{e}"

    def run_test(self, sol, test):
        if not sol or "# ERROR" in sol: return False, "No Solution Code"
        
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
'''

# PART 2: The Fight Loop
PART_2 = r'''
    def fight(self, prompt, max_rounds=3):
        logger.info(f"⚔️ DUEL: {prompt}")
        sol = self._generate(f"Write Python code for: {prompt}. Output CODE ONLY.")
        
        for i in range(1, max_rounds + 1):
            valid, msg = self.syntax_check(sol)
            if not valid:
                sol = self._generate(f"Previous code was invalid: {msg}\nWrite Python code for: {prompt}")
                continue

            breaker = self._generate(f"ROLE: Red Team.\nTARGET:\n{sol}\nTASK: Write a unit test that fails. Output CODE ONLY.")
            survived, log = self.run_test(sol, breaker)

            if survived:
                return f"## 🛡️ VERIFIED\n
http://googleusercontent.com/immersive_entry_chip/0

**Check Results:**
```bash
python3 -c "import redis, json; r=redis.Redis(host='miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com', port=6379, decode_responses=True); print('\n'.join([json.loads(m)['content'] for m in r.lrange('miso:chat:history', -5, -1)]))"
