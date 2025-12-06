import json
import os
import logging
import google.generativeai as genai
import time
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, "continuum_memory.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [CONTINUUM] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class ContinuumMemory:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = None
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = self._get_best_model()
        
        self.load_memory()
        self.chunk_sizes = {"FAST": 5, "MID": 3, "SLOW": 3} # Lowered for faster demo

    def _get_best_model(self):
        try:
            models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            preferences = ['gemini-1.5-flash', 'gemini-flash', 'gemini-1.5-pro', 'gemini-pro']
            for pref in preferences:
                for m in models:
                    if pref in m.name:
                        logger.info(f"🧠 Continuum using: {m.name}")
                        return genai.GenerativeModel(m.name)
            if models: return genai.GenerativeModel(models[0].name)
        except: pass
        return None

    def load_memory(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r') as f: self.data = json.load(f)
            except: self.data = {"FAST": [], "MID": [], "SLOW": []}
        else:
            self.data = {"FAST": [], "MID": [], "SLOW": []}

    def save_memory(self):
        with open(MEMORY_FILE, 'w') as f: json.dump(self.data, f, indent=2)

    def compress_information(self, source_data, target_level):
        if not self.model: return "Model Offline"
        
        prompt = f"""
        Compress these logs into a single strategic insight for {target_level} memory.
        LOGS: {json.dumps(source_data)}
        OUTPUT: One sentence summary.
        """
        try:
            resp = self.model.generate_content(prompt)
            return resp.text.strip()
        except Exception as e:
            logger.error(f"Compression Error: {e}")
            return "Compression Failed"

    def ingest_event(self, event):
        self.data["FAST"].append(event)
        
        # Fast -> Mid
        if len(self.data["FAST"]) >= self.chunk_sizes["FAST"]:
            chunk = self.data["FAST"][:]
            self.data["FAST"] = []
            insight = self.compress_information(chunk, "MID")
            self.data["MID"].append(insight)
            logger.info(f"🧠 Consolidated (MID): {insight}")
            self.save_memory()
            
            # Mid -> Slow
            if len(self.data["MID"]) >= self.chunk_sizes["MID"]:
                chunk = self.data["MID"][:]
                self.data["MID"] = []
                strategy = self.compress_information(chunk, "SLOW")
                self.data["SLOW"].append(strategy)
                logger.info(f"🏛️  Wisdom (SLOW): {strategy}")
                self.save_memory()

    def get_context(self):
        return {
            "tactics": self.data["MID"][-3:],
            "strategy": self.data["SLOW"][-1:]
        }

if __name__ == "__main__":
    cm = ContinuumMemory()
    logger.info("⏳ Simulating High-Speed Events...")
    for i in range(20):
        cm.ingest_event({"id": i, "metric": "latency", "value": 100 + i})
        time.sleep(0.1)
