import google.generativeai as genai
import os
import logging
import json
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# We need access to the codebase to compare "Theory" vs "Reality"
WORKER_FILE = os.path.join(BASE_DIR, "worker.py")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [RESEARCHER] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class Researcher:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')

    def read_codebase(self):
        try:
            with open(WORKER_FILE, 'r') as f: return f.read()
        except: return "Codebase unavailable."

    def analyze_paper(self, article_text):
        code_context = self.read_codebase()
        
        prompt = f"""
        You are the R&D Lead for an AI Architecture Firm.
        
        SOURCE MATERIAL (The Research):
        {article_text}
        
        CURRENT IMPLEMENTATION (MISO):
        ```python
        {code_context[:2000]} ...
        ```
        
        TASK: 
        1. Classify MISO's current architecture based on the 5 types in the text (Hierarchical, Swarm, Meta-Learning, Modular, Evolutionary).
        2. Identify a GAP. What does the article suggest that MISO is missing?
        3. Propose a concrete upgrade.
        
        OUTPUT JSON ONLY:
        {{
            "current_classification": "Self Organizing Modular",
            "gap_analysis": "MISO lacks true Population-based Evolutionary Curriculum.",
            "recommendation": "Implement a Curriculum Engine to scale task difficulty dynamically."
        }}
        """
        
        try:
            logger.info("🧐 Analyzing Research Paper...")
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            logger.error(f"Research Failed: {e}")
            return None

if __name__ == "__main__":
    # Test Mode
    pass
