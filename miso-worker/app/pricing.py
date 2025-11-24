import random
import logging

logger = logging.getLogger(__name__)

class MarketOracle:
    """
    Simulates a Real-Time Spot Market.
    In V14, this would connect to the AWS Price List API / Azure Retail Rates API.
    """
    def __init__(self):
        # Base prices in micro-dollars (-bash.0001) per ms of compute
        self.base_rates = {
            "GCP": 10,
            "AZURE": 5,  # Azure is 50% cheaper base
            "AWS": 15    # AWS is premium
        }

    def get_spot_prices(self):
        """
        Returns current market rates. 
        Simulates 'Surge Pricing' based on random volatility.
        """
        prices = {}
        
        # GCP has high volatility (Surge pricing up to 3x)
        gcp_surge = random.choice([1, 1, 1, 3]) # 25% chance of surge
        prices["GCP"] = self.base_rates["GCP"] * gcp_surge
        
        # Azure is stable but occasionally drops (Flash Sale)
        azure_discount = random.choice([1, 1, 0.8]) 
        prices["AZURE"] = self.base_rates["AZURE"] * azure_discount
        
        # AWS is flat
        prices["AWS"] = self.base_rates["AWS"]
        
        # Log surges for audit visibility
        if gcp_surge > 1:
            logger.warning(f"📈 MARKET SURGE: GCP Price spiked to {prices['GCP']}!")
        
        return prices
