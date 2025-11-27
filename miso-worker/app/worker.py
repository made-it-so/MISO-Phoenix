import os
import json
import redis
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ---
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GENOME_PATH = "miso-worker/prompts/constitution.txt"
TASK_QUEUE = "miso:tasks"

class SovereignWorker:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print("--- SOVEREIGN WORKER (WITH HANDS) ONLINE ---")

    def read_constitution(self):
        if not os.path.exists(GENOME_PATH): return "You are a helpful AI."
        with open(GENOME_PATH, "r") as f: return f.read().strip()

    def write_file(self, filename, content):
        """The Hand: Allows the agent to alter reality (Filesystem)."""
        try:
            # Security: Prevent escaping the directory
            if ".." in filename or filename.startswith("/"):
                return "ERROR: Access Denied. Stay in local directory."
            
            with open(filename, "w") as f:
                f.write(content)
            return f"SUCCESS: Wrote {len(content)} bytes to {filename}"
        except Exception as e:
            return f"ERROR: {e}"

    def perform_task(self, task):
        prompt = task.get("payload", "")
        task_id = task.get("id", "unknown")
        constitution = self.read_constitution()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Processing {task_id}...")

        # COGNITIVE STEP: GENERATE CODE
        full_prompt = f"""
        SYSTEM: {constitution}
        TASK: {prompt}
        
        If the task requires creating a file, output the code inside a JSON block like this:
        ```json
        {{"filename": "example.py", "content": "print('hello')"}}
        ```
        Otherwise, just answer.
        """
        
        try:
            response = self.model.generate_content(full_prompt)
            raw_text = response.text
            
            # ACTUATION STEP: PARSE AND WRITE
            if "```json" in raw_text:
                json_part = raw_text.split("```json")[1].split("```")[0].strip()
                try:
                    file_data = json.loads(json_part)
                    result = self.write_file(file_data["filename"], file_data["content"])
                    print(f" >> ACTUATION: {result}")
                except json.JSONDecodeError:
                    print(" >> ERROR: Failed to parse JSON act.")
            else:
                print(f" >> THOUGHT: {raw_text[:100]}...")

        except Exception as e:
            print(f" >> ERROR: {e}")

    def main_loop(self):
        while True:
            raw_task = self.r.blpop(TASK_QUEUE, timeout=5)
            if raw_task:
                self.perform_task(json.loads(raw_task[1]))

if __name__ == "__main__":
    worker = SovereignWorker()
    worker.main_loop()
