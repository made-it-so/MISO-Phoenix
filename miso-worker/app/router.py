import google.generativeai as genai
import os
import logging
import json
import re
import sys

# LOGGING TO STDOUT
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PLANNER] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class NeuralRouter:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_best_model()

    def _get_best_model(self):
        # We use Flash for planning because it is fast and cheap
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferences = ['gemini-1.5-flash', 'gemini-flash', 'gemini-pro']
            for pref in preferences:
                for m in models:
                    if pref in m.name: return genai.GenerativeModel(m.name)
            return genai.GenerativeModel(models[0].name)
        except: return None

    def create_plan(self, task):
        """
        The Persona Broker Logic.
        Breaks 1 big task into N small subtasks with assigned models.
        """
        prompt = f"""
        You are a Project Manager AI.
        GOAL: Break this task into 3-5 logical steps.
        TASK: "{task[:1000]}"
        
        FOR EACH STEP:
        - Assign a "model": "gemini-1.5-flash" (if easy/formatting/boilerplate) OR "gemini-1.5-pro" (if complex reasoning/security).
        - Assign a "cloud": "GCP" (default) or "AZURE" (if backup needed).
        
        OUTPUT JSON ONLY (List of objects):
        [
            {{"step": 1, "instruction": "Define the struct", "model": "gemini-1.5-flash", "cloud": "GCP"}},
            {{"step": 2, "instruction": "Implement thread-safe logic", "model": "gemini-1.5-pro", "cloud": "AZURE"}}
        ]
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text
            match = re.search(r'\[.*\]', text, re.DOTALL)
            
            if match:
                plan = json.loads(match.group(0))
                logger.info(f"🧩 Decomposed Task into {len(plan)} steps.")
                return plan
            else:
                # Fallback: Treat as single step
                return [{"step": 1, "instruction": task, "model": "gemini-1.5-pro", "cloud": "GCP"}]
                
        except Exception as e:
            logger.error(f"Planning Failed: {e}")
            return [{"step": 1, "instruction": task, "model": "gemini-1.5-pro", "cloud": "GCP"}]

if __name__ == "__main__":
    r = NeuralRouter()
    plan = r.create_plan("Write a secure banking ledger in Rust")
    print(json.dumps(plan, indent=2))
