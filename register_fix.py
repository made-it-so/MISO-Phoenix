import boto3
import sys

# Initialize the Batch client
batch = boto3.client('batch', region_name='us-east-1')

print("Registering MisoJob_Shell...")

try:
    response = batch.register_job_definition(
        jobDefinitionName='MisoJob_Shell',
        type='container',
        containerProperties={
            'image': '356206423360.dkr.ecr.us-east-1.amazonaws.com/miso-production:latest',
            'memory': 2048,
            'vcpus': 1,
            'jobRoleArn': 'arn:aws:iam::356206423360:role/MisoInstanceRole',
            'entryPoint': ['/bin/sh', '-c'],  # <--- This is the magic override
            'command': ['echo', 'Placeholder']
        }
    )
    print("Success! Created: " + response['jobDefinitionArn'])
except Exception as e:
    print("Error:", e)
