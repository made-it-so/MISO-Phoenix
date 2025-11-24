import boto3
import time

CLUSTER = "MISO-Cluster-Elastic"
SERVICE = "miso-worker-service-iac"
REGION = "us-east-1"

def go_live():
    client = boto3.client('ecs', region_name=REGION)
    
    print(f"🚀 Connecting to ECS Cluster: {CLUSTER}...")
    
    try:
        # 1. Force Update
        response = client.update_service(
            cluster=CLUSTER,
            service=SERVICE,
            desiredCount=1
        )
        print("✅ Update Signal Sent. Scaling to 1...")
        
        # 2. Watch for Stability
        print("⏳ Waiting for provisioning (this takes ~30s)...")
        waiter = client.get_waiter('services_stable')
        waiter.wait(
            cluster=CLUSTER,
            services=[SERVICE],
            WaiterConfig={'Delay': 5, 'MaxAttempts': 20}
        )
        print("✅ SERVICE IS LIVE AND STABLE.")
        
        # 3. Get Public IP (Forensics)
        # We need to find the Task -> ENI -> Public IP
        tasks = client.list_tasks(cluster=CLUSTER, serviceName=SERVICE)
        if tasks['taskArns']:
            task_id = tasks['taskArns'][0]
            print(f"   Task Active: {task_id.split('/')[-1]}")
        else:
            print("⚠️  Service is stable but no tasks found? (Check logs)")

    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    go_live()
