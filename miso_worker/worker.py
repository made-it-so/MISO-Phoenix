# This is the new, architecturally correct worker script
import os
import logging
import json
import re
import time
import boto3
import google.generativeai as genai
import subprocess
import sys
from git import Repo, Actor, GitCommandError

# --- Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] [%(levelname)s] [MISO_WORKER_V5_SECURE]: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# --- Environment Variables ---
# We will get the *actual values* of these from the Fargate Task Definition
GITHUB_PAT = os.environ.get('GITHUB_PAT')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SQS_QUEUE_URL = os.environ.get('MISO_SQS_QUEUE_URL') # This one is plain text

GITHUB_REPO_URL = "https://github.com/made-it-so/MISO-Phoenix.git"
REPO_NAME = "made-it-so/MISO-Phoenix"
MAX_FIX_ATTEMPTS = 3

# This is the directory where the Dockerfile pre-loaded the repo
REPO_DIR = "/src/miso-phoenix-repo"

# --- Clients & Secrets ---
try:
    sqs_client = boto3.client('sqs')
    
    # --- THIS IS THE FIX ---
    # The Fargate task definition will pass the *actual secret values*
    # into these environment variables. We just read them.
    # We no longer need to call Secrets Manager.
    
    if not GITHUB_PAT or not GEMINI_API_KEY or not SQS_QUEUE_URL:
        logging.critical("CRITICAL: GITHUB_PAT, GEMINI_API_KEY, or SQS_QUEUE_URL env vars are missing.")
        raise ValueError("Missing required secret environment variables.")

    genai.configure(api_key=GEMINI_API_KEY)
    
    # This is the only model we define here.
    # The "Persona Broker" (Critic) will decide which models to use.
    # We use Flash for the Broker itself, as it's fast and cheap.
    persona_broker_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    auth_repo_url = GITHUB_REPO_URL.replace("https://", f"https://oauth2:{GITHUB_PAT}@")
    logging.info("All clients and secrets configured.")
    
    # This is our test log message from Phase 1
    logging.info("GRADUATION TEST V1 PASSED.")

except Exception as e:
    logging.critical(f"Failed during initialization: {e}", exc_info=True)
    exit(1) # Exit immediately if config fails

# --- HANDLER 1: PYTEST_FIX ---

def run_persona_broker(error_log):
    """
    This is the new "Critic" or "Persona Broker".
    It analyzes the task and generates a full JSON "Persona" (plan).
    The worker will be a dumb executor of this plan.
    """
    logging.info("PersonaBroker: Running AI Critic to generate Persona...")
    try:
        prompt = f"""
        You are the MISO "Persona Broker" (Critic). Your job is to analyze a failed
        pytest log and generate a JSON "Persona" (a plan) to fix the bug.
        This plan achieves "Elastic Intelligence" by selecting the cheapest compute.

        RULES:
        1.  Analyze the error log.
        2.  "compute_tier": "T2" for simple, single-file bugs. "T3" for complex bugs.
        3.  "model_to_use": Use "gemini-1.5-flash-latest" for T2 bugs. Use "gemini-1.5-pro-latest" for T3 bugs.
        4.  "files_to_read": A list of all relevant application file paths.
        5.  "primary_fix_file": The one file that should be modified.
        6.  Return ONLY a JSON object.

        EXAMPLE T2 PERSONA:
        {{
            "compute_tier": "T2",
            "model_to_use": "gemini-1.5-flash-latest",
            "files_to_read": ["src/miso_app/utils.py"],
            "primary_fix_file": "src/miso_app/utils.py"
        }}

        EXAMPLE T3 PERSONA:
        {{
            "compute_tier": "T3",
            "model_to_use": "gemini-1.5-pro-latest",
            "files_to_read": ["src/miso_app/main.py", "src/miso_app/utils.py"],
            "primary_fix_file": "src/miso_app/main.py"
        }}

        FAILED PYTEST LOG:
        {error_log}
        """
        response = persona_broker_model.generate_content(prompt)
        cleaned_response = response.text.strip().strip("```json").strip("```")
        
        persona = json.loads(cleaned_response)
        logging.info(f"PersonaBroker: Persona generated: {persona}")
        
        if not persona.get("files_to_read") or not persona.get("primary_fix_file"):
            raise ValueError("AI Persona missing 'files_to_read' or 'primary_fix_file'.")

        return persona

    except Exception as e:
        logging.error(f"PersonaBroker: AI failed to generate Persona: {e}. Aborting.")
        return None

