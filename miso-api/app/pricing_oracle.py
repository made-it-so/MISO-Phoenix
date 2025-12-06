import random
from typing import List, Dict

class PricingOracle:
    """
    Simulates the external microservice that aggregates real-time Spot Price feeds 
    from multiple cloud vendors.
    
    This client defines the required interfaces for V3 Cross-Cloud Arbitrage.
    """
    
    GLOBAL_COMPUTE_POOL = [
        {"vendor": "AWS", "region": "us-east-1", "queue_name": "miso_job_queue", "base_cost": 0.10},
        {"vendor": "AWS", "region": "us-west-2", "queue_name": "miso_job_queue_west", "base_cost": 0.09}, # Arbitrage assumption: West is cheaper
        {"vendor": "GCP", "region": "us-central1", "queue_endpoint": "https://gcp-sqs-sim/us-central1", "base_cost": 0.11},
        {"vendor": "AZURE", "region": "eastus", "queue_endpoint": "https://azure-sqs-sim/eastus", "base_cost": 0.12}
    ]

    def get_market_liquidity(self) -> List[Dict]:
        """
        Simulates retrieving current price and availability data for all major cloud providers.
        """
        # In a real V3/V4 system, this would call external HTTP APIs (GCP, Azure).
        # We simulate dynamic pricing by adding a small random factor to the base cost.
        
        market_data = []
        for provider in self.GLOBAL_COMPUTE_POOL:
            # Simulate a live cost feed fluctuation
            fluctuation = random.uniform(-0.01, 0.01)
            live_cost = provider['base_cost'] + fluctuation
            
            market_data.append({
                "vendor": provider['vendor'],
                "region": provider['region'],
                "cost_per_vCPU_min": round(live_cost, 4),
                "is_available": random.choice([True, True, True, False]) # Simulate 75% availability
            })
            
        return market_data

    def select_optimal_route(self, intent: str) -> Dict:
        """
        Determines the cheapest, available compute resource globally.
        """
        market = self.get_market_liquidity()
        
        # 1. Filter: Only use available vendors
        available = [p for p in market if p['is_available']]
        
        if not available:
            # Fallback to hardcoded US-EAST-1 if global market is down
            return {"vendor": "AWS", "region": "us-east-1", "queue_name": "miso_job_queue"} 

        # 2. Arbitrage: Find the cheapest available option
        optimal_provider = min(available, key=lambda x: x['cost_per_vCPU_min'])
        
        # 3. Return the necessary routing information
        return optimal_provider

oracle = PricingOracle()

