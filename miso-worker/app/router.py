import google.generativeai as genai
import os
import logging
import json
import re
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ROUTER-FIX] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class NeuralRouter:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = None # <--- FIX: Initialize default value
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = self._get_best_model()
            except Exception as e:
                logger.error(f"Router Init Failed: {e}")

    def _get_best_model(self):
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferences = ['gemini-1.5-flash', 'gemini-flash', 'gemini-pro']
            for pref in preferences:
                for m in models:
                    if pref in m.name: return genai.GenerativeModel(m.name)
            return genai.GenerativeModel(models[0].name)
        except: return None

    def create_plan(self, task):
        if not self.model:
            logger.error("❌ Router is Brain Dead (No Model). Defaulting to Single Step.")
            return [{"step": 1, "instruction": task, "tool": "LLM-PRO", "model": "gemini-1.5-pro"}]

        prompt = f"""
        You are a Systems Architect.
        Break this task into steps.
        
        TASK: "{task[:1000]}"
        
        FOR EACH STEP ASSIGN A TOOL:
        - "INTERPRETER": Math, counting, logic.
        - "LLM-FLASH": Simple text.
        - "LLM-PRO": Complex reasoning.
        
        OUTPUT JSON:
        [
            {{"step": 1, "instruction": "Calculate...", "tool": "INTERPRETER"}},
            {{"step": 2, "instruction": "Explain...", "tool": "LLM-PRO"}}
        ]
        """
        try:
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            match = re.search(r'\[.*\]', text, re.DOTALL)
            if match: return json.loads(match.group(0))
            return [{"step": 1, "instruction": task, "tool": "LLM-PRO"}]
        except Exception as e:
            logger.error(f"Planning Error: {e}")
            return [{"step": 1, "instruction": task, "tool": "LLM-PRO"}]
