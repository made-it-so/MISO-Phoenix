import os
import boto3
from functools import lru_cache

@lru_cache()
def get_secret(key_name, default=None):
    # LOCAL DEV: Allow fallback to env vars if AWS creds aren't active
    if os.getenv("MISO_ENV") == "local":
        return os.getenv(key_name, default)

    # PROD (FARGATE): Fetch from SSM Parameter Store
    try:
        ssm = boto3.client('ssm', region_name='us-east-1')
        # Assumes keys are stored as /miso/openai_key, etc.
        # For this MVP, we will try env vars first to keep it simple for you today.
        return os.getenv(key_name, default) 
    except Exception:
        return default

# MAPPING: Normalized Model Names -> Provider Models
MODEL_MAP = {
    "flash": "gemini/gemini-1.5-flash", 
    "coder": "claude-3-sonnet-20240229", # AWS Bedrock or Anthropic
    "reasoner": "gpt-4o",
    "cheap": "gpt-3.5-turbo"
}
