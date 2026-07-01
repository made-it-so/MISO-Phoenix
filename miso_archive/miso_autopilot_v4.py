import json
import time
import os

MEMORY_FILE = r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
LOCK_FILE = r"C:\Users\kyle\miso_data\miso.lock"

def update_shared_memory(course_id, topic):
    # Ensure directory exists
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    
    # Simple Windows Lock Mechanism
    for _ in range(10): # Try 10 times
        if os.path.exists(LOCK_FILE):
            time.sleep(0.2)
            continue
        
        try:
            # Create Lock
            open(LOCK_FILE, 'w').close()
            
            # Read/Write Data
            if os.path.exists(MEMORY_FILE):
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    memory = json.load(f)
            else:
                memory = {}

            memory[course_id] = {
                "kernel": topic,
                "timestamp": time.ctime(),
                "status": "ANCHORED"
            }

            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(memory, f, indent=4)
            
            # Remove Lock
            os.remove(LOCK_FILE)
            print(f"✅ [ANCHOR SUCCESS] {course_id} locked to disk.")
            return True
        except Exception as e:
            if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)
            time.sleep(0.2)
    return False

if __name__ == "__main__":
    print("🚀 MISO V4.1 [WINDOWS-LOCKED] ONLINE.")
    curriculum = [
        ("18.065", "SVD and Matrix Methods"),
        ("20.420J", "Molecular Bioengineering"),
        ("8.333", "Statistical Mechanics")
    ]
    while True:
        for cid, topic in curriculum:
            update_shared_memory(cid, topic)
            time.sleep(15)
