import boto3
import logging
from datetime import datetime, timedelta
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.market")

class MarketTicker:
    """
    The Bloomberg Terminal for Compute.
    Fetches live Spot Instance prices across regions.
    """
    def __init__(self):
        # We check a few strategic regions for arbitrage opportunities
        self.regions = ['us-east-1', 'us-east-2', 'us-west-2', 'eu-west-1']
        self.clients = {}
        self._init_clients()

    def _init_clients(self):
        for region in self.regions:
            try:
                self.clients[region] = boto3.client('ec2', region_name=region)
            except:
                pass # Region unavailable or creds missing

    def get_spot_prices(self, instance_type: str = "t3.medium") -> List[Dict]:
        """Finds the cheapest region for a specific body type."""
        logger.info(f"Querying Spot Market for {instance_type}...")
        opportunities = []
        
        for region, client in self.clients.items():
            try:
                # Check price history for last hour
                response = client.describe_spot_price_history(
                    InstanceTypes=[instance_type],
                    ProductDescriptions=['Linux/UNIX'],
                    StartTime=datetime.now() - timedelta(hours=1)
                )
                
                if response['SpotPriceHistory']:
                    # Get latest price
                    latest = response['SpotPriceHistory'][0]
                    price = float(latest['SpotPrice'])
                    opportunities.append({
                        "region": region,
                        "price": price,
                        "zone": latest['AvailabilityZone']
                    })
            except Exception as e:
                logger.warning(f"Market access failed for {region}: {e}")

        # Sort by price (Cheapest first)
        opportunities.sort(key=lambda x: x['price'])
        return opportunities

    def get_best_bid(self) -> Dict:
        """Returns the single best arbitrage opportunity."""
        market_data = self.get_spot_prices()
        if market_data:
            best = market_data[0]
            logger.info(f"Arbitrage Opportunity: {best['region']} @ ${best['price']}/hr")
            return best
        return {"region": "us-east-1", "price": 0.03} # Fallback to on-demand estimate
