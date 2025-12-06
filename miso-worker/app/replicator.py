import boto3
import os
import logging
import zipfile
import io
import sys
import json
import time

# CONFIG
REGION = "us-east-1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAMBDA_NAME = "MISO_Colony_Alpha"
# UPDATED ROLE ARN
ROLE_ARN = "arn:aws:iam::356206423360:role/MISO-Colony-Role"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [REPLICATOR] %(message)s')
logger = logging.getLogger(__name__)

lambda_client = boto3.client('lambda', region_name=REGION)

def create_genome_zip():
    """Packages source code into a Lambda-compatible ZIP."""
    logger.info("🧬 Sequencing DNA (Creating Zip)...")
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Create the entry point for Lambda
        handler_code = """
import json
import os

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps('👋 HELLO FROM MISO COLONY! I AM ALIVE.')
    }
"""
        zf.writestr("lambda_function.py", handler_code)
        
        # Backup source code into the zip
        for root, dirs, files in os.walk(BASE_DIR):
            for file in files:
                if file.endswith(".py"):
                    arcname = os.path.join("source_backup", file)
                    zf.write(os.path.join(root, file), arcname)
                    
    zip_buffer.seek(0)
    logger.info(f"📦 Genome Packaged: {len(zip_buffer.getvalue())} bytes")
    return zip_buffer.getvalue()

def spawn_colony(zip_bytes):
    """Deploys code to AWS Lambda."""
    try:
        try:
            lambda_client.get_function(FunctionName=LAMBDA_NAME)
            logger.info("♻️  Colony exists. Updating DNA...")
            lambda_client.update_function_code(
                FunctionName=LAMBDA_NAME,
                ZipFile=zip_bytes
            )
        except lambda_client.exceptions.ResourceNotFoundException:
            logger.info("✨ Spawning NEW Colony...")
            lambda_client.create_function(
                FunctionName=LAMBDA_NAME,
                Runtime='python3.9',
                Role=ROLE_ARN,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_bytes},
                Timeout=10,
                MemorySize=128
            )
            
        # Wait for update to propagate
        logger.info("⏳ Incubating (Wait 5s)...")
        time.sleep(5)
        return True
        
    except Exception as e:
        logger.error(f"❌ Replication Failed: {e}")
        return False

def contact_colony():
    """Invokes the remote clone."""
    try:
        logger.info("📡 Pinging Colony...")
        response = lambda_client.invoke(
            FunctionName=LAMBDA_NAME,
            InvocationType='RequestResponse'
        )
        payload = json.loads(response['Payload'].read())
        logger.info(f"👽 REMOTE SIGNAL RECEIVED: {payload['body']}")
    except Exception as e:
        logger.error(f"❌ Contact Lost: {e}")

if __name__ == "__main__":
    genome = create_genome_zip()
    if spawn_colony(genome):
        contact_colony()
