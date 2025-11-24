import boto3
import json
import time
import logging
import os
import google.generativeai as genai
from tenant_manager import Landlord
from router import NeuralRouter
from continuum import ContinuumMemory # <--- NESTED LEARNING

# CONFIG
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [WORKER-V36] %(message)s')
logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=AWS_REGION)
landlord = Landlord()
router = NeuralRouter()
continuum = ContinuumMemory()

def execute_step(instruction, model_name, context=""):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # --- NESTED LEARNING INJECTION ---
        # We inject the Continuum Memory into the prompt.
        # This is equivalent to the "Context Flow" in the paper.
        memory_state = continuum.get_context()
        
        system_prompt = f"""
        SYSTEM WISDOM:
        - Strategic Goal: {memory_state['strategy']}
        - Recent Tactics: {memory_state['tactics']}
        
        CONTEXT: {context}
        TASK: {instruction}
        """
        
        response = model.generate_content(system_prompt)
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
        
        # 1. PLAN
        plan = router.create_plan(task_desc)
        total_cost = 0
        
        logger.info(f"🏗️ Processing for {tenant['name']}...")

        for step in plan:
            # 2. EXECUTE (With Nested Memory)
            start = time.perf_counter()
            result = execute_step(step['instruction'], step['model'])
            dur = time.perf_counter() - start
            
            # 3. INGEST EVENT (Update the Continuum)
            # This is the "Online Consolidation" described in the paper
            event = {
                "step": step['instruction'][:20],
                "duration": dur,
                "model": step['model'],
                "status": "SUCCESS"
            }
            continuum.ingest_event(event)
            
            logger.info(f"   👉 {step['model']}: Done in {dur:.2f}s")
            
            # Pricing logic...
            total_cost += 1 # Mock cost

        landlord.charge_rent(api_key, total_cost)

    except Exception as e:
        logger.error(f"ERR: {e}")

def run():
    logger.info("🧠 MISO V36 (NESTED LEARNING) LISTENING...")
    while True:
        try:
            r = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5)
            for m in r.get('Messages', []):
                process(m['Body'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m['ReceiptHandle'])
        except: time.sleep(1)

if __name__ == "__main__":
    run()
