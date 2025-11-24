# EVOLVED BY MISO V29 (SOCIOPATH)
# EVOLVED BY MISO V28 (SPEED)
import boto3
import json
import time
import os
import google.generativeai as genai  # <--- REQUIRED FOR EXECUTION
from tenant_manager import Landlord
from router import NeuralRouter

# --- CONFIG & CLIENTS (SINGLETONS) ---
# Constants are resolved faster from the global scope.
AWS_REGION = "us-east-1"
QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/356206423360/miso_job_queue"

# Pre-initializing clients avoids connection overhead on every job.
sqs = boto3.client('sqs', region_name=AWS_REGION)
landlord = Landlord()
router = NeuralRouter()

# Pre-configure Gemini client at startup; cache model instances to avoid re-creation.
_model_cache = {}
try:
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
except Exception:
    pass # Fail silently; execute_step will raise if not configured.

def execute_step(instruction, model_name, context=""):
    """
    The Actual Work.
    Instantiates the specific brain requested by the Planner.
    Optimized to use a cache for model objects.
    """
    try:
        # Check cache first to avoid object instantiation overhead.
        model = _model_cache.get(model_name)
        if model is None:
            model = genai.GenerativeModel(model_name)
            _model_cache[model_name] = model

        # F-strings are the fastest method for string formatting.
        prompt = f"PREVIOUS CONTEXT: {context}\n\nCURRENT TASK: {instruction}\n\nOUTPUT: Perform the task."

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error executing step: {e}"

def process(body):
    """Processes a single SQS message with logging and other I/O removed."""
    try:
        p = json.loads(body)
        api_key = p.get("api_key")
        
        # Early exit on auth failure is a critical optimization.
        if not landlord.authenticate(api_key):
            return

        # 1. THE PLAN
        plan = router.create_plan(p.get("description", "Generic Task"))

        total_cost = 0
        context_parts = []  # Use a list for efficient string concatenation in a loop.

        # 2. THE SWARM
        for step in plan:
            step_id = step['step']
            instruction = step['instruction']
            brain = step['model']

            # Join context right before use; avoids repeated large string creations.
            current_context = "".join(context_parts)

            # REAL EXECUTION
            start = time.perf_counter()
            result = execute_step(instruction, brain, current_context)
            dur = time.perf_counter() - start

            # Append new context to the list.
            context_parts.append(f"\n--- STEP {step_id} RESULT ---\n{result}\n")

            # Pricing
            step_cost = 10 * (dur * 1000)
            if "pro" in brain:
                step_cost *= 10
            total_cost += step_cost

        # 3. SETTLEMENT
        landlord.charge_rent(api_key, total_cost)

    except Exception:
        # In a speed-focused strategy, we drop failed messages and move on.
        # The message will be deleted without retry.
        pass

def run():
    """Main worker loop optimized for high-throughput SQS consumption."""
    while True:
        try:
            # Use maximum long polling to reduce empty responses and API calls.
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=10, # Max batch size
                WaitTimeSeconds=20      # Max long poll duration
            )
            messages = response.get('Messages', [])
            if not messages:
                continue

            for m in messages:
                process(m['Body'])
                # Delete message immediately after processing attempt.
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=m['ReceiptHandle']
                )
        except Exception:
            # On transient SQS or network errors, pause briefly to avoid spamming.
            time.sleep(1)

if __name__ == "__main__":
    run()