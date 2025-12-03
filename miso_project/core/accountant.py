import boto3
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.accountant")

class CloudAccountant:
    """
    The Financial Auditor.
    Scans infrastructure for waste and calculates Arbitrage opportunities.
    """
    def __init__(self):
        # We wrap AWS clients in try/except so local testing doesn't crash without creds
        try:
            self.ec2 = boto3.client('ec2', region_name='us-east-1')
            self.pricing = boto3.client('pricing', region_name='us-east-1')
            self.cloud_active = True
        except Exception as e:
            logger.warning(f"AWS Connection Failed (Running in Local Mode): {e}")
            self.cloud_active = False

    def audit_infrastructure(self) -> Dict[str, Any]:
        """
        Scans for "Zombie" resources (On-Demand instances, Unused Volumes).
        """
        if not self.cloud_active:
            return {"error": "AWS Credentials missing or invalid."}

        logger.info(">>> AUDITING AWS INFRASTRUCTURE...")
        report = {"waste": [], "opportunities": []}
        
        try:
            # 1. Check for On-Demand Instances (The Money Pit)
            instances = self.ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
            for r in instances['Reservations']:
                for i in r['Instances']:
                    iid = i['InstanceId']
                    # Spot instances usually have an 'InstanceLifecycle' attribute = 'spot'
                    lifecycle = i.get('InstanceLifecycle', 'on-demand')
                    
                    if lifecycle == 'on-demand':
                        msg = f"Instance {iid} is ON-DEMAND. Migrate to Spot to save ~70%."
                        report["opportunities"].append(msg)

            # 2. Check for Unattached Volumes (Digital Dust)
            volumes = self.ec2.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])
            for v in volumes['Volumes']:
                size = v['Size']
                cost = size * 0.10 # Approx $0.10/GB/month
                msg = f"Unattached Volume {v['VolumeId']} ({size}GB) costing ~${cost:.2f}/mo. Delete recommended."
                report["waste"].append(msg)
                
        except Exception as e:
            return {"error": f"Audit execution failed: {e}"}

        return report

    def generate_terraform_migration(self) -> str:
        """
        CODE FIRST: Generates Infrastructure-as-Code for a cheaper Spot Fleet.
        """
        return """
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
    Name = "MISO-V85-Spot-Worker"
  }
}
"""

    def estimate_request_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """
        The Ledger: Calculates the exact cost of a thought.
        """
        # Pricing Map (Cost per 1k tokens)
        prices = {
            "gpt-4o": {"in": 0.005, "out": 0.015}, 
            "gemini-2.5-flash": {"in": 0.0001, "out": 0.0004},
            "claude-3-haiku": {"in": 0.00025, "out": 0.00125}
        }
        
        # Default to cheapest if unknown
        rate = prices.get(model, prices["gemini-2.5-flash"])
        cost = (tokens_in / 1000 * rate["in"]) + (tokens_out / 1000 * rate["out"])
        return round(cost, 6)
