import json
import os
import time
import logging
import sys

# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FED_FILE = os.path.join(BASE_DIR, "federated_state.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [FEDERATION] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class FederationHub:
    def __init__(self):
        self._ensure_db()

    def _ensure_db(self):
        if not os.path.exists(FED_FILE):
            with open(FED_FILE, 'w') as f:
                json.dump({"nodes": {}, "global_best": None, "last_update": 0}, f)

    def _load(self):
        try:
            with open(FED_FILE, 'r') as f: return json.load(f)
        except: return {"nodes": {}, "global_best": None}

    def _save(self, data):
        with open(FED_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def check_in(self, node_id, provider, region, metrics):
        data = self._load()
        
        # Update Node State
        data["nodes"][node_id] = {
            "provider": provider,
            "region": region,
            "metrics": metrics,
            "last_seen": time.time()
        }
        
        # Recalculate Global Best
        best_node = None
        lowest_score = float('inf')
        
        for nid, info in data["nodes"].items():
            price = info['metrics'].get('price', 999)
            lat = info['metrics'].get('latency', 999)
            score = price * lat
            
            if score < lowest_score:
                lowest_score = score
                best_node = nid
                
        data["global_best"] = best_node
        data["last_update"] = time.time()
        
        self._save(data)
        return data["global_best"]

    def get_world_view(self):
        return self._load()

if __name__ == "__main__":
    hub = FederationHub()
    print(json.dumps(hub.get_world_view(), indent=2))
