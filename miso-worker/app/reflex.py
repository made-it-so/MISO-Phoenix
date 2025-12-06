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

    def start(self):
        logger.info("🛡️ Reflex Sensors Activated.")
        self._thread.start()

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            try:
                cpu = psutil.cpu_percent(interval=None)
                if cpu > self.cpu_threshold and not self._danger_flag.is_set():
                    logger.warning(f"⚠️ DANGER: High CPU ({cpu}%). Raising Shield.")
                    self._danger_flag.set()
                elif cpu <= self.cpu_threshold and self._danger_flag.is_set():
                    logger.info("✅ CPU Normalized. Lowering Shield.")
                    self._danger_flag.clear()
            except: pass
            time.sleep(0.5)

    def wait_for_safety(self):
        if self._danger_flag.is_set():
            logger.warning("⛔ REFLEX BLOCK: Pausing for safety...")
            while self._danger_flag.is_set():
                time.sleep(1)
