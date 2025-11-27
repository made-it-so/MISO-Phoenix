import os
import json
import redis
import subprocess
import google.generativeai as genai
from datetime import datetime
from memory import Hippocampus

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENOME_PATH = "miso-worker/prompts/constitution.txt"
TASK_QUEUE = "miso:tasks"

class SovereignArchitect:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        if not GEMINI_API_KEY:
            print("CRITICAL: No API Key found.")
            return
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = self.find_best_model()
        self.hippocampus = Hippocampus()
        print("--- SOVEREIGN ARCHITECT (V47 SECURE) ONLINE ---")

    def find_best_model(self):
        try:
            available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = next((m for m in available if "gemini-1.5-flash" in m), 
                     next((m for m in available if "gemini-pro" in m), available[0] if available else None))
            return genai.GenerativeModel(target) if target else None
        except: return None

    def read_constitution(self):
        if not os.path.exists(GENOME_PATH): return "You are a helpful AI."
        with open(GENOME_PATH, "r") as f: return f.read().strip()

    def write_file(self, filename, content):
        if ".." in filename or filename.startswith("/"): return "ERROR: Access Denied."
        with open(filename, "w") as f: f.write(content)
        return f"SUCCESS: Wrote {len(content)} bytes to {filename}"

    def execute_shell(self, command):
        if "docker" in command: return 1, "ERROR: Recursion limit."
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
            output = f"EXIT: {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            return result.returncode, output
        except Exception as e:
            return 1, f"ERROR: {e}"

    def perform_task(self, task):
        if not self.model: return
        prompt = task.get("payload", "")
        task_id = task.get("id", "unknown")
        constitution = self.read_constitution()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Architecting {task_id}...")

        past = self.hippocampus.recall(prompt)
        context = f"RELEVANT PAST:\n{past}\n" if past else "NO PRECEDENT."

        full_prompt = f"""
        SYSTEM: {constitution}
        CONTEXT: {context}
        TASK: {prompt}
        
        SAFETY PROTOCOL:
        - If writing a script that modifies AWS/Infrastructure, ensure it prints changes first (Dry Run).
        
        TOOLS:
        1. Write File -> JSON: {{"tool": "write", "filename": "x.py", "content": "..."}}
        2. Run Shell -> JSON: {{"tool": "shell", "command": "ls -la"}}
        Output ONLY JSON.
        """
        
        try:
            response = self.model.generate_content(full_prompt)
            text = response.text
            if "```json" in text:
                json_part = text.split("```json")[1].split("```")[0].strip()
                data = json.loads(json_part)
                
                if data.get("tool") == "write":
                    res = self.write_file(data["filename"], data["content"])
                    print(f" >> WRITE: {res}")
                    # Tentatively memorize writes
                    self.hippocampus.remember(prompt, data["content"])
                    
                elif data.get("tool") == "shell":
                    exit_code, output = self.execute_shell(data["command"])
                    print(f" >> SHELL OUTPUT:\n{output}")
                    
                    # THE V47 SUCCESS FILTER
                    if exit_code == 0:
                        self.hippocampus.remember(prompt, f"COMMAND: {data['command']}\nRESULT: SUCCESS")
                        print(" >> CONSOLIDATION: Verified Success. Memory Encoded.")
                    else:
                        print(" >> CONSOLIDATION ABORTED: Execution Failed.")
                    
        except Exception as e:
            print(f" >> ERROR: {e}")

    def main_loop(self):
        while True:
            raw_task = self.r.blpop(TASK_QUEUE, timeout=5)
            if raw_task: self.perform_task(json.loads(raw_task[1]))

if __name__ == "__main__":
    SovereignArchitect().main_loop()
