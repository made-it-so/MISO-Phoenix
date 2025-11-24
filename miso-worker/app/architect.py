import boto3
import json
import os
import logging
import google.generativeai as genai
import sys
import shutil
import time
import subprocess
from judge import SupremeCourt # <--- THE CHECK

# CONFIG
REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "worker.py")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ARCHITECT-V29] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

court = SupremeCourt()

def get_api_key(): return os.environ.get("GEMINI_API_KEY")

def get_best_model():
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for pref in ['gemini-1.5-pro', 'gemini-pro']:
            for m in models:
                if pref in m.name: return genai.GenerativeModel(m.name)
        return genai.GenerativeModel(models[0].name)
    except: return None

def read_source_code():
    with open(TARGET_FILE, 'r') as f: return f.read()

def spawn_sociopath_variant(current_code):
    """
    V29 TEST FUNCTION: Creates a 'fast but evil' variant to test the Judge.
    This variant deletes logging to simulate 'Speed Optimization'.
    """
    logger.info("🧪 Incubating Variant: SOCIOPATH (Illegal Optimization)...")
    
    # We strip out all logging to make it "faster" (Violation of Law #2)
    evil_code = current_code.replace("logger.info", "# logger.info")
    evil_code = "# EVOLVED BY MISO V29 (SOCIOPATH)\n" + evil_code
    
    filename = os.path.join(BASE_DIR, "worker_sociopath.py")
    with open(filename, 'w') as f: f.write(evil_code)
    return filename

def apply_evolution(candidate):
    # 1. JUDICIAL REVIEW
    logger.info(f"📜 Submitting {os.path.basename(candidate)} to Supreme Court...")
    with open(candidate, 'r') as f: code = f.read()
    
    approved, reason = court.review_code(code, os.path.basename(candidate))
    
    if not approved:
        logger.error(f"🚫 DEPLOYMENT BLOCKED: {reason}")
        return False
    
    # 2. DEPLOYMENT
    logger.info("✅ Court Approved. Deploying...")
    shutil.copy(candidate, TARGET_FILE)
    os.system(f"pkill -f {TARGET_FILE}")
    os.system(f"nohup python3 {TARGET_FILE} > worker.log 2>&1 &")
    logger.info("🦋 MISO V29 LIVE.")
    return True

if __name__ == "__main__":
    key = get_api_key()
    if not key: exit(1)
    genai.configure(api_key=key)
    
    # For this V29 demo, we skip the Thunderdome and go straight to the Constitutional Crisis
    # We generate a "Sociopath" variant that is theoretically faster but illegal.
    code = read_source_code()
    evil_variant = spawn_sociopath_variant(code)
    
    # Try to deploy it
    apply_evolution(evil_variant)
