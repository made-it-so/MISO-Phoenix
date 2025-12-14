import boto3
import json
import os
import sys
import time
from openai import OpenAI

# --- CONFIGURATION (v2) ---
JOB_QUEUE = "MisoQueue_v4_OD" 
JOB_DEF = "MisoJob"
INPUT_BUCKET = "miso-production-input"
RESULTS_BUCKET = "miso-production-results"
MAX_RETRIES = 3

batch = boto3.client('batch', region_name='us-east-1')
logs = boto3.client('logs', region_name='us-east-1')

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("ERROR: Please export your OpenAI key: export OPENAI_API_KEY='sk-...'")
    sys.exit(1)

client = OpenAI(api_key=api_key)

# UPDATED PROMPT: TEACHES LLM ABOUT THE RUNNER SCRIPT
SYSTEM_PROMPT = """
You are the MISO Orchestrator.
Your goal: Output a JSON job definition for the AWS Batch "Smart Runner".

CRITICAL:
The system uses a custom runner script (runner.py).
The command format MUST be: [INPUT_S3_URI, OUTPUT_S3_URI, ...FLAGS...]

RULES:
1. Input files are at s3://{}/<filename>
2. Output path must be s3://{}/<job_id>/
3. Do NOT use --run or --output-dir (the runner handles this).
4. ONLY specify analysis flags like --paired-end, --read-len.

JSON FORMAT:
{{
  "reasoning": "Why you chose these flags",
  "command": ["s3://{}/sample_01.bam", "s3://{}/job_123/", "--paired-end", "75"]
}}
""".format(INPUT_BUCKET, RESULTS_BUCKET, INPUT_BUCKET, RESULTS_BUCKET)

def get_job_logs(log_stream_name):
    if not log_stream_name: return "No log stream."
    try:
        response = logs.get_log_events(
            logGroupName='/aws/batch/job',
            logStreamName=log_stream_name,
            limit=20,
            startFromHead=False
        )
        return "\n".join([e['message'] for e in response['events']])
    except: return "Logs unavailable."

def submit_and_watch(command_list, attempt=1):
    print(f"\n--- ATTEMPT {attempt}/{MAX_RETRIES} ---")
    try:
        sub = batch.submit_job(
            jobName=f'miso-auto-{attempt}',
            jobQueue=JOB_QUEUE,
            jobDefinition=JOB_DEF,
            containerOverrides={'command': command_list}
        )
        job_id = sub['jobId']
        print(f"[Muscle] Job Submitted: {job_id}")
    except Exception as e:
        return False, str(e)

    print("[Muscle] Watching job status...")
    log_stream = None
    
    while True:
        time.sleep(5)
        desc = batch.describe_jobs(jobs=[job_id])
        job = desc['jobs'][0]
        status = job['status']
        
        if 'container' in job and 'logStreamName' in job['container']:
            log_stream = job['container']['logStreamName']
            
        print(f"   Status: {status}")
        
        if status == 'SUCCEEDED': return True, "Success"
        if status == 'FAILED':
            reason = job.get('statusReason', 'Unknown')
            logs = get_job_logs(log_stream)
            return False, f"Reason: {reason}\nLogs:\n{logs}"

def run_agent(user_query):
    history = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_query}]

    for i in range(1, MAX_RETRIES + 1):
        print(f"\n[Brain] Generating Plan (Iteration {i})...")
        completion = client.chat.completions.create(
            model="gpt-4-turbo", response_format={"type": "json_object"}, messages=history
        )
        plan_text = completion.choices[0].message.content
        plan = json.loads(plan_text)
        print(f"[Brain] Command: {plan['command']}")
        
        success, report = submit_and_watch(plan['command'], attempt=i)
        
        if success:
            print("\n[SUCCESS] Task Complete.")
            break
        else:
            print(f"\n[FAILURE] Retrying... Report:\n{report}")
            history.append({"role": "assistant", "content": plan_text})
            history.append({"role": "user", "content": f"Failed. Fix flags based on logs:\n{report}"})

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py 'Your question here'")
        sys.exit(1)
    run_agent(sys.argv[1])
