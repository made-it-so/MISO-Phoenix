import json
import time
import os

MEMORY_FILE = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
LOCK_FILE = r"C:\Users\kyle\miso_data\miso.lock"

def sovereign_harvest(node_block, kernel_data):
    for _ in range(10):
        if os.path.exists(LOCK_FILE):
            time.sleep(0.1)
            continue
        try:
            open(LOCK_FILE, 'w').close()
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                memory = json.load(f)

            memory[f"HLE_{node_block}"] = {
                "content": kernel_data,
                "kernel_ver": "v128",
                "derivation": "MacLane-Langevin-Palmyrene",
                "timestamp": time.ctime()
            }

            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=4)
            
            os.remove(LOCK_FILE)
            print(f"📦 [HARVEST SUCCESS] Node Block {node_block} anchored.")
            return True
        except Exception:
            if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
            time.sleep(0.1)
    return False

if __name__ == "__main__":
    sovereign_harvest("2201-2300", "Topological Category Theory and Stochastic Bio-Dynamics")
