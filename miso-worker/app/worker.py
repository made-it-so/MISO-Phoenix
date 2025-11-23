import boto3
import json
import time
import os
import logging
import redis
from botocore.exceptions import ClientError

# --- MISO V7: Source of Truth ---
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"
DYNAMO_TABLE = "miso_replay_buffer"
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

# Secrets ARNs
SECRET_ARN_GEMINI = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/gemini_api_key-sJkRuG"
SECRET_ARN_GCP = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/gcp_arbitrage_key"
SECRET_ARN_AZURE = "arn:aws:secretsmanager:us-east-1:356206423360:secret:miso/azure_arbitrage_key"

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [MISO-V7] %(message)s')
logger = logging.getLogger(__name__)

# Clients
sqs = boto3.client('sqs', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
table = dynamodb.Table(DYNAMO_TABLE)

# Redis Connection (With Retry Logic)
cache = None
try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_connect_timeout=2)
    cache.ping() 
    logger.info(f"✅ MSD Cache Connected: {REDIS_HOST}")
except Exception as e:
    logger.warning(f"⚠️ MSD Cache Connection Failed: {e}")

def get_secret(secret_arn):
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
    except ClientError as e:
        logger.error(f"Secret Error: {e}")
        return None

def check_msd_cache(feature_vector):
    """O(1) Geometric Lookup"""
    if not cache: return None
    try:
        cached_decision = cache.get(feature_vector)
        if cached_decision: return cached_decision.decode('utf-8')
    except Exception as e:
        logger.error(f"Cache Read Error: {e}")
    return None

def update_msd_cache(feature_vector, decision):
    if not cache: return
    try:
        cache.setex(feature_vector, 3600, decision)
    except Exception as e:
        logger.error(f"Cache Write Error: {e}")

def commit_replay_buffer(session_id, feature_vector, decision, vendor):
    """
    Fixed Schema: Maps session_id -> task_id
    """
    try:
        table.put_item(
            Item={
                'task_id': session_id,  # <--- SCHEMA FIX (Was session_id)
                'feature_vector_hash': feature_vector,
                'decision_timestamp': int(time.time()),
                'optimal_decision': decision,
                'vendor_target': vendor,
                'msd_hit_count': 0 
            }
        )
        logger.info(f"💾 Committed to DynamoDB: {session_id}")
    except ClientError as e:
        logger.error(f"DynamoDB Commit Failed: {e}")

def process_arbitrage_task(task_body):
    payload = json.loads(task_body)
    session_id = payload.get("session_id", "UNKNOWN")
    cloud_target = payload.get("cloud_target", "AWS") 
    feature_vector = payload.get("feature_hash", "hash_0000")

    logger.info(f"Processing Task: {session_id} | Vector: {feature_vector}")

    # 1. Check Cache
    cached_decision = check_msd_cache(feature_vector)
    if cached_decision:
        logger.info(f"🚀 MSD Cache HIT! Reusing: {cached_decision}")
        return

    # 2. Check Secrets
    api_key = None
    if cloud_target == "GCP":
        secrets = get_secret(SECRET_ARN_GCP)
        api_key = secrets.get("gcp_api_key") if secrets else None
    elif cloud_target == "AZURE":
        secrets = get_secret(SECRET_ARN_AZURE)
        api_key = secrets.get("azure_api_key") if secrets else None
    else:
        secrets = get_secret(SECRET_ARN_GEMINI)
        api_key = list(secrets.values())[0] if secrets else None

    if not api_key:
        logger.error("❌ Credentials missing.")
        return

    # 3. Compute
    logger.info(f"⚡ Computing on {cloud_target}...")
    time.sleep(1) 
    decision = f"OPTIMAL_{cloud_target}"

    # 4. Save
    update_msd_cache(feature_vector, decision)
    commit_replay_buffer(session_id, feature_vector, decision, cloud_target)

def poll_queue():
    logger.info(f"🎧 MISO Worker V7 Listening...")
    while True:
        try:
            response = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=1, WaitTimeSeconds=10)
            if 'Messages' in response:
                for message in response['Messages']:
                    process_arbitrage_task(message['Body'])
                    sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
        except Exception as e:
            logger.error(f"Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    poll_queue()