def run_pytest_validation():
    """
    Runs pytest using the pre-installed dependencies in the Docker image.
    This function NO LONGER runs 'pip install'. It is now fast and secure.
    """
    try:
        # We use the system executable, which is in the venv we built in the Dockerfile
        process = subprocess.run(
            [sys.executable, "-m", "pytest"],
            cwd=REPO_DIR, capture_output=True, text=True
        )
        if process.returncode == 0:
            return True, None
        else:
            return False, process.stdout + "\n" + process.stderr
    except Exception as e:
        logging.error(f"Pytest validation subprocess failed: {e}", exc_info=True)
        return False, str(e)

def create_pull_request(branch_name, commit_sha, file_to_fix):
    try:
        title = f"FIX(MISO-AI): Autonomous fix for {file_to_fix} [{commit_sha[:7]}]"
        body = f"MISO-AI autonomous fix. Validated by `pytest`. \n\nFailed Commit: {commit_sha}"
        env = os.environ.copy()
        env['GH_TOKEN'] = GITHUB_PAT
        
        # We must run 'gh' from within the repo directory
        subprocess.run(
            ['gh', 'pr', 'create', '--title', title, '--body', body, '--base', 'main', '--head', branch_name, '--repo', REPO_NAME],
            cwd=REPO_DIR, check=True, capture_output=True, text=True, env=env
        )
        logging.info(f"Successfully created Pull Request for {branch_name}.")
    except Exception as e:
        logging.error(f"Failed to create PR: {e}", exc_info=True)
        # We don't fail the whole task if the PR fails
        pass

