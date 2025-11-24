import boto3
import time

REGION = "us-east-1"
LOG_GROUP = "/ecs/miso-worker-task"

def read_black_box():
    client = boto3.client('logs', region_name=REGION)
    print(f"🕵️‍♂️ Spying on Cloud Logs ({LOG_GROUP})...")
    
    try:
        # Get latest stream
        streams = client.describe_log_streams(
            logGroupName=LOG_GROUP,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("❌ No log streams found. Task might be silent.")
            return

        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"   Target Stream: {stream_name}")
        
        # Get events
        events = client.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=stream_name,
            limit=15,
            startFromHead=False
        )
        
        print("\n--- CLOUD TELEMETRY ---")
        for e in events['events']:
            print(f"☁️  {e['message']}")
            
    except Exception as e:
        print(f"❌ SPY FAILED: {e}")

if __name__ == "__main__":
    read_black_box()
