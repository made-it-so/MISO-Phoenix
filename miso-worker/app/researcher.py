import google.generativeai as genai
import os
import logging
import json
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKER_FILE = os.path.join(BASE_DIR, "worker.py")

# FORCE STDOUT LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [RESEARCHER-FIX] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class Researcher:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_best_model()

    def _get_best_model(self):
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Researcher needs high reasoning (Pro)
            preferences = ['gemini-1.5-pro', 'gemini-pro', 'gemini-1.5-flash', 'gemini-flash']
            for pref in preferences:
                for m in models:
                    if pref in m.name:
                        logger.info(f"🧠 Researcher using: {m.name}")
                        return genai.GenerativeModel(m.name)
            if models: return genai.GenerativeModel(models[0].name)
        except: pass
        return None

    def read_codebase(self):
        try:
            with open(WORKER_FILE, 'r') as f: return f.read()
        except: return "Codebase unavailable."

    def analyze_paper(self, article_text):
        if not self.model:
            logger.error("❌ No Model Available.")
            return None

        code_context = self.read_codebase()
        
        prompt = f"""
        You are the R&D Lead for an AI Architecture Firm.
        
        SOURCE MATERIAL (New Research):
        {article_text}
        
        CURRENT IMPLEMENTATION (MISO Worker):
        ```python
        {code_context[:2000]} ...
        ```
        
        TASK: 
        1. Compare MISO's architecture to the Source Material.
        2. Identify a GAP or Opportunity.
        3. Propose a concrete code change (file to create or modify).
        
        OUTPUT JSON ONLY:
        {{
            "current_classification": "Modular Swarm",
            "gap_analysis": "MISO lacks [concept from paper].",
            "recommendation": "Create [filename] that implements [concept]."
        }}
        """
        
        try:
            logger.info("🧐 Analyzing Research Paper...")
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
            return None
        except Exception as e:
            logger.error(f"Research Failed: {e}")
            return None

if __name__ == "__main__":
    pass
