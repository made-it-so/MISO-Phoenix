import boto3
import json
import time
import logging
import redis
from botocore.exceptions import ClientError
from vendors import get_vendor_adapter

AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
DYNAMO_TABLE = "miso_replay_buffer"
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379
SECRET_ARN_GCP = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/gcp_arbitrage_key"
SECRET_ARN_AZURE = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/azure_arbitrage_key"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [MISO-V7.1] %(message)s')
logger = logging.getLogger(__name__)

sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
secrets = boto3.client('secretsmanager', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

cache = None
try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_connect_timeout=2)
    cache.ping()
except: pass

def get_key(arn):
    try: return json.loads(secrets.get_secret_value(SecretId=arn)['SecretString'])
    except: return {}

def process(body):
    p = json.loads(body)
    tid = p.get("session_id")
    tgt = p.get("cloud_target", "AWS")
    vec = p.get("feature_hash", "0")
    
    logger.info(f"Processing: {tid} -> {tgt}")
    
    # 1. MSD Cache Check
    if cache and cache.get(vec):
        logger.info("🚀 Cache HIT")
        return

    # 2. Credential Fetch
    key = None
    if tgt == "GCP": key = get_key(SECRET_ARN_GCP).get("gcp_api_key")
    elif tgt == "AZURE": key = get_key(SECRET_ARN_AZURE).get("azure_api_key")
    
    if not key:
        logger.error("❌ No Key found or Invalid Target")
        return

    # 3. External Execution via Adapter
    try:
        adapter = get_vendor_adapter(tgt)
        res = adapter.compute({"id": tid}, key)
        logger.info(f"✅ External Success: {res}")
        
        # 4. Persistence
        if cache: cache.setex(vec, 3600, res)
        table.put_item(Item={
            'task_id': tid,
            'feature_vector_hash': vec,
            'decision_timestamp': int(time.time()),
            'optimal_decision': res,
            'vendor_target': tgt
        })
        logger.info("💾 Saved to DynamoDB")
    except Exception as e:
        logger.error(f"🔥 Fail: {e}")

def run():
    logger.info("🎧 MISO V7.1 (Network) Listening...")
    while True:
        try:
            r = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=10)
            for m in r.get('Messages', []):
                process(m['Body'])
                sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=m['ReceiptHandle'])
        except Exception as e:
            logger.error(f"Loop Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run()
