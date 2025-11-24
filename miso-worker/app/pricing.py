import boto3
import logging
import json
from datetime import datetime

# CONFIG
REGION = "us-east-1"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PRICING] %(message)s')
logger = logging.getLogger(__name__)

class MarketOracle:
    def __init__(self):
        # We use the EC2 client to describe spot price history
        self.ec2 = boto3.client('ec2', region_name=REGION)
        self.cache = {}
        self.last_fetch = 0

    def get_spot_prices(self):
        """
        Fetches REAL AWS Spot Instance prices.
        Mocks Azure/GCP for now (Hybrid Step).
        """
        # Cache for 60 seconds to avoid rate limits
        if time.time() - self.last_fetch < 60 and self.cache:
            return self.cache

        try:
            # Fetch price for a standard AI worker node (g4dn.xlarge)
            response = self.ec2.describe_spot_price_history(
                InstanceTypes=['g4dn.xlarge'],
                MaxResults=1,
                ProductDescriptions=['Linux/UNIX']
            )
            
            if response['SpotPriceHistory']:
                aws_price = float(response['SpotPriceHistory'][0]['SpotPrice'])
                # Normalize to "micro-dollars per second" for our internal math
                # AWS price is $/Hour. 
                # Example: -bash.50/hr = -bash.00013/sec = 130 micro-dollars/sec
                real_price_score = (aws_price / 3600) * 1000000
                
                logger.info(f"💰 REAL AWS DATA: g4dn.xlarge = ${aws_price}/hr")
            else:
                real_price_score = 150 # Fallback
            
            # Hybrid Real/Mock map
            self.cache = {
                "AWS": int(real_price_score), 
                "GCP": 140, # Mock (Competitor)
                "AZURE": 135 # Mock (Competitor)
            }
            self.last_fetch = time.time()
            return self.cache
            
        except Exception as e:
            logger.error(f"AWS Price Fetch Failed: {e}")
            return {"AWS": 150, "GCP": 140, "AZURE": 135}

import time
if __name__ == "__main__":
    m = MarketOracle()
    print(json.dumps(m.get_spot_prices(), indent=2))
