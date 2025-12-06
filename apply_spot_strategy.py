import boto3

REGION = "us-east-1"
CLUSTER = "MISO-Cluster-Elastic"
SERVICE = "miso-worker-service-iac"

def switch_to_spot():
    client = boto3.client('ecs', region_name=REGION)
    print(f"💰 Switching {SERVICE} to Fargate Spot...")
    
    try:
        response = client.update_service(
            cluster=CLUSTER,
            service=SERVICE,
            capacityProviderStrategy=[
                {
                    'capacityProvider': 'FARGATE_SPOT',
                    'weight': 1,
                    'base': 0
                },
                {
                    'capacityProvider': 'FARGATE',
                    'weight': 0, # Only use standard if Spot is unavailable
                    'base': 0
                }
            ],
            forceNewDeployment=True
        )
        print("✅ Spot Strategy Applied. You are now saving ~70% on compute.")
        
    except Exception as e:
        print(f"❌ FAILED: {e}")

if __name__ == "__main__":
    switch_to_spot()
