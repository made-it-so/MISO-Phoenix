import boto3
import time
import os
import logging
import google.generativeai as genai
import sys
from notifier import Notifier

# CONFIG
TOPIC = "NVIDIA Stock & AI Market Sentiment"
CHECK_INTERVAL = 60 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SENTINEL] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def get_best_model():
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # TARGET: Use the aliases found in your account
        targets = ['gemini-flash-latest', 'gemini-pro-latest', 'gemini-2.0-flash', 'gemini-1.5-flash']
        
        for t in targets:
            for m in models:
                if t in m.name:
                    logger.info(f"🧠 Sentinel using: {m.name}")
                    return genai.GenerativeModel(m.name)
        
        # Fallback
        logger.warning(f"⚠️ Preferred models missing. Using: {models[0].name}")
        return genai.GenerativeModel(models[0].name)
    except Exception as e:
        logger.error(f"Model Init Failed: {e}")
        return None

def scan_horizon(model):
    if not model: return "Model Offline."
    prompt = f"""
    You are a Market Analyst.
    TASK: Simulate a real-time news feed for: '{TOPIC}'.
    
    Generate 3 realistic, high-impact headlines that *could* happen today.
    Make one of them slightly concerning/negative to test the alert system.
    
    OUTPUT: Just the headlines.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except: return "Feed Offline."

def evaluate_threat(headlines, model):
    if not model: return "OK"
    prompt = f"""
    HEADLINES:
    {headlines}
    
    TASK: Analyze sentiment for '{TOPIC}'.
    - If normal/boring: Output "OK".
    - If critical/market-moving/negative: Output "ALERT: <Short Reason>".
    
    Your goal is to filter noise. Only alert on signal.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except: return "OK"

if __name__ == "__main__":
    key = get_api_key()
    if not key: exit(1)
    genai.configure(api_key=key)
    
    model = get_best_model()
    notifier = Notifier()
    
    if not model:
        logger.critical("💀 FATAL: Could not initialize Brain.")
        exit(1)
    
    logger.info(f"🦅 SENTINEL ONLINE. TARGET: {TOPIC}")
    notifier.send_alert(f"Watchdog restarted (V40 Evergreen). Monitoring {TOPIC}.")
    
    while True:
        logger.info("🔭 Scanning horizon...")
        headlines = scan_horizon(model)
        logger.info(f"   Latest Headlines:\n{headlines}")
        
        analysis = evaluate_threat(headlines, model)
        
        if "ALERT" in analysis:
            notifier.send_alert(f"{analysis}\n\nContext:\n{headlines}")
        else:
            logger.info("✅ No threats detected.")
            
        logger.info(f"💤 Sleeping for {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)
