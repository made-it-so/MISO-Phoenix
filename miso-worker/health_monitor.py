import psutil
import logging
import time
import os

# --- Configuration ---
CPU_THRESHOLD = 90.0  # Percent
MEMORY_THRESHOLD = 90.0  # Percent
CHECK_INTERVAL = 60  # Seconds
# Log file will be created in the same directory as the script
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'health_monitor.log')

# --- Logger Setup ---
def setup_logger():
    """Sets up the logger to log to a file and console."""
    logger = logging.getLogger('HealthMonitor')
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if the script is reloaded in some context
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Console Handler (for immediate feedback if run interactively)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logger()

# --- Core Functions ---
def check_system_resources():
    """Checks CPU and Memory usage and logs a warning if they exceed thresholds."""
    try:
        # Get CPU usage over a 1-second interval
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Get virtual memory (RAM) usage
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        logger.info(f"Current Usage - CPU: {cpu_usage:.2f}%, Memory: {memory_usage:.2f}%")

        if cpu_usage > CPU_THRESHOLD:
            logger.warning(
                f"HIGH CPU USAGE DETECTED! Usage: {cpu_usage:.2f}%, Threshold: {CPU_THRESHOLD:.2f}%"
            )

        if memory_usage > MEMORY_THRESHOLD:
            logger.warning(
                f"HIGH MEMORY USAGE DETECTED! Usage: {memory_usage:.2f}%, Threshold: {MEMORY_THRESHOLD:.2f}%"
            )

    except Exception as e:
        logger.error(f"An error occurred while checking system resources: {e}", exc_info=True)

# --- Main Execution Loop ---
if __name__ == "__main__":
    logger.info("System Health Monitor started.")
    try:
        while True:
            check_system_resources()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logger.info("System Health Monitor stopped by user.")
    except Exception as e:
        logger.critical(f"Health Monitor encountered a fatal error and is shutting down: {e}", exc_info=True)
