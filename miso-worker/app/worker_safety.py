# EVOLVED BY MISO V28 (SAFETY)
import boto3
import json
import time
import logging
import redis
import random
import os
import sys
import google.generativeai as genai  # <--- REQUIRED FOR EXECUTION
from vendors import get_vendor_adapter
from pricing import MarketOracle
from tenant_manager import Landlord
from router import NeuralRouter

# --- CONFIGURATION ---
try:
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    QUEUE_URL = os.environ.get("QUEUE_URL", "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue")
    DYNAMO_TABLE = os.environ.get("DYNAMO_TABLE", "miso_replay_buffer")
    REDIS_HOST = os.environ.get("REDIS_HOST", "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com")
except Exception as e:
    logging.critical(f"FATAL: Could not read environment variables for configuration. Error: {e}")
    sys.exit(1)

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WORKER-V28 (SAFETY)] %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- SERVICE INITIALIZATION ---
# Each service initialization is critical. If any fail, the worker cannot function.
try:
    sqs = boto3.client('sqs', region_name=AWS_REGION)
    dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
    secrets = boto3.client('secretsmanager', region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMO_TABLE)
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize core AWS services. Check credentials and region. Error: {e}")
    sys.exit(1)

try:
    market = MarketOracle()
    landlord = Landlord()
    router = NeuralRouter()
except Exception as e:
    logger.critical(f"FATAL: Failed to initialize custom service classes (Oracle, Landlord, Router). Error: {e}")
    sys.exit(1)

def get_key(arn):
    """Safely retrieves and parses a secret from AWS Secrets Manager."""
    try:
        secret_value = secrets.get_secret_value(SecretId=arn)
        return json.loads(secret_value['SecretString'])
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from secret ARN {arn}. Error: {e}")
        return None
    except Exception as e: # Catches Boto3 ClientError, etc.
        logger.error(f"Failed to retrieve or parse secret ARN {arn}. Error: {e}")
        return None

def execute_step(instruction, model_name, context=""):
    """
    Executes a single step of a plan, isolated to prevent crashes.
    Returns the result or a descriptive error message.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set.")
            return "Error: Server-side configuration issue. API key is missing."

        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(model_name)
        
        prompt = f"""
        PREVIOUS CONTEXT: {context}
        
        CURRENT TASK: {instruction}
        
        OUTPUT: Perform the task.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error during model execution '{model_name}'. Instruction: '{instruction[:50]}...'. Error: {e}")
        return f"Error executing step with model {model_name}: {e}"

def process(body):
    """
    Processes a single job message with granular error handling at each stage.
    """
    # 1. PARSE MESSAGE
    try:
        p = json.loads(body)
        api_key = p.get("api_key")
        task_desc = p.get("description", "Generic Task")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from message body. Body: '{body}'. Error: {e}")
        return # Unrecoverable for this message.

    # 2. AUTHENTICATE
    try:
        tenant = landlord.authenticate(api_key)
        if not tenant:
            logger.warning(f"Authentication failed for provided API key.")
            return # Unrecoverable for this message.
    except Exception as e:
        logger.error(f"An exception occurred during authentication. Error: {e}")
        raise # Raise to signal a retryable, systemic failure.

    # 3. CREATE PLAN
    try:
        plan = router.create_plan(task_desc)
        if not plan or not isinstance(plan, list):
             logger.error(f"NeuralRouter returned an invalid or empty plan for task: {task_desc}")
             return # Unrecoverable for this message.
    except Exception as e:
        logger.error(f"Failed to create a plan with NeuralRouter for task: '{task_desc}'. Error: {e}")
        raise # Raise to signal a retryable, systemic failure.

    logger.info(f"🏗️ Executing {len(plan)}-Step Workflow for {tenant.get('name', 'Unknown Tenant')}...")
    total_cost = 0
    accumulated_context = ""

    # 4. EXECUTE SWARM
    for step in plan:
        try:
            step_id = step['step']
            instruction = step['instruction']
            brain = step['model']
            
            logger.info(f"   👉 Step {step_id} ({brain}): {instruction[:40]}...")
            
            start = time.perf_counter()
            result = execute_step(instruction, brain, accumulated_context)
            dur = time.perf_counter() - start
            
            if result.strip().startswith("Error:"):
                logger.warning(f"Step {step_id} resulted in a managed error: {result}")
            
            accumulated_context += f"\n--- STEP {step_id} RESULT ---\n{result}\n"
            
            step_cost = 10 * (dur * 1000)
            if "pro" in brain: step_cost *= 10
            total_cost += step_cost

        except KeyError as e:
            logger.error(f"Malformed step in plan. Missing key: {e}. Step: {step}. Skipping.")
            accumulated_context += f"\n--- STEP FAILED (MALFORMED) ---\nMissing key: {e}\n"
            continue
        except Exception as e:
            logger.error(f"Unexpected error during step execution. Step: {step}. Error: {e}")
            accumulated_context += f"\n--- STEP FAILED (UNEXPECTED) ---\n{e}\n"
            continue

    # 5. SETTLEMENT
    try:
        landlord.charge_rent(api_key, total_cost)
        logger.info(f"✅ Workflow Complete. Cost: {int(total_cost)} micro-dollars for {tenant.get('name')}.")
    except Exception as e:
        logger.critical(f"BILLING FAILED for tenant {tenant.get('name')}. Amount: {total_cost}. Error: {e}")
        raise # Critical failure; re-processing is required to attempt billing again.

def run():
    """Main worker loop to poll SQS, with robust handling for each message."""
    logger.info("🐝 MISO V28 (SAFETY) LISTENING...")
    while True:
        messages = []
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=5
            )
            messages = response.get('Messages', [])
        except Exception as e:
            logger.error(f"Could not receive messages from SQS. Retrying in 5s. Error: {e}")
            time.sleep(5)
            continue

        for m in messages:
            receipt_handle = None
            try:
                receipt_handle = m['ReceiptHandle']
                # process() will raise an exception on retryable errors.
                process(m['Body'])

                # If process() completes without error, the message is safe to delete.
                try:
                    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=receipt_handle)
                except Exception as e:
                    logger.critical(f"CRITICAL: Processed successfully but FAILED TO DELETE. Handle: {receipt_handle}. DUPLICATE WORK IMMINENT. Error: {e}")
            
            except Exception as e:
                # This catches errors raised from process(), indicating a systemic
                # issue where the job should be retried after the visibility timeout.
                logger.error(f"Job failed with a retryable error. Will reappear in queue. Handle: {receipt_handle}. Error: {e}")
                # We do NOT delete the message.
                continue

if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Shutdown signal received. Exiting worker.")
    except Exception as e:
        logger.critical(f"FATAL: The main run() loop has crashed unexpectedly. Error: {e}", exc_info=True)
        sys.exit(1)