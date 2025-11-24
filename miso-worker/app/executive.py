import boto3
import json
import os
import logging
import google.generativeai as genai
import time
import subprocess
import sys
from cfo import CFO
from scout import Scout
from researcher import Researcher

REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDER_SCRIPT = os.path.join(BASE_DIR, "commander.py")
FEED_FILE = os.path.join(BASE_DIR, "knowledge_feed.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EXECUTIVE-V37] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def get_best_model():
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['gemini-1.5-pro', 'gemini-pro']:
            for m in models:
                if pref in m.name: return genai.GenerativeModel(m.name)
        return genai.GenerativeModel(models[0].name)
    except: return None

def issue_command(order):
    logger.info(f"👑 EXECUTIVE DECREE: '{order}'")
    subprocess.run(["python3", "-u", COMMANDER_SCRIPT, order])

if __name__ == "__main__":
    key = get_api_key()
    if not key: exit(1)
    genai.configure(api_key=key)
    model = get_best_model()
    
    logger.info("🏛️ MISO V37 EXECUTIVE ONLINE.")
    
    # 1. SCOUTING PHASE
    scout = Scout()
    discovery = scout.patrol_internet()
    
    if discovery:
        logger.info("⚡ NEW KNOWLEDGE DETECTED. Triggering Research Lab...")
        
        # 2. RESEARCH PHASE
        # We pass the discovery to the Researcher Agent
        researcher = Researcher()
        # Note: In V32 researcher.py, we used 'analyze_paper'. Let's assume it works.
        # We pass the 'summary' as the text to analyze.
        analysis = researcher.analyze_paper(discovery['summary'])
        
        if analysis:
            logger.info(f"📄 Research Report: {json.dumps(analysis)}")
            
            # 3. DECISION PHASE
            # Executive decides if the upgrade is worth it
            prompt = f"""
            You are the CEO.
            R&D PROPOSAL: "{analysis['recommendation']}"
            GAP: "{analysis['gap_analysis']}"
            
            Should we implement this? (Assume we have budget).
            If YES, write a command for the Commander to build it.
            If NO, write "SLEEP".
            
            OUTPUT ONLY THE COMMAND.
            """
            response = model.generate_content(prompt)
            order = response.text.strip()
            
            if "SLEEP" not in order:
                issue_command(order)
            else:
                logger.info("💤 Research rejected.")
    else:
        logger.info("💤 No new research. Monitoring operations...")
