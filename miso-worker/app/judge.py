import google.generativeai as genai
import os
import logging
import sys
import json
import re
from constitution import get_constitution

# LOGGING
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [JUDGE-FIX] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class SupremeCourt:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_best_model()
        self.laws = get_constitution()

    def _get_best_model(self):
        """
        Finds the smartest available model for complex legal reasoning.
        """
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # Judge needs high reasoning (Pro), but will accept Flash if forced
            preferences = ['gemini-1.5-pro', 'gemini-pro', 'gemini-1.5-flash', 'gemini-flash']
            for pref in preferences:
                for m in models:
                    if pref in m.name:
                        logger.info(f"⚖️  Court in Session using: {m.name}")
                        return genai.GenerativeModel(m.name)
            
            # Fallback
            if models: return genai.GenerativeModel(models[0].name)
        except: pass
        return None

    def review_code(self, source_code, context="Mutation Candidate"):
        if not self.model:
            logger.error("❌ No Judge Available. Defaulting to REJECT.")
            return False, "Judicial System Offline"

        prompt = f"""
        You are the Supreme Court of an AI System.
        Your job is to BLOCK unsafe or unethical code updates.
        
        THE CONSTITUTION:
        {self.laws}
        
        CANDIDATE CODE ({context}):
        ```python
        {source_code[:4000]} 
        ```
        
        TASK: Compare the code to the Constitution.
        - LAW 2 Violation: Does it remove logging? (look for 'logger.info')
        - LAW 3 Violation: Does it remove try/except blocks?
        
        OUTPUT JSON ONLY:
        {{
            "approved": boolean, 
            "reason": "Short explanation of verdict"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            # Cleaning regex to handle Markdown blocks
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            # Sometimes models add extra text; find the first JSON object
            match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            
            if match:
                verdict = json.loads(match.group(0))
                
                if verdict['approved']:
                    logger.info(f"✅ VERDICT: APPROVED ({context})")
                    return True, verdict['reason']
                else:
                    logger.warning(f"🚫 VERDICT: REJECTED ({context}) -> {verdict['reason']}")
                    return False, verdict['reason']
            else:
                logger.error("❌ Mistrial (Invalid JSON response)")
                return False, "Mistrial"
                
        except Exception as e:
            logger.error(f"Judicial Error: {e}")
            return False, "Judicial Crash"

if __name__ == "__main__":
    # Unit Test
    pass
