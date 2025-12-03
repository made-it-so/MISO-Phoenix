import boto3
import logging
import json
import os
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.accountant")

class CloudAccountant:
    """
    The Financial Auditor.
    Scans infrastructure for waste and calculates Arbitrage opportunities.
    """
    def __init__(self):
        # Assumes AWS Credentials are in environment or ~/.aws/credentials
        self.ec2 = boto3.client('ec2', region_name='us-east-1') # Adjust region if needed
        self.cw = boto3.client('cloudwatch', region_name='us-east-1')
        self.pricing = boto3.client('pricing', region_name='us-east-1')

    def audit_infrastructure(self):
        """
        Scans for "Zombie" resources and expensive instances.
        """
        logger.info(">>> AUDITING AWS INFRASTRUCTURE...")
        report = {"waste": [], "opportunities": []}
        
        # 1. Check for On-Demand Instances (The Money Pit)
        instances = self.ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
        for r in instances['Reservations']:
            for i in r['Instances']:
                iid = i['InstanceId']
                lifecycle = i.get('InstanceLifecycle', 'on-demand') # Spot instances are labeled 'spot'
                
                if lifecycle == 'on-demand':
                    msg = f"Instance {iid} is ON-DEMAND. Migrate to Spot to save ~70%."
                    report["opportunities"].append(msg)
                    logger.warning(msg)

        # 2. Check for Unattached Volumes (Digital Dust)
        volumes = self.ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
        for v in volumes['Volumes']:
            cost = v['Size'] * 0.10 # Approx $0.10/GB
            msg = f"Unattached Volume {v['VolumeId']} ({v['Size']}GB) costing ~${cost}/mo. Delete recommended."
            report["waste"].append(msg)
            logger.warning(msg)

        return report

    def generate_terraform_migration(self):
        """
        CODE FIRST: Generates the Infrastructure-as-Code to run MISO cheaper.
        """
        tf_code = """
provider "aws" {
  region = "us-east-1"
}

# The MISO Spot Fleet Request
resource "aws_spot_instance_request" "miso_worker" {
  ami           = "ami-0c7217cdde317cfec" # Ubuntu 22.04 LTS
  instance_type = "t3.medium"
  spot_price    = "0.015" # Max price willing to pay
  wait_for_fulfillment = true
  
  tags = {
    Name = "MISO-V84-Spot-Worker"
  }
  
  # User data to auto-clone and start MISO
  user_data = <<-EOF
              #!/bin/bash
              git clone https://github.com/made-it-so/MISO-Phoenix.git
              cd MISO-Phoenix
              pip install -r requirements.txt
              python3 main.py
              EOF
}
"""
        return tf_code

    def estimate_request_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """
        The Ledger: Calculates the exact cost of a thought.
        """
        # Pricing Map (Update dynamically in future)
        prices = {
            "gpt-4o": {"in": 0.005, "out": 0.015}, # per 1k
            "gemini-2.5-flash": {"in": 0.0001, "out": 0.0004}, # per 1k
            "claude-3-haiku": {"in": 0.00025, "out": 0.00125}
        }
        
        rate = prices.get(model, prices["gemini-2.5-flash"])
        cost = (tokens_in / 1000 * rate["in"]) + (tokens_out / 1000 * rate["out"])
        return round(cost, 6)
