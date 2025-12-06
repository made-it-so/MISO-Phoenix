import threading
import time
import os
import sys

# Add the local directory to sys.path so we can import our organs
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backbone import DigitalBackbone
from sovereign import TheSovereign
from scientist import RealScientist
from architect import SovereignArchitect

class MisoOrganism:
    def __init__(self):
        print("--- INITIALIZING MISO ORGANISM V45 ---")
        
        # Instantiate Organs
        self.backbone = DigitalBackbone()
        self.sovereign = TheSovereign()
        self.scientist = RealScientist()
        self.architect = SovereignArchitect()
        
    def run(self):
        # Create Threads for simultaneous biological function
        
        # 1. THE HEART (Time & State)
        # pulses every 2s, writes state to Redis
        t_backbone = threading.Thread(target=self.backbone.pulse, daemon=True)
        
        # 2. THE STOMACH (Metabolism)
        # Taxes the system, checks wallet balance
        t_sovereign = threading.Thread(target=self.sovereign.main_loop, daemon=True)
        
        # 3. THE SUBCONSCIOUS (Dreams & Evolution)
        # Rewrites constitution when state == DREAM
        t_scientist = threading.Thread(target=self.scientist.main_loop, daemon=True)
        
        # 4. THE CORTEX (Motor Action)
        # Listens for tasks, executes shell/file operations
        t_architect = threading.Thread(target=self.architect.main_loop, daemon=True)

        print("--- ORGANISM ALIVE. STARTING THREADS. ---")
        
        t_backbone.start()
        t_sovereign.start()
        t_scientist.start()
        t_architect.start()
        
        # Keep the main thread alive to allow daemons to run
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("--- ORGANISM SHUTTING DOWN ---")

if __name__ == "__main__":
    lifeform = MisoOrganism()
    lifeform.run()
