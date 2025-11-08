# MISO Triage Agent - "SWARM LAUNCHER"
# This agent's ONLY job is to launch a parallel
# swarm of Fargate "worker" tasks.

import re
import os
import boto3

class MisoTriageAgent:
    def __init__(self):
        # Initialize the AWS client
        self.ecs_client = boto3.client('ecs', region_name='us-east-1')
        
        # We need to know what Task Definition to run
        self.worker_task_def_arn = "arn:aws:ecs:us-east-1:356206423360:task-definition/miso-task-def-elastic:5"
        self.worker_cluster = "miso-cluster"
        self.worker_subnets = [
            'subnet-01df846c12e725654',
            'subnet-02832ec949ebf1994',
            'subnet-065eb180fb19e1e36',
            'subnet-0faca65ba8ae5f3e4'
        ]
        
        self.mypy_error_regex = re.compile(
            r"^(.*?\.py):\d+: error: (.*?) \[", re.MULTILINE
        )

    def launch_fix_swarm(self, error_log: str) -> int:
        """
        This is the "Elastic Infrastructure" logic.
        It launches a parallel swarm of Fargate tasks to fix bugs.
        """
        print("[COORDINATOR]: Received new batch of errors. Analyzing for Fargate swarm...")
        tasks_launched = 0
        
        all_errors = self.mypy_error_regex.findall(error_log)
        
        # We process *every* error, not just unique files
        if not all_errors:
            print("[COORDINATOR]: No parseable mypy errors found in log.")
            return 0

        print(f"[COORDINATOR]: Identified {len(all_errors)} bugs. Preparing Fargate tasks...")

        for (filename, error_message) in all_errors:
            
            # We only know how to fix this one bug in a swarm
            if "missing a type annotation" in error_message:
                try:
                    print(f"[COORDINATOR]: Launching Fargate 'Lizard' worker for {filename}...")
                    
                    # This is the "Fargate-on-Fargate" call
                    response = self.ecs_client.run_task(
                        cluster=self.worker_cluster,
                        taskDefinition=self.worker_task_def_arn,
                        launchType='FARGATE',
                        networkConfiguration={
                            'awsvpcConfiguration': {
                                'subnets': self.worker_subnets,
                                'assignPublicIp': 'ENABLED'
                            }
                        },
                        overrides={
                            'containerOverrides': [
                                {
                                    'name': 'miso-app',
                                    # This is the KEY: We override the Docker CMD
                                    # to run our new "worker" script instead of the server
                                    'command': [
                                        "python", "miso_worker.py", 
                                        filename, error_message
                                    ]
                                }
                            ]
                        }
                    )
                    # print(f"  [COORDINATOR]: Task {response['tasks'][0]['taskArn']} launched.")
                    tasks_launched += 1
                
                except Exception as e:
                    print(f"  [COORDINATOR]: ERROR! Fargate 'run_task' failed for {filename}: {e}")
            
            else:
                print(f"  [COORDINATOR]: No agent available for error in {filename}: '{error_message}'")

        print(f"[COORDINATOR]: Swarm task complete. {tasks_launched} Fargate tasks launched.")
        return tasks_launched
