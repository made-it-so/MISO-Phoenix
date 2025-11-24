import sys
import time
import random
import logging
from federation import FederationHub

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(name)s] %(message)s')

class Observer:
    def __init__(self, name, provider, region):
        self.name = name
        self.provider = provider
        self.region = region
        self.hub = FederationHub()
        self.logger = logging.getLogger(f"OBSERVER-{name}")
        self.logger.setLevel(logging.INFO)

    def sense_environment(self):
        # Simulate Regional Differences
        base_price = 10
        base_latency = 50
        
        if self.provider == "AWS": 
            base_price = 12
            base_latency = 40 
        elif self.provider == "GCP":
            base_price = 10
            base_latency = 50
        elif self.provider == "AZURE":
            base_price = 8    
            base_latency = 80 
            
        # Add Volatility
        current_price = base_price * random.uniform(0.8, 1.5)
        current_latency = base_latency * random.uniform(0.9, 1.2)
        
        return {
            "price": int(current_price),
            "latency": int(current_latency)
        }

    def run(self):
        self.logger.info(f"📡 Deploying to {self.provider} ({self.region})...")
        
        while True:
            metrics = self.sense_environment()
            
            # Report to Hub
            global_winner = self.hub.check_in(self.name, self.provider, self.region, metrics)
            
            status = "WINNING" if global_winner == self.name else "LOSING"
            self.logger.info(f"Reported: ${metrics['price']} / {metrics['latency']}ms | Status: {status}")
            
            time.sleep(5)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python observer.py <NAME> <PROVIDER> <REGION>")
        exit(1)
    
    name, provider, region = sys.argv[1], sys.argv[2], sys.argv[3]
    agent = Observer(name, provider, region)
    agent.run()
