import os
import shutil
import sys
import random
from datetime import datetime

# --- BIOLOGICAL CONSTRAINT ---
# Telomere limit: Prevents infinite recursion (Fork Bomb)
MAX_GENERATION = 1

def mitose():
    current_dir = os.path.abspath(".")
    parent_name = os.path.basename(current_dir)
    
    # Check Telomeres
    if "Gen" in parent_name:
        print(f"MITOSIS FAILED: Telomeres depleted. Current generation ({parent_name}) cannot reproduce.")
        return

    # Create Offspring
    new_name = f"MISO-Gen{random.randint(100,999)}"
    new_path = os.path.join(os.path.dirname(current_dir), new_name)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] INITIATING MITOSIS...")
    print(f"TARGET: {new_path}")
    
    try:
        # Copy the organism
        shutil.copytree(current_dir, new_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.venv', '__pycache__', '*.log'))
        
        print(f"SUCCESS: Organism replicated to {new_name}")
        print(f"NEXT STEP: cd ../{new_name} && python3 miso-worker/app/worker.py")
        
    except Exception as e:
        print(f"MITOSIS FAILED: {e}")

if __name__ == "__main__":
    mitose()
