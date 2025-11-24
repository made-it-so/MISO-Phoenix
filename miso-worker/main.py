import time
import logging
from core import config
from core.task_queue import get_next_task
from core.execution import execute_task
from core.reporting import report_status
# PRIORITY ALPHA DIRECTIVE: Integrating Continuum Memory Subsystem.
from core.memory import continuum

logging.basicConfig(level=config.LOG_LEVEL)
log = logging.getLogger(__name__)

def main_loop():
    """Main worker loop for processing tasks."""
    log.info("MISO Worker V19.0 starting main loop.")
    log.info(f"Fast-Frequency Feedback Loop: {'ACTIVE' if config.FAST_FREQUENCY_FEEDBACK_ENABLED else 'INACTIVE'}")

    while True:
        task = get_next_task()
        if task:
            log.info(f"Executing task {task.id}...")
            result, status = execute_task(task)
            
            # --- POST-EXECUTION STEP ---
            log.info(f"Task {task.id} finished with status: {status}")
            
            # 1. Report status to Commander
            report_status(task.id, status, result)
            
            # 2. PRIORITY ALPHA DIRECTIVE: Update Continuum Memory post-execution.
            continuum.update_memory(task.id, result, status)
            log.info(f"Continuum memory updated for task {task.id}.")
            # --- END POST-EXECUTION STEP ---

        else:
            time.sleep(2) # Polling interval

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        log.info("MISO Worker shutting down.")
    except Exception as e:
        log.critical(f"FATAL ERROR in main loop: {e}", exc_info=True)
