import redis
import time
import sys

# TARGET: LIVE CONTROL PLANE
REDIS_HOST = "miso-msd-cache.me5spp.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379

def monitor():
    print(f"--- MISO PHOENIX MONITORING STATION ---")
    print(f"Target: {REDIS_HOST}")
    print("Waiting for Agent Telemetry... (Ctrl+C to exit)\n")
    
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
        # Start by reading the whole log to catch up
        logs = r.lrange('miso:backbone:logs', 0, -1)
        last_log_len = len(logs)
        
        # Print last 10 lines for context
        for entry in logs[-10:]:
            print(entry)
            
        while True:
            logs = r.lrange('miso:backbone:logs', 0, -1)
            current_len = len(logs)
            
            if current_len > last_log_len:
                new_entries = logs[last_log_len:]
                for entry in new_entries:
                    print(f">> {entry}")
                last_log_len = current_len
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nMonitoring session closed.")
        sys.exit(0)
    except Exception as e:
        print(f"Connection lost: {e}")

if __name__ == "__main__":
    monitor()
