import boto3
import time

CLUSTER = "MISO-Cluster-Elastic"
SERVICE = "miso-worker-service-iac"
REGION = "us-east-1"

def hibernate():
    client = boto3.client('ecs', region_name=REGION)
    print(f"☁️  Connecting to {CLUSTER}...")

    try:
        # Step A: Force New Deployment (Updates the service to use the new Image we just pushed)
        # We set desiredCount=0 immediately so it updates the definition but doesn't spin up tasks.
        print("🔄 Updating Service Definition to V36...")
        client.update_service(
            cluster=CLUSTER,
            service=SERVICE,
            forceNewDeployment=True,
            desiredCount=0 
        )
        print("✅ Service Updated. Target State: 0 Tasks.")

        # Step B: Verification
        print("⏳ Verifying Shutdown...")
        time.sleep(5)
        response = client.describe_services(cluster=CLUSTER, services=[SERVICE])
        running = response['services'][0]['runningCount']
        desired = response['services'][0]['desiredCount']
        
        print(f"📊 STATUS: Running={running} | Desired={desired}")
        
        if desired == 0:
            print("✅ HIBERNATION CONFIRMED. No costs will be incurred.")
        else:
            print("⚠️ WARNING: Desired count is not zero.")

    except Exception as e:
        print(f"❌ AWS ERROR: {e}")

if __name__ == "__main__":
    hibernate()
