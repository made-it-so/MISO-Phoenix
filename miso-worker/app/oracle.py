import logging
import json
import os
import time
import random
import sys

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MARKET_HISTORY_FILE = os.path.join(BASE_DIR, "market_history.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ORACLE] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class Oracle:
    def __init__(self):
        self.history = []
        self.load_history()

    def load_history(self):
        if os.path.exists(MARKET_HISTORY_FILE):
            try:
                with open(MARKET_HISTORY_FILE, 'r') as f: self.history = json.load(f)
            except: self.history = []

    def ingest_price(self, provider, price):
        """Record a data point"""
        self.history.append({
            "timestamp": time.time(),
            "provider": provider,
            "price": price
        })
        # Keep last 100 points
        if len(self.history) > 100: self.history.pop(0)
        
        with open(MARKET_HISTORY_FILE, 'w') as f:
            json.dump(self.history, f)

    def predict_trend(self, provider):
        """
        Simple Moving Average Crossover to predict near-future price.
        Returns: 'RISING', 'FALLING', or 'STABLE'
        """
        data = [x['price'] for x in self.history if x['provider'] == provider]
        if len(data) < 5: return "UNKNOWN"
        
        short_ma = sum(data[-3:]) / 3
        long_ma = sum(data[-10:]) / 10 if len(data) >= 10 else short_ma
        
        if short_ma > long_ma * 1.1: return "RISING 📈"
        if short_ma < long_ma * 0.9: return "FALLING 📉"
        return "STABLE ➡️"

    def advise_execution(self, provider):
        trend = self.predict_trend(provider)
        if "FALLING" in trend:
            return "WAIT (Price dropping)"
        elif "RISING" in trend:
            return "RUSH (Price spiking)"
        else:
            return "EXECUTE (Stable)"

if __name__ == "__main__":
    oracle = Oracle()
    # Simulate a price drop
    logger.info("🔮 Oracle gazing into the future...")
    for p in [100, 90, 80, 70, 60]: 
        oracle.ingest_price("AWS", p)
        
    advice = oracle.advise_execution("AWS")
    logger.info(f"🔮 Prediction for AWS: {advice}")
