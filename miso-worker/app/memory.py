import json
import os
import time

class Hippocampus:
    def __init__(self):
        # Shard memory by Process ID for thread safety in Hive Mode
        self.pid = os.getpid()
        self.memory_file = f"miso_memory_{self.pid}.json"
        
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f: json.dump([], f)
        print(f">> 🧠 HIPPOCAMPUS ONLINE (Shard: {self.pid})")

    def remember(self, prompt, result):
        entry = {
            "timestamp": time.time(),
            "pid": self.pid,
            "prompt": prompt,
            "result": result
        }
        try:
            # Atomic append (safer)
            with open(self.memory_file, 'r+') as f:
                data = json.load(f)
                data.append(entry)
                f.seek(0)
                json.dump(data, f, indent=2)
        except: pass

    def recall(self, query):
        # In Hive Mode, recall is local-only for speed. 
        # Global knowledge comes from the Constitution (updated by Sleep Cycle).
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            matches = [m for m in data if any(w in m['prompt'] for w in query.split())]
            return json.dumps(matches[-3:] if matches else [])
        except: return "NO PRECEDENT."
