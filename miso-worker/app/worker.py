import boto3
import json
import time
import logging
import os
import google.generativeai as genai
from tenant_manager import Landlord
from router import NeuralRouter
from cache_layer import SemanticCache
from pricing import MarketOracle
from oracle import Oracle
from reflex import SystemReflex # <--- RE-INTEGRATING V33
from federation import FederationHub # <--- INTEGRATING V39

# CONFIG
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SUPER-WORKER] %(message)s')
logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=AWS_REGION)
secrets = boto3.client('secretsmanager', region_name=AWS_REGION)

# The Full Organism
landlord = Landlord()
router = NeuralRouter()
memory = SemanticCache()
market = MarketOracle()
oracle = Oracle()
reflex = SystemReflex()
hub = FederationHub() # Connect to the Global Sensor Network

def process(body):
    try:
        p = json.loads(body)
        api_key = p.get("api_key")
        tenant = landlord.authenticate(api_key)
        if not tenant: return

        task_desc = p.get("description", "Generic Task")
        
        # 1. CACHE CHECK (V30)
        if memory.check(task_desc):
            logger.info("⚡ CACHE HIT. Zero Cost.")
            return

        # 2. FEDERATED INTELLIGENCE (V39)
        # Check if the Federation Hub has found a global best region
        world_view = hub.get_world_view()
        global_best = world_view.get('global_best')
        
        if global_best:
            best_node = world_view['nodes'][global_best]
            target = best_node['provider']
            logger.info(f"🌐 FEDERATION CONSENSUS: Route to {target} ({best_node['region']})")
        else:
            # Fallback to Local Oracle (V38)
            prices = market.get_spot_prices()
            target = "GCP" if prices.get("GCP", 999) < prices.get("AZURE", 999) else "AZURE"
            advice = oracle.advise_execution(target)
            if "WAIT" in advice:
                logger.info(f"🔮 ORACLE WARN: {advice}. Pausing...")
                time.sleep(2)

        # 3. EXECUTION (V27 Swarm)
        plan = router.create_plan(task_desc)
        logger.info(f"🏗️ Executing on {target}...")
        
        for step in plan:
            # 4. REFLEX SAFETY CHECK (V33)
            reflex.wait_for_safety()
            
            # Do the work...
            time.sleep(0.1) 
            
        logger.info("✅ Done.")

    except Exception as e:
        logger.error(f"ERR: {e}")

def run():
    logger.info("🤖 MISO COMPLETE (V39+V33) LISTENING...")
    reflex.start() # Start the heartbeat
    while True:
        try:
            r = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=5)
            for m in r.get('Messages', []):
                process(m['Body'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m['ReceiptHandle'])
        except: time.sleep(1)

if __name__ == "__main__":
    run()
