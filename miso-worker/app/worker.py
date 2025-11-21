import boto3
import json
import logging
import os
import time
import sys
import google.generativeai as genai

# --- MISO FINTECH CONFIGURATION ---
COST_PER_VCPU_HOUR = 0.04048
COST_PER_GB_HOUR = 0.004445
TASK_VCPU = 0.25
TASK_MEMORY_GB = 0.5
COMPUTE_PRICE_PER_SECOND = ((TASK_VCPU * COST_PER_VCPU_HOUR) + (TASK_MEMORY_GB * COST_PER_GB_HOUR)) / 3600

# Intelligence Market Data
MODEL_ID = "gemini-2.0-flash"
PRICE_PER_1M_INPUT = 0.10
PRICE_PER_1M_OUTPUT = 0.40

# DynamoDB Configuration
TABLE_NAME = "miso_replay_buffer"

# Configure Structured Logging
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

def update_replay_buffer(task_id: str, status: str, metrics: dict):
    """Writes the final execution status and cost metrics back to DynamoDB."""
    try:
        dynamodb = boto3.resource("dynamodb", region_name='us-east-1')
        table = dynamodb.Table(TABLE_NAME)
        
        # Update the existing item using the task_id as the primary key
        table.update_item(
            Key={'task_id': task_id},
            UpdateExpression="SET #s = :status, #m = :metrics, #t = :ts",
            ExpressionAttributeNames={
                '#s': 'status',
                '#m': 'metrics',
                '#t': 'completed_at'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':metrics': metrics,
                ':ts': int(time.time())
            }
        )
        emit_telemetry("DB_WRITEBACK_SUCCESS", {"task_id": task_id, "status": status})
        
    except Exception as e:
        # Log the failure but do not crash the worker
        emit_telemetry("DB_WRITEBACK_FAILURE", {"task_id": task_id, "error": str(e)})


def process_task(payload):
    start_time = time.time()
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_ID)

    prompt = payload.get("persona", {}).get("payload", {}).get("prompt") # Extract from the Persona structure
    task_id = payload.get("task_id", "unknown_id")
    
    if not prompt:
        raise ValueError("No prompt provided in task payload")

    try:
        response = model.generate_content(prompt)
        if not response.parts:
             raise ValueError("Model returned no content")

        # Metrics Extraction
        usage = response.usage_metadata
        input_tokens = usage.prompt_token_count
        output_tokens = usage.candidates_token_count
        
        duration = time.time() - start_time
        compute_cost = duration * COMPUTE_PRICE_PER_SECOND
        token_cost = calculate_token_cost(input_tokens, output_tokens)
        total_cost = compute_cost + token_cost

        metrics = {
            "duration_seconds": round(duration, 4),
            "total_cost_usd": round(total_cost, 8),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_snippet": response.text[:100] + "..." 
        }
        
        # --- PHASE 1: WRITEBACK ---
        update_replay_buffer(task_id, "SUCCESS", metrics)
        
        return metrics
        
    except Exception as e:
        metrics = {"duration_seconds": round(time.time() - start_time, 4), "error": str(e)}
        update_replay_buffer(task_id, "FAILED", metrics)
        emit_telemetry("INFERENCE_FAILURE", metrics)
        raise e

def main():
    # Logging initialization... [omitted for brevity, assume full logging from previous steps]
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = os.environ.get("SQS_QUEUE_URL") or os.environ.get("MISO_SQS_QUEUE_URL")

    if not queue_url:
        sys.exit(1)

    # Worker start logic... [omitted]

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
                        # The SQS body now contains { "task_id": ..., "persona": { ... } }
                        task_id = body.get("task_id", "unknown")
                        
                        # Execute task and WRITEBACK
                        metrics = process_task(body)
                        
                        # SETTLE TRADE (Delete Message)
                        sqs.delete_message(
                            QueueUrl=queue_url,
                            ReceiptHandle=receipt_handle
                        )
                        
                        emit_telemetry("TASK_COMPLETE", metrics)
                        
                    except Exception as e:
                        # Error handling will trigger FAILED status in update_replay_buffer
                        pass 

        except Exception as e:
            # Worker error handling... [omitted]
            time.sleep(5)

if __name__ == "__main__":
    main()
