import google.generativeai as genai
import os
import logging
import sys
import re
import json

# PATH CORRECTION: Go up two levels to Project Root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
LOG_FILE = os.path.join(PROJECT_ROOT, "worker.log")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CTO-V31.1] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class CTO:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_best_model()

    def _get_best_model(self):
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferences = ['gemini-1.5-pro', 'gemini-pro', 'gemini-1.5-flash', 'gemini-flash']
            for pref in preferences:
                for m in models:
                    if pref in m.name:
                        logger.info(f"🧠 CTO using: {m.name}")
                        return genai.GenerativeModel(m.name)
            if models: return genai.GenerativeModel(models[0].name)
        except: pass
        return None

    def read_telemetry(self):
        try:
            logger.info(f"🔍 Scanning Log File: {LOG_FILE}")
            if not os.path.exists(LOG_FILE): 
                logger.error("❌ Log file not found at expected path.")
                return "No logs found."
            
            with open(LOG_FILE, 'r') as f:
                # Read last 1000 lines to ensure we catch the injection
                lines = f.readlines()
                return "".join(lines[-1000:])
        except Exception as e: 
            logger.error(f"Read Error: {e}")
            return "Log access failed."

    def analyze_patterns(self, logs):
        # We explicitly point out the error pattern to the LLM
        prompt = f"""
        You are the CTO.
        INPUT: SYSTEM LOGS
        ```text
        {logs} 
        ```
        
        TASK: Scan for "Payment Gateway Timeout".
        If found, report CRITICAL status and suggest a "Circuit Breaker".
        
        OUTPUT JSON ONLY:
        {{
            "status": "CRITICAL" or "STABLE",
            "observation": "Found X errors...",
            "directive": "Implement Circuit Breaker"
        }}
        """
        try:
            logger.info("🧠 Analyzing Telemetry...")
            response = self.model.generate_content(prompt)
            text = response.text.replace('```json', '').replace('```', '').strip()
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match: return json.loads(match.group(0))
            return None
        except Exception as e:
            logger.error(f"Analysis Error: {e}")
            return None

if __name__ == "__main__":
    pass
