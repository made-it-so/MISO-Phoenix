import logging
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

    def test(self, sol, t):
        if not sol or sol.startswith("#"): return False, "No Code"
        try:
            with open("s.py","w") as f: f.write(sol)
            with open("t.py","w") as f: f.write("import sys\nsys.path.append('.')\nimport s\n"+t)
            r = subprocess.run(["python3","t.py"], capture_output=True, text=True, timeout=5)
            if os.path.exists("s.py"): os.remove("s.py")
            if os.path.exists("t.py"): os.remove("t.py")
            return (True, r.stdout) if r.returncode == 0 else (False, r.stderr)
        except Exception as e: return False, str(e)

    def fight(self, prompt, max_rounds=3):
        logger.info(f"⚔️ FIGHT: {prompt}")
        sol = self._gen(f"Write Python code for: {prompt}. Output CODE ONLY.")
        for i in range(max_rounds):
            ok, msg = self.check(sol)
            if not ok: 
                sol = self._gen(f"Fix error: {msg}\nCode:\n{sol}"); continue
            
            atk = self._gen(f"Role: QA. Target:\n{sol}\nTask: Write failing test. Output CODE ONLY.")
            win, log = self.test(sol, atk)
            
            if win: return f"## 🛡️ VERIFIED\n
http://googleusercontent.com/immersive_entry_chip/0

### STEP 5: VERIFY (Wait 60s)
Wait for the deployment to finish, then run:

```bash
python3 -c "import redis, json; r=redis.Redis(host='miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com', port=6379, decode_responses=True); r.rpush('miso:tasks', json.dumps({'id':'TASK-GLADIATOR-FINAL','type':'CHAT_COMMAND','payload':'CRITICAL: Write a Python function to calculate Fibonacci numbers.'})); print('⚔️ SENT')"
