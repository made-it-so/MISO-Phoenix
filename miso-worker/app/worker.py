import boto3
import json
import logging
import os
import time
import sys
import google.generativeai as genai
from google.api_core import retry

# --- CONFIGURATION ---
COST_PER_VCPU_HOUR = 0.04048
COST_PER_GB_HOUR = 0.004445
TASK_VCPU = 0.25
TASK_MEMORY_GB = 0.5
COMPUTE_PRICE_PER_SECOND = ((TASK_VCPU * COST_PER_VCPU_HOUR) + (TASK_MEMORY_GB * COST_PER_GB_HOUR)) / 3600

# Model ID
MODEL_ID = "gemini-1.5-flash"
PRICE_PER_1M_INPUT = 0.075
PRICE_PER_1M_OUTPUT = 0.30

logger = logging.getLogger("MISO_Fintech_Worker")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

def emit_telemetry(event_type, details):
    log_entry = {
        "event": event_type,
        "timestamp": time.time(),
        "worker_id": os.environ.get("HOSTNAME", "unknown"),
        "model_id": MODEL_ID,
        **details
    }
    logger.info(json.dumps(log_entry))

def calculate_token_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1_000_000) * PRICE_PER_1M_INPUT
    output_cost = (output_tokens / 1_000_000) * PRICE_PER_1M_OUTPUT
    return input_cost + output_cost

def process_task(payload):
    start_time = time.time()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_ID)

    prompt = payload.get("payload", {}).get("prompt")
    if not prompt:
        raise ValueError("No prompt provided")

    try:
        response = model.generate_content(prompt)
        if not response.parts:
             raise ValueError("Model returned no content")

        response_text = response.text
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        
    except Exception as e:
        emit_telemetry("INFERENCE_FAILURE", {"error": str(e)})
        raise e

    duration = time.time() - start_time
    compute_cost = duration * COMPUTE_PRICE_PER_SECOND
    token_cost = calculate_token_cost(input_tokens, output_tokens)
    total_cost = compute_cost + token_cost

    return {
        "status": "SUCCESS",
        "duration_seconds": round(duration, 4),
        "compute_cost_usd": round(compute_cost, 8),
        "token_cost_usd": round(token_cost, 8),
        "total_cost_usd": round(total_cost, 8),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "response_snippet": response_text[:100] + "..." 
    }

def main():
    # --- DEBUG: LOG VERSION ON STARTUP ---
    emit_telemetry("WORKER_INIT", {
        "status": "booting",
        "google_sdk_version": genai.__version__ 
    })

    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = os.environ.get("SQS_QUEUE_URL") or os.environ.get("MISO_SQS_QUEUE_URL")

    if not queue_url:
        emit_telemetry("CRITICAL_FAILURE", {"error": "Missing SQS_QUEUE_URL"})
        sys.exit(1)

    emit_telemetry("WORKER_START", {"status": "online", "queue": queue_url})

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            if 'Messages' in response:
                for message in response['Messages']:
                    receipt_handle = message['ReceiptHandle']
                    try:
                        body = json.loads(message['Body'])
                        emit_telemetry("TASK_RECEIVED", {"message_id": message['MessageId']})
                        result = process_task(body)
                        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
                        emit_telemetry("TASK_COMPLETE", result)
                    except Exception as e:
                        emit_telemetry("TASK_FAILED", {"error": str(e)})
        except Exception as e:
            emit_telemetry("WORKER_ERROR", {"error": str(e)})
            time.sleep(5)

if __name__ == "__main__":
    main()
