import json
import time
import os

MEMORY_FILE = "miso_shared_buffer.json"

def update_shared_memory(course, kernel):
    # Load existing memory
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            memory = json.load(f)
    else:
        memory = {}

    # Inject new HLE logic
    memory[course] = {
        "kernel": kernel,
        "timestamp": time.time(),
        "status": "Verified"
    }

    # Save back to shared buffer
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=4)
    print(f"[📂] Shared Buffer Updated: {course}")

if __name__ == "__main__":
    # Example ingestion loop
    while True:
        update_shared_memory("Course 18", "Probabilistic Proofs")
        time.sleep(10)
