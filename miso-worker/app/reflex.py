import psutil
import time
import threading
import logging

logger = logging.getLogger('Reflex')
logger.setLevel(logging.INFO)

class SystemReflex:
    def __init__(self):
        self._stop_event = threading.Event()
        self._danger_flag = threading.Event()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.cpu_threshold = 80.0
        self.ram_threshold = 80.0

    def start(self):
        logger.info("🛡️ Reflex Sensors Activated.")
        self._thread.start()

    def _monitor_loop(self):
        """
        The 'Lizard Brain'. Runs independently of the main AI.
        Checks vitals every 0.5s.
        """
        while not self._stop_event.is_set():
            try:
                # Quick Sensor Check
                cpu = psutil.cpu_percent(interval=None) # Non-blocking
                ram = psutil.virtual_memory().percent
                
                is_dangerous = (cpu > self.cpu_threshold) or (ram > self.ram_threshold)
                
                if is_dangerous and not self._danger_flag.is_set():
                    logger.warning(f"⚠️ DANGER DETECTED: CPU {cpu}% | RAM {ram}%")
                    self._danger_flag.set() # RAISE SHIELD
                
                elif not is_dangerous and self._danger_flag.is_set():
                    logger.info(f"✅ Conditions Normalized: CPU {cpu}% | RAM {ram}%")
                    self._danger_flag.clear() # LOWER SHIELD
                    
            except Exception as e:
                logger.error(f"Sensor Failure: {e}")
            
            time.sleep(0.5)

    def is_safe(self):
        """Returns True if environment is safe to proceed."""
        return not self._danger_flag.is_set()

    def wait_for_safety(self):
        """Blocks execution until the danger clears."""
        if self._danger_flag.is_set():
            logger.warning("⛔ REFLEX OVERRIDE: Pausing execution until safety is restored...")
            # Wait until flag is cleared
            while self._danger_flag.is_set():
                time.sleep(1)
            logger.info("🟢 Resuming execution.")

