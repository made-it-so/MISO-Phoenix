import boto3
import json
import time
import logging
import os
import google.generativeai as genai
from tenant_manager import Landlord
from router import NeuralRouter
from cache_layer import SemanticCache
from reflex import SystemReflex # <--- THE UPGRADE

# CONFIG
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WORKER-V33] %(message)s')
logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=AWS_REGION)
secrets = boto3.client('secretsmanager', region_name=AWS_REGION)

landlord = Landlord()
router = NeuralRouter()
memory = SemanticCache()
reflex = SystemReflex() # <--- INSTANTIATE

def execute_step(instruction, model_name, context=""):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        prompt = f"CONTEXT: {context}\nTASK: {instruction}\nOUTPUT: Perform task."
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: {e}"

def process(body):
    try:
        p = json.loads(body)
        api_key = p.get("api_key")
        tenant = landlord.authenticate(api_key)
        if not tenant: return

        task_desc = p.get("description", "Generic Task")
        
        # CHECK INTENT CACHE
        cached = memory.check(task_desc)
        if cached:
            logger.info("⚡ CACHE HIT. Skipping logic.")
            return

        # DELIBERATIVE LAYER (Planning)
        plan = router.create_plan(task_desc)
        total_cost = 0
        accumulated_context = ""
        
        logger.info(f"🏗️ Executing {len(plan)}-Step Workflow...")

        # EXECUTIVE LAYER (Sequencing)
        for step in plan:
            # --- REACTIVE LAYER CHECK ---
            # Before every step, we check the Reflex.
            # If CPU is high, this line BLOCKS until it drops.
            reflex.wait_for_safety()
            # ----------------------------

            instruction = step['instruction']
            brain = step['model']
            
            start = time.perf_counter()
            result = execute_step(instruction, brain, accumulated_context)
            dur = time.perf_counter() - start
            
            logger.info(f"   👉 {brain}: {instruction[:30]}... ({dur:.2f}s)")
            accumulated_context += f"\nResult: {result}\n"
            
            base_price = 10 if "pro" in brain else 1
            total_cost += (base_price * dur * 10)

        memory.store(task_desc, accumulated_context)
        landlord.charge_rent(api_key, total_cost)
        logger.info(f"✅ Done. Cost: {int(total_cost)}.")

    except Exception as e:
        logger.error(f"ERR: {e}")

def run():
    logger.info("🛡️ MISO V33 (HIERARCHICAL CONTROL) STARTING...")
    
    # START THE REFLEX DAEMON
    reflex.start()
    
    while True:
        try:
            # Reflex check logic handles the pause, so we just poll normally
            r = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5)
            for m in r.get('Messages', []):
                process(m['Body'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m['ReceiptHandle'])
        except: time.sleep(1)

if __name__ == "__main__":
    run()