def handle_pytest_fix(payload):
    logging.info("--- Handling Task: PYTEST_FIX ---")
    commit_sha = payload.get("commit_sha")
    original_error_log = payload.get("error_log")
    if not commit_sha or not original_error_log:
        logging.error("PytestFix: Invalid payload. Missing 'commit_sha' or 'error_log'.")
        return False

    # 1. CALL PERSONA BROKER (THE "CRITIC")
    # This is the new architecture. The worker asks the Critic for a plan.
    persona = run_persona_broker(original_error_log)
    if not persona:
        logging.error("PytestFix: Failed to get a valid Persona from the Broker. Aborting.")
        return False

    # 2. EXECUTE THE PERSONA (The "Dumb Worker")
    # The worker now just reads the plan (Persona) and executes it.
    try:
        primary_file_to_fix = persona["primary_fix_file"]
        files_to_read = persona["files_to_read"]
        model_to_use = persona["model_to_use"]
        
        # Instantiate the model the Persona told us to use
        active_model = genai.GenerativeModel(model_to_use)
        logging.info(f"PytestFix: Executing Persona. Compute: {persona['compute_tier']} ({model_to_use})")
        
        # We are using the repo pre-loaded at /src/miso-phoenix-repo
        # We no longer clone. We just fetch and checkout.
        repo = Repo(REPO_DIR)
        repo.remote(name='origin').fetch()
        repo.git.checkout(commit_sha, f=True) # Force checkout to the failed commit
        
        author = Actor("MISO-AI", "miso@autonomous-agent.ai")
        repo.config_writer().set_value("user", "name", author.name).release()
        repo.config_writer().set_value("user", "email", author.email).release()

        new_branch_name = f"miso-fix/{primary_file_to_fix.replace('/', '-')}-{commit_sha[:7]}"
        repo.create_head(new_branch_name).checkout()

        # Read context files
        context_prompt_files = []
        for file_path in files_to_read:
            full_file_path = os.path.join(REPO_DIR, file_path)
            if os.path.exists(full_file_path):
                with open(full_file_path, "r") as f:
                    file_content = f.read()
                context_prompt_files.append(f"--- FILE: {file_path} ---\n```python\n{file_content}\n```")
        
        full_context_prompt = "\n\n".join(context_prompt_files)
        primary_full_path = os.path.join(REPO_DIR, primary_file_to_fix)
        current_error_log = original_error_log

        # 3. VERIFICATION LOOP
        for attempt in range(MAX_FIX_ATTEMPTS):
            logging.info(f"PytestFix: Fix Attempt {attempt + 1}/{MAX_FIX_ATTEMPTS}...")

            prompt = f"""
            You are an autonomous AI engineer. A pytest run failed.
            Fix the primary file {primary_file_to_fix} using the provided context.

            CURRENT ERROR LOG:
            {current_error_log}

            RELEVANT FILES:
            {full_context_prompt}

            Provide ONLY the full, corrected Python code for {primary_file_to_fix}.
            """

            response = active_model.generate_content(prompt)
            fixed_code = response.text.strip().strip("```python").strip("```").strip()

            with open(primary_full_path, "w") as f:
                f.write(fixed_code)

            # THIS IS THE FIX: We no longer run 'pip install'.
            # We just run pytest, which is now fast and secure.
            tests_passed, new_error_log = run_pytest_validation()

            if tests_passed:
                logging.info(f"PytestFix: ATTEMPT {attempt + 1} SUCCESSFUL. Tests passed.")
                repo.git.add(update=True)
                repo.index.commit(f"FIX(MISO-AI): Autonomous fix for {primary_file_to_fix}", author=author)
                
                # We need to set the upstream URL with authentication
                repo.remote(name='origin').set_url(auth_repo_url)
                repo.remote(name='origin').push(new_branch_name)
                
                create_pull_request(new_branch_name, commit_sha, primary_file_to_fix)
                return True
            else:
                logging.warning(f"PytestFix: ATTEMPT {attempt + 1} FAILED.")
                current_error_log = new_error_log
                repo.git.checkout(primary_full_path) # Reset file

        logging.error(f"PytestFix: All {MAX_FIX_ATTEMPTS} attempts failed.")
        return False
        
    except GitCommandError as e:
        logging.error(f"PytestFix: Git operation failed: {e}", exc_info=True)
        return False
    except Exception as e:
        logging.error(f"PytestFix: Unhandled exception in fix cycle: {e}", exc_info=True)
        return False
    finally:
        # We no longer delete the repo, but we must check out main
        # to leave the container in a clean state for the next task.
        try:
            repo.git.checkout('main')
            repo.git.branch('-D', new_branch_name)
        except:
            pass # Don't fail if cleanup fails

# --- TASK ROUTER (MAIN LOOP) ---
def main():
    logging.info("MISO Task Router Service Started. Polling SQS...")
    while True:
        try:
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=20
            )
            if "Messages" not in response:
                continue

            message = response["Messages"][0]
            receipt_handle = message['ReceiptHandle']
            success = False # Default to failure

            try:
                message_body = json.loads(message['Body'])
                task_type = message_body.get("task_type")
                payload = message_body.get("payload")
                logging.info(f"Received task: {task_type}")

                # --- This is the Router ---
                if task_type == "PYTEST_FIX":
                    success = handle_pytest_fix(payload)
                else:
                    logging.error(f"Unknown task type: {task_type}. Message will be sent to DLQ.")
                    # We let it fail (success=False), so it goes to the DLQ
                    
            except Exception as e:
                logging.error(f"Critical error processing message: {e}. Message will be sent to DLQ.", exc_info=True)
                # Let it fail (success=False), so it goes to the DLQ
            
            # This is the new, safer logic:
            # We ONLY delete the message if the task was *successful*.
            # All failures (unknown task, processing error) will be ignored,
            # fail to be deleted, and be sent to the DLQ by SQS.
            if success:
                sqs_client.delete_message(
                    QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle
                )
                logging.info(f"Task {task_type} completed successfully. Message deleted.")
            else:
                logging.warning(f"Task {task_type} failed. Message will be returned to queue and sent to DLQ after retries.")

        except Exception as e:
            logging.error(f"Error in main SQS poll loop: {e}", exc_info=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
