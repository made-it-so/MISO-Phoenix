# CREATED BY MISO V18 GENESIS

import os
import sys
import time
import logging

# --- Agent Configuration ---
LOOP_INTERVAL_SECONDS = 2

def setup_logging():
    """Configures the logging format and level."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - [watchdog] - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def get_cpu_load():
    """
    Retrieves the CPU load average over 1, 5, and 15 minutes.
    Returns a formatted string or an error message.
    """
    try:
        # os.getloadavg() is specific to Unix-like systems.
        load1, load5, load15 = os.getloadavg()
        return f"CPU Load (1, 5, 15 min): {load1:.2f}, {load5:.2f}, {load15:.2f}"
    except OSError as e:
        return f"Error retrieving CPU load: {e}"
    except AttributeError:
        # This will be caught if os.getloadavg() doesn't exist (e.g., on Windows)
        return "os.getloadavg() not available on this system."

def run():
    """Main execution loop for the watchdog agent."""
    setup_logging()
    logging.info("Agent starting up...")

    # Initial check for compatibility
    if not hasattr(os, 'getloadavg'):
        logging.error("This agent requires 'os.getloadavg()', which is not supported on this operating system (e.g., Windows).")
        logging.info("Agent shutting down.")
        sys.exit(1)

    logging.info(f"Monitoring CPU load every {LOOP_INTERVAL_SECONDS} seconds. Press Ctrl+C to stop.")

    try:
        while True:
            status_message = get_cpu_load()
            if "Error" in status_message or "not available" in status_message:
                logging.warning(status_message)
            else:
                logging.info(status_message)
            
            time.sleep(LOOP_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logging.info("Shutdown signal received (Ctrl+C).")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Agent has stopped.")
        sys.exit(0)

if __name__ == "__main__":
    run()