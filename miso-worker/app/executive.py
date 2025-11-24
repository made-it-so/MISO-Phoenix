import boto3
import json
import os
import logging
import google.generativeai as genai
import time
import subprocess
import sys
from cto import CTO # <--- NEW ADVISOR

REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMANDER_SCRIPT = os.path.join(BASE_DIR, "commander.py")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [EXECUTIVE-V31] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def issue_command(order):
    logger.info(f"👑 EXECUTIVE DECREE: '{order}'")
    try:
        subprocess.run(["python3", "-u", COMMANDER_SCRIPT, order], check=True)
    except: pass

if __name__ == "__main__":
    key = get_api_key()
    if not key: exit(1)
    
    logger.info("🏛️ MISO V31 EXECUTIVE ONLINE.")
    
    # 1. CONSULT THE CTO
    cto = CTO()
    logs = cto.read_telemetry()
    report = cto.analyze_patterns(logs)
    
    if report and report.get('status') == "CRITICAL":
        logger.warning(f"🚨 CTO ALERT: {report['observation']}")
        directive = report['directive']
        
        # Convert Technical Directive into Commander Order
        order = f"Create or update the system to: {directive}"
        issue_command(order)
    else:
        logger.info("✅ CTO reports system stability. Maintaining course.")
