import os
# EVOLVED BY MISO V28 (ECONOMY)
import boto3
import json
import time
import logging
import redis
import random
import os
import google.generativeai as genai  # <--- REQUIRED FOR EXECUTION
from vendors import get_vendor_adapter
from pricing import MarketOracle
from tenant_manager import Landlord
from router import NeuralRouter

# CONFIG
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
DYNAMO_TABLE = "miso_replay_buffer"
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
ECONOMY_MODEL = "gemini-1.5-flash-latest" # Cost-optimization strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WORKER-V28.0-ECONOMY] %(message)s')
logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
secrets = boto3.client('secretsmanager', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)
market = MarketOracle()
landlord = Landlord()
router = NeuralRouter()

def get_key(arn):
    try: return json.loads(secrets.get_secret_value(SecretId=arn)['SecretString'])
    except: return {}

def execute_step(instruction, model_name, context=""):
    """
    The Actual Work.
    Instantiates the specific brain requested.
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
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
        logger.warning(f"Execution step failed for model {model_name}: {e}")
        return f"Error executing step: {e}"

def process(body):
    try:
        p = json.loads(body)
        api_key = p.get("api_key")
        tenant = landlord.authenticate(api_key)
        if not tenant: return

        task_desc = p.get("description", "Generic Task")

        # 1. THE PLAN
        plan = router.create_plan(task_desc)

        total_cost = 0
        accumulated_context = "" # Chains the outputs together

        logger.info(f"🏗️ Executing {len(plan)}-Step Workflow for {tenant['name']}...")

        # 2. THE SWARM (ECONOMY MODE)
        for step in plan:
            step_id = step['step']
            instruction = step['instruction']
            original_brain = step['model'] # Router's suggestion, e.g., 'gemini-1.5-pro'

            # == ECONOMY STRATEGY APPLIED ==
            # Aggressively override the planner's choice to use the Flash model.
            brain = ECONOMY_MODEL
            if brain != original_brain:
                logger.info(f"   ⚡️ ECONOMY OVERRIDE: Using {brain} instead of {original_brain}")
            # ==============================

            logger.info(f"   👉 Step {step_id} ({brain}): {instruction[:40]}...")

            # REAL EXECUTION
            start = time.perf_counter()
            result = execute_step(instruction, brain, accumulated_context)
            dur = time.perf_counter() - start

            # Accumulate Context (So Step 2 knows what Step 1 did)
            accumulated_context += f"\n--- STEP {step_id} RESULT ---\n{result}\n"

            # Pricing (Mock calculation for billing)
            # This logic will now rarely, if ever, apply the 'pro' multiplier.
            step_cost = 10 * (dur * 1000)
            if "pro" in brain: step_cost *= 10
            total_cost += step_cost

        # 3. SETTLEMENT
        landlord.charge_rent(api_key, total_cost)
        logger.info(f"✅ Workflow Complete. Cost: {int(total_cost)} micro-dollars.")

    except Exception as e:
        logger.error(f"ERR: {e}")

def run():
    logger.info("🐝 MISO V28.0 (ECONOMY) LISTENING...")
    while True:
        try:
            r = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5)
            for m in r.get('Messages', []):
                process(m['Body'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m['ReceiptHandle'])
        except Exception as e:
            logger.error(f"SQS loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()