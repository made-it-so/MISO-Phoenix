import boto3
import json
import time
import logging
import statistics
import os

# CONFIG
DYNAMO_TABLE = "miso_replay_buffer"
REGION = "us-east-1"
# Robust Path finding
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [OPTIMIZER] %(message)s')
logger = logging.getLogger(__name__)

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(DYNAMO_TABLE)

def calculate_volatility():
    try:
        response = table.scan(Limit=20)
        items = response.get('Items', [])
        if len(items) < 5: return 0.1
        durations = [float(i.get('duration_ms', 0)) for i in items]
        if not durations: return 0.1
        mean = statistics.mean(durations)
        if mean == 0: return 0
        return statistics.stdev(durations) / mean
    except: return 0.1

def update_hyperparameters(volatility):
    try:
        # Read
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Meta-Learning Logic
        # If volatility is high (> 0.5), we panic and increase exploration
        new_epsilon = max(0.01, min(0.50, volatility))
        
        config["EPSILON"] = round(new_epsilon, 4)
        config["MODE"] = "VOLATILE 🌊" if volatility > 0.5 else "STABLE 🗿"
        
        # Write
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
            
        return config["EPSILON"], config["MODE"]
    except Exception as e:
        logger.error(f"IO Error: {e}")
        return 0.15, "ERROR"

if __name__ == "__main__":
    logger.info(f"🧠 Meta-Optimizer Online. Config Path: {CONFIG_FILE}")
    while True:
        vol = calculate_volatility()
        eps, mode = update_hyperparameters(vol)
        logger.info(f"Market Volatility: {vol:.2f} | New Learning Rate: {eps*100:.1f}% | {mode}")
        time.sleep(5)
