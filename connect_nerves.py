import os
import boto3
import sys

# --- CONFIGURATION ---
CLUSTER = "MISO-Cluster-Elastic"
SERVICE = "miso-worker-service-iac"
REDIS_ENDPOINT = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"

client = boto3.client('ecs', region_name='us-east-1')

print(f"🔌 Connecting Nerves (Injecting REDIS_HOST) into {SERVICE}...")

# 1. Fetch Current Definition
services = client.describe_services(cluster=CLUSTER, services=[SERVICE])
current_task_arn = services['services'][0]['taskDefinition']
full_def = client.describe_task_definition(taskDefinition=current_task_arn)
task_def = full_def['taskDefinition']

# 2. Inject Variables
container_defs = task_def['containerDefinitions']
for container in container_defs:
    env = container.get('environment', [])
    # Remove existing to avoid dupes
    env = [e for e in env if e['name'] not in ['REDIS_HOST', 'REDIS_PORT']]
    # Add correct values
    env.append({'name': 'REDIS_HOST', 'value': REDIS_ENDPOINT})
    env.append({'name': 'REDIS_PORT', 'value': '6379'})
    container['environment'] = env

# 3. Register New Definition
register_args = {
    "family": task_def['family'],
    "containerDefinitions": container_defs,
    "networkMode": task_def.get('networkMode'),
    "requiresCompatibilities": task_def.get('requiresCompatibilities'),
    "cpu": task_def.get('cpu'),
    "memory": task_def.get('memory'),
}
if 'taskRoleArn' in task_def: register_args['taskRoleArn'] = task_def['taskRoleArn']
if 'executionRoleArn' in task_def: register_args['executionRoleArn'] = task_def['executionRoleArn']

response = client.register_task_definition(**register_args)
new_arn = response['taskDefinition']['taskDefinitionArn']
print(f"✅ Configuration Updated: {new_arn.split('/')[-1]}")

# 4. Update Service
client.update_service(cluster=CLUSTER, service=SERVICE, taskDefinition=new_arn, forceNewDeployment=True)
print("🚀 Service Restarting with Connectivity. Wait 60s.")
