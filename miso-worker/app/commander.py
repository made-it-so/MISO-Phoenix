import boto3
import json
import os
import logging
import google.generativeai as genai
import sys
import subprocess
import time

REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FORCE LOGGING TO STDOUT
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [COMMANDER] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

def get_api_key():
    return os.environ.get("GEMINI_API_KEY")

def get_best_model():
    try:
        models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not models: return None
        preferences = ['gemini-1.5-pro', 'gemini-pro']
        for pref in preferences:
            for m in models:
                if pref in m.name: return genai.GenerativeModel(m.name)
        return genai.GenerativeModel(models[0].name)
    except: return None

def propose_plan(instruction, model):
    prompt = f"""
    You are MISO V19 (Shell Agent).
    USER INSTRUCTION: "{instruction}"
    CURRENT DIR: {BASE_DIR}
    TASK: Generate a BASH SCRIPT.
    RULES:
    1. Use 'cat <<EOF' to create files.
    2. Use 'nohup python3 ... > /dev/null 2>&1 &' for background processes.
    3. Output ONLY raw bash code. NO markdown backticks. NO 'bash' label at start.
    """
    try:
        logger.info("🧠 Drafting Plan...")
        response = model.generate_content(prompt)
        # Aggressive Cleanup
        return response.text.replace("```bash", "").replace("```", "").strip()
    except: return None

def critique_plan(instruction, script, model):
    prompt = f"""
    ROLE: Auditor.
    SCRIPT:
    {script}
    TASK: Check for safety. If safe, output "VERDICT: APPROVED". If not, output "VERDICT: REJECTED" and the fixed script.
    """
    try:
        logger.info("🤔 Auditing Plan...")
        response = model.generate_content(prompt)
        if "VERDICT: APPROVED" in response.text:
            return script
        else:
            logger.warning("⚠️ Plan Refined.")
            if "```" in response.text:
                return response.text.split("```")[1].replace("bash", "").strip()
            return script
    except: return script

def execute_plan(script):
    logger.info("⚡ EXECUTING...")
    # Clean up any leading "bash" word artifacts
    if script.startswith("bash"): script = script[4:].strip()
    
    print(f"\n----- SCRIPT -----\n{script}\n------------------\n")
    try:
        with open("temp_exec.sh", "w") as f: f.write(script)
        
        # FIX: Explicitly call /bin/bash instead of relying on shebang
        result = subprocess.run(["/bin/bash", "temp_exec.sh"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ EXECUTION SUCCESS")
            print(result.stdout)
        else:
            logger.error(f"❌ EXECUTION FAILED: {result.stderr}")
        os.remove("temp_exec.sh")
    except Exception as e:
        logger.error(f"Runtime: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2: exit(1)
    instruction = " ".join(sys.argv[1:])
    key = get_api_key()
    if not key: exit(1)
    
    genai.configure(api_key=key)
    model = get_best_model()
    if model:
        draft = propose_plan(instruction, model)
        if draft:
            final = critique_plan(instruction, draft, model)
            execute_plan(final)
