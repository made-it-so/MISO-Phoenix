import os
import logging
import json
import tempfile
import shutil
import re
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import boto3
import google.generativeai as genai
import ollama
from git import Repo, Actor

# --- Configuration & Logging ---
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [MISO_APP]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Environment Variable Secrets ---
EXPECTED_SECRET = os.environ.get('MISO_WEBHOOK_SECRET')
GEMINI_API_KEY = os.environ.get('GOOGLE_API_KEY')
GITHUB_PAT = os.environ.get('MISO_GITHUB_PAT')
GITHUB_REPO_URL = "https://github.com/made-it-so/MISO-Phoenix.git"

# --- Configure Gemini API ---
try:
    if not GEMINI_API_KEY:
        logging.critical("GEMINI_API_KEY env var not set.")
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-pro-latest')
    logging.info("Gemini AI model configured.")
except Exception as e:
    logging.critical(f"Failed to configure Gemini: {e}")

if not EXPECTED_SECRET:
    logging.critical("MISO_WEBHOOK_SECRET env var not set.")
if not GITHUB_PAT:
    logging.critical("MISO_GITHUB_PAT env var not set.")

app = Flask(__name__)

# --- BACKGROUND TASK LOGIC ---
def run_ai_fix_cycle(commit_sha, branch_name, error_log, file_to_fix):
    logging.info(f"BACKGROUND_JOB: Starting fix for {commit_sha} on branch {branch_name}")
    auth_repo_url = GITHUB_REPO_URL.replace("https://", f"https://oauth2:{GITHUB_PAT}@")
    repo_dir = tempfile.mkdtemp(prefix="miso-")
    
    try:
        logging.info(f"BACKGROUND_JOB: Cloning {GITHUB_REPO_URL} into {repo_dir}...")
        repo = Repo.clone_from(auth_repo_url, repo_dir, branch='main')
        author = Actor("MISO-AI", "miso@autonomous-agent.ai")
        repo.config_writer().set_value("user", "name", author.name).release()
        repo.config_writer().set_value("user", "email", author.email).release()
        
        full_file_path = os.path.join(repo_dir, file_to_fix)
        if not os.path.exists(full_file_path):
            logging.error(f"BACKGROUND_JOB: File not found in repo: {full_file_path}")
            return
            
        with open(full_file_path, "r") as f:
            original_code = f.read()

        logging.info(f"BACKGROUND_JOB: Sending error and file content to Gemini...")
        prompt = f"""
        You are an autonomous AI software engineer (MISO). A pytest run has failed.
        You must fix the provided Python file to resolve the error.

        THE ERROR LOG:
        {error_log}

        THE BROKEN FILE: {file_to_fix}
        ```python
        {original_code}
        ```

        You must provide *only* the full, corrected Python code for the file {file_to_fix}.
        Do not add any explanation, markdown, or chat. Your output will be piped directly
        to a file and committed.
        """
        
        response = gemini_model.generate_content(prompt)
        fixed_code = response.text
        logging.info("BACKGROUND_JOB: Gemini has provided a fix.")

        new_branch = repo.create_head(branch_name)
        new_branch.checkout()

        with open(full_file_path, "w") as f:
            cleaned_code = fixed_code.strip().strip("```python").strip("```")
            f.write(cleaned_code)

        repo.git.add(update=True)
        repo.git.add(full_file_path)
        commit_message = f"FIX(MISO-AI): Autonomous fix for {file_to_fix} [{commit_sha[:7]}]"
        repo.index.commit(commit_message, author=author)
        
        origin = repo.remote(name='origin')
        origin.push(new_branch.name)
        
        logging.info(f"BACKGROUND_JOB: Successfully pushed fix to branch: {branch_name}")

    except Exception as e:
        logging.error(f"BACKGROUND_JOB: Git/AI operation failed: {e}", exc_info=True)
    finally:
        if os.path.exists(repo_dir):
            shutil.rmtree(repo_dir)
            logging.info(f"BACKGROUND_JOB: Cleaned up temp directory {repo_dir}")

# --- Fixed Triage Regex ---
def triage_error_log(error_log):
    logging.info("Triage: Parsing error log...")
    
    traceback_pattern = re.compile(r'File ".*?/MISO-Phoenix/(.*?)"', re.IGNORECASE)
    match = traceback_pattern.search(error_log)
    
    if match:
        relative_path = match.group(1)
        logging.info(f"Triage: Found file in traceback: {relative_path}")
        return relative_path
        
    summary_pattern = re.compile(r'ERROR ([\w/]+\.py)')
    match = summary_pattern.search(error_log)
    if match:
        file_path = match.group(1)
        logging.info(f"Triage: Found file in summary: {file_path}")
        return file_path

    logging.warning("Triage: Could not determine file to fix from error log.")
    return None

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

def check_auth():
    auth_header = request.headers.get('Authorization')
    if not auth_header or auth_header != f'Bearer {EXPECTED_SECRET}':
        logging.warning("AUTH FAILED. Invalid or missing token.")
        return False
    logging.info("**AUTH SUCCESSFUL.**")
    return True

@app.route('/miso/trigger', methods=['POST'])
def handle_ci_webhook():
    logging.info("Endpoint /miso/trigger HIT.")
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload_data = request.data.decode('utf-8')
        logging.info(f"Received payload: {payload_data[:500]}...")
        payload = json.loads(payload_data)
        
        commit_sha = payload.get("commit_sha")
        error_log = payload.get("error_log")
        
        if not error_log:
            logging.error("No error_log found in payload.")
            return jsonify({"error": "Missing error_log"}), 400

        file_to_fix = triage_error_log(error_log)
        if not file_to_fix:
            logging.error("Triage failed to find a file to fix.")
            return jsonify({"error": "Triage failed"}), 400
        
        fix_branch_name = f"miso-fix/{file_to_fix.replace('/', '-')}-{commit_sha[:7]}"
        
        logging.info(f"Scheduling background job for {fix_branch_name}...")
        scheduler.add_job(
            func=run_ai_fix_cycle,
            args=[commit_sha, fix_branch_name, error_log, file_to_fix],
            id=f"job-{commit_sha}",
            trigger='date'
        )
        
        logging.info("Job scheduled. Sending 200 OK immediately.")
        
        return jsonify({"status": "received", "action": "fix_job_scheduled", "branch": fix_branch_name}), 200

    except Exception as e:
        logging.error(f"FATAL ERROR in /miso/trigger: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@app.route('/miso/swarm_trigger', methods=['POST'])
def handle_swarm_webhook():
    logging.info("Endpoint /miso/swarm_trigger HIT.")
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"status": "received", "action": "swarm_task_initiated"}), 200

if __name__ != '__main__':
    scheduler = BackgroundScheduler()
    scheduler.start()
    logging.info("BackgroundScheduler started.")
