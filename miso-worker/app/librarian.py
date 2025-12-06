import json
import os
import logging
import google.generativeai as genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [LIBRARIAN] %(message)s')
logger = logging.getLogger(__name__)

class Librarian:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_model()
        self.load_memory()

    def _get_model(self):
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            for pref in ['gemini-1.5-pro', 'gemini-pro']:
                for m in models:
                    if pref in m.name: return genai.GenerativeModel(m.name)
            return genai.GenerativeModel(models[0].name)
        except: return None

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f: self.memories = json.load(f)
        else: self.memories = []

    def save_memory(self):
        with open(MEMORY_FILE, 'w') as f: json.dump(self.memories, f, indent=2)

    def archive_case_study(self, agent, outcome, details):
        self.memories.append({"topic": agent, "outcome": outcome, "details": details})
        self.save_memory()

    def consult_archives(self, plan):
        if not self.memories: return "[ALLOW] No history."
        
        failures = [m for m in self.memories if m['outcome'] == "FAILURE"]
        context = json.dumps(failures[-10:])

        prompt = f"""
        You are the Risk Officer.
        PLAN: "{plan}"
        PAST FAILURES: {context}
        
        TASK: Compare the PLAN to the PAST FAILURES.
        - If the plan repeats a specific logic that failed before, output "[BLOCK]".
        - If the plan is different or safer, output "[ALLOW]".
        
        OUTPUT ONLY THE TAG FOLLOWED BY A REASON.
        Example: "[BLOCK] This attempts crypto mining, which failed previously."
        Example: "[ALLOW] This is a new optimization strategy."
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except: return "[ALLOW] Archive offline."

if __name__ == "__main__":
    pass
