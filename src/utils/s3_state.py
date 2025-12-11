import boto3
import os
import sys
import json

# Auto-detect bucket name based on account ID to ensure uniqueness
try:
    sts = boto3.client('sts')
    account_id = sts.get_caller_identity()["Account"]
    BUCKET_NAME = f"miso-brain-state-{account_id}"
    REGION = "us-east-1"
except:
    BUCKET_NAME = None

PATHS = [
    "miso_episodic_memory.json",
    "miso-worker/prompts/constitution.txt",
    "miso-worker/app/tools/registry.json"
]
TOOLS_DIR = "miso-worker/app/tools"

def init_bucket():
    if not BUCKET_NAME: return False
    s3 = boto3.client('s3', region_name=REGION)
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
    except:
        try:
            print(f">> 📦 Creating Lifeboat Bucket: {BUCKET_NAME}")
            s3.create_bucket(Bucket=BUCKET_NAME)
        except Exception as e:
            print(f">> ❌ S3 Init Failed: {e}")
            return False
    return True

def push_state():
    if not init_bucket(): return
    s3 = boto3.client('s3')
    print(">> ☁️  SYNC: Uploading State to S3...")
    
    # 1. Upload Core Files
    for path in PATHS:
        if os.path.exists(path):
            try:
                s3.upload_file(path, BUCKET_NAME, path)
            except Exception as e: print(f">> ⚠️ Upload Failed {path}: {e}")

    # 2. Upload All Tools (Dynamic)
    if os.path.exists(TOOLS_DIR):
        for f in os.listdir(TOOLS_DIR):
            if f.endswith(".py"):
                local = os.path.join(TOOLS_DIR, f)
                remote = os.path.join(TOOLS_DIR, f)
                try:
                    s3.upload_file(local, BUCKET_NAME, remote)
                except: pass
    print(">> ✅ State Secured.")

def pull_state():
    if not init_bucket(): return
    s3 = boto3.client('s3')
    print(">> 📥 RESURRECTION: Downloading State from S3...")
    
    try:
        # List all objects
        objs = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' not in objs:
            print(">> 🕸️  S3 Bucket Empty. Starting Genesis Mode.")
            return

        for obj in objs['Contents']:
            key = obj['Key']
            # Ensure local dir exists
            dir_name = os.path.dirname(key)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name)
            
            s3.download_file(BUCKET_NAME, key, key)
            print(f"   - Restored: {key}")
            
        print(">> ✅ Resurrection Complete. Memory Restored.")
    except Exception as e:
        print(f">> ⚠️ Pull Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pull":
        pull_state()
    else:
        push_state()
