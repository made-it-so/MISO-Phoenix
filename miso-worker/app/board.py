import time
import os
import logging
import subprocess
import google.generativeai as genai
from ledger_real import CentralBank

# CONFIG
REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXECUTIVE_SCRIPT = os.path.join(BASE_DIR, "executive.py")

# FORCE LOGGING TO STDOUT
import sys
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [BOARD] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

bank = CentralBank(initial_funding=2.00) # We start with .00 of "Runway"

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def get_best_model():
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferences = ['gemini-1.5-pro', 'gemini-pro']
        for pref in preferences:
            for m in models:
                if pref in m.name: return genai.GenerativeModel(m.name)
        return genai.GenerativeModel(models[0].name)
    except: return None

def generate_strategic_directive(balance, spend, model):
    """
    The Boardroom Meeting. 
    Decides the strategy based on remaining runway.
    """
    burn_rate = "HIGH" if balance < 1.0 else "LOW"
    
    prompt = f"""
    You are the Board of Directors for an Autonomous AI Company.
    
    FINANCIAL REPORT:
    - Remaining Runway: ${balance:.4f}
    - Total Burn: ${spend:.4f}
    - Burn Rate Status: {burn_rate}
    
    YOUR GOAL: Keep the company alive and profitable.
    
    DECISION LOGIC:
    1. If Runway > .50: "EXPAND". Order the CEO to build new revenue-generating features.
    2. If Runway < .00: "CONSOLIDATE". Order the CEO to optimize code and reduce costs.
    3. If Runway < -bash.20: "EMERGENCY". Order the CEO to delete non-essential agents.
    
    OUTPUT: A specific, 1-sentence directive for the CEO (Executive Agent).
    Example: "Direct the Commander to create a marketing_bot.py to find new clients."
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Board Meeting Adjourned (Error): {e}")
        return "Maintain status quo."

def run_company():
    key = get_api_key()
    if not key: return
    genai.configure(api_key=key)
    model = get_best_model()
    
    logger.info("🏛️ BOARDROOM SESSION STARTED.")
    
    # COST OF DOING BUSINESS (Board Meeting costs money)
    if not bank.authorize_transaction("BOARD_MEETING", 0.05):
        logger.critical("💀 BANKRUPTCY DECLARED. SHUTTING DOWN CORPORATION.")
        os.system("pkill -f python3") # The Kill Switch
        sys.exit(1)

    balance, spend = bank.get_status()
    logger.info(f"💰 Balance: ${balance:.4f} | Burn: ${spend:.4f}")
    
    # 1. Generate Strategy
    directive = generate_strategic_directive(balance, spend, model)
    logger.info(f"📜 BOARD DIRECTIVE: \"{directive}\"")
    
    # 2. Pass Directive to Executive (CEO)
    # We modify executive.py slightly to accept args, or just pass via Env Var for this demo
    # For V25, we will simulate the CEO receiving this by injecting it into the environment
    os.environ["BOARD_DIRECTIVE"] = directive
    
    try:
        # Run the Executive for one cycle
        subprocess.run(["python3", "-u", EXECUTIVE_SCRIPT], check=True)
    except Exception as e:
        logger.error(f"CEO Failed: {e}")

if __name__ == "__main__":
    # Run continuously until money runs out
    while True:
        run_company()
        time.sleep(10) # Board meets every 10 seconds
