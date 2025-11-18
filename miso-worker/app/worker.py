import boto3
import json
import logging
import os
import time
import sys
import google.generativeai as genai

# --- CONFIGURATION ---
MODEL_ID_PRIMARY = "gemini-1.5-flash"
MODEL_ID_FALLBACK = "gemini-pro" # Fallback to the older model if Flash fails

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
        **details
    }
    logger.info(json.dumps(log_entry))

def list_available_models():
    """Diagnostics: Print what the worker can actually see."""
    try:
        emit_telemetry("DIAGNOSTIC_START", {"message": "Listing available models..."})
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"AVAILABLE MODEL: {m.name}")
    except Exception as e:
         emit_telemetry("DIAGNOSTIC_ERROR", {"error": str(e)})

def process_task(payload):
    start_time = time.time()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
    
    genai.configure(api_key=api_key)

    # TRY PRIMARY MODEL (FLASH)
    active_model_id = MODEL_ID_PRIMARY
    try:
        model = genai.GenerativeModel(active_model_id)
        prompt = payload.get("payload", {}).get("prompt")
        response = model.generate_content(prompt)
    except Exception as e:
        # FAILOVER TO LEGACY MODEL
        emit_telemetry("MODEL_FALLBACK", {"primary_failed": str(e), "switching_to": MODEL_ID_FALLBACK})
        active_model_id = MODEL_ID_FALLBACK
        model = genai.GenerativeModel(active_model_id)
        response = model.generate_content(prompt)

    response_text = response.text
    
    duration = time.time() - start_time
    
    # Simple cost calc (placeholder for fallback logic)
    cost = duration * 0.00001 

    return {
        "status": "SUCCESS",
        "model_used": active_model_id,
        "duration_seconds": round(duration, 4),
        "total_cost_usd": round(cost, 8),
        "response_snippet": response_text[:100] + "..." 
    }

def main():
    # --- CRITICAL DIAGNOSTICS ---
    emit_telemetry("WORKER_INIT", {
        "status": "booting",
        "google_sdk_version": genai.__version__,
        "python_version": sys.version
    })
    
    # Initialize API to run diagnostics
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        list_available_models()

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
