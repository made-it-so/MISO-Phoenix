import sqlite3
import time
import logging
import json
import threading
import subprocess
import os
from datetime import datetime

# --- Configuration ---
DB_NAME = "miso_backbone.db"
LOG_FILE = "miso_sync_kernel.log"
HEARTBEAT_INTERVAL = 10  # Seconds
STABILITY_THRESHOLD = 52.0
BRAIN_MODULE = "miso_multiplex_brain"
MUSCLE_MODULE = "miso_bio_muscle"

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# --- Database Management ---

class MisoDB:
    """Handles SQLite operations and schema setup for the backbone."""
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect_and_configure()
        self._setup_schema()

    def _connect_and_configure(self):
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.cursor = self.conn.cursor()
            logging.info(f"Database connected and WAL mode enabled: {self.db_name}")
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            raise

    def _setup_schema(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    timestamp TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    data_hash TEXT UNIQUE NOT NULL,
                    divergence REAL,
                    payload_json TEXT
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    timestamp TEXT PRIMARY KEY,
                    target TEXT NOT NULL,
                    command_id TEXT UNIQUE NOT NULL,
                    status TEXT,
                    parameters_json TEXT
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    timestamp TEXT PRIMARY KEY,
                    process_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL,
                    UNIQUE(timestamp, process_id, metric_name)
                )
            """)
            self.conn.commit()
            logging.info("Database schema initialized or verified.")
        except Exception as e:
            logging.error(f"Schema setup error: {e}")
            raise

    def execute(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return self.cursor
        except Exception as e:
            logging.error(f"DB execution error: {query[:50]}... | Error: {e}")
            self.conn.rollback()
            return None

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed.")

# --- Process Management & Resilience ---

class ProcessController:
    """Manages the lifecycle and health monitoring of external Python processes."""
    def __init__(self, module_name, db_instance):
        self.module_name = module_name
        self.db = db_instance
        self.process = None
        self.is_running = False
        self.start_time = None
        self.process_name = f"{module_name}.py"

    def start(self):
        if self.is_running:
            logging.warning(f"{self.process_name} is already running.")
            return

        logging.info(f"Attempting to start {self.process_name}...")
        try:
            # Execute as a separate Python process
            self.process = subprocess.Popen(
                ['python', self.module_name + '.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.is_running = True
            self.start_time = time.time()
            logging.info(f"{self.process_name} started successfully (PID: {self.process.pid}).")
        except FileNotFoundError:
            logging.error(f"Python executable not found. Ensure Python is in PATH.")
            self.is_running = False
        except Exception as e:
            logging.error(f"Failed to start {self.process_name}: {e}")
            self.is_running = False

    def terminate(self):
        if self.is_running and self.process and self.process.poll() is None:
            logging.warning(f"Terminating {self.process_name} (PID: {self.process.pid}).")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.is_running = False
            self.process = None
            logging.info(f"{self.process_name} terminated.")

    def check_health(self):
        if not self.is_running:
            return False, f"{self.process_name} is stopped."
        
        # Check if process is still alive (non-blocking poll)
        if self.process.poll() is not None:
            logging.error(f"{self.process_name} terminated unexpectedly. Return code: {self.process.returncode}")
            self.is_running = False
            self.process = None
            # Read final output for debugging if terminated
            stdout, stderr = self.process.communicate()
            logging.error(f"{self.process_name} STDOUT: {stdout.strip()}")
            logging.error(f"{self.process_name} STDERR: {stderr.strip()}")
            return False, f"{self.process_name} crashed."
        
        return True, "OK"

    def restart(self):
        self.terminate()
        # Give a brief pause before restarting to prevent rapid cycling
        time.sleep(1)
        self.start()

# --- Orchestrator Core ---

class MisoSyncKernel:
    def __init__(self):
        logging.info("Kernel initialization started.")
        self.db = MisoDB(DB_NAME)
        
        # Initialize process controllers
        self.brain_ctrl = ProcessController(BRAIN_MODULE, self.db)
        self.muscle_ctrl = ProcessController(MUSCLE_MODULE, self.db)
        
        self._running = True
        self.heartbeat_thread = None

    def _initialize_system(self):
        """Start required components upon kernel boot."""
        self.brain_ctrl.start()
        self.muscle_ctrl.start()
        logging.info("System initialization complete. Starting heartbeat loop.")

    def _audit_dkldivergence(self):
        """Fetches the latest D_KL divergence from the signals table."""
        query = """
            SELECT divergence FROM signals
            WHERE divergence IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 1
        """
        result = self.db.fetchone(query)
        
        if result and result[0] is not None:
            latest_divergence = result[0]
            logging.info(f"Latest D_KL Divergence: {latest_divergence:.4f}")
            return latest_divergence
        else:
            logging.warning("No recent D_KL divergence data found in signals table.")
            return None

    def _check_and_record_stability(self, current_stability):
        """Records stability metric and triggers resilience check."""
        timestamp = datetime.now().isoformat()
        
        # Record Telemetry
        self.db.execute("""
            INSERT OR REPLACE INTO telemetry (timestamp, process_id, metric_name, value)
            VALUES (?, ?, ?, ?)
        """, (timestamp, "KERNEL", "CURRENT_STABILITY", current_stability))

        if current_stability < STABILITY_THRESHOLD:
            logging.error(f"Stability ({current_stability:.2f}%) below threshold ({STABILITY_THRESHOLD:.2f}%). Initiating recovery sequence.")
            self._handle_instability(current_stability)
            return False
        
        logging.info(f"System Stability Check: {current_stability:.2f}% (Threshold: {STABILITY_THRESHOLD:.2f}%)")
        return True

    def _handle_instability(self, stability):
        """Auto-restart Brain/Muscle components if stability drops."""
        
        # Aggressive restart strategy for kernel instability
        
        brain_ok, _ = self.brain_ctrl.check_health()
        muscle_ok, _ = self.muscle_ctrl.check_health()

        if not brain_ok:
            logging.warning("Brain appears failed. Attempting restart.")
            self.brain_ctrl.restart()
            
        if not muscle_ok:
            logging.warning("Muscle appears failed. Attempting restart.")
            self.muscle_ctrl.restart()
            
        # Re-check after restart attempts
        new_brain_ok, _ = self.brain_ctrl.check_health()
        new_muscle_ok, _ = self.muscle_ctrl.check_health()
        
        if new_brain_ok and new_muscle_ok:
            logging.info("Components successfully restarted.")
        else:
            logging.error("Component restart failed or processes are still unhealthy.")

    def _heartbeat_loop(self):
        """The core monitoring pulse."""
        while self._running:
            start_time = time.time()
            logging.debug("Executing Kernel Heartbeat Pulse...")
            
            # 1. Process Health Check
            brain_ok, brain_msg = self.brain_ctrl.check_health()
            muscle_ok, muscle_msg = self.muscle_ctrl.check_health()
            
            # Calculate rudimentary stability based on process health (Placeholder: Real stability derived from D_KL)
            health_score = 100.0
            if not brain_ok: health_score -= 30
            if not muscle_ok: health_score -= 30
            
            # 2. D_KL Audit (Primary Metric)
            divergence = self._audit_dkldivergence()
            
            # Combine metrics for final stability score (Simple representation)
            final_stability = health_score
            if divergence is not None:
                # Simple mapping: High divergence -> Low stability
                # Assuming 'good' divergence is low, e.g., 0.0. Let's scale it inversely.
                # For simplicity here, we use the health score unless D_KL forces a drop below 52.0
                if divergence > 0.5: # Example threshold for bad divergence
                     final_stability = min(final_stability, 30.0) 

            # 3. Stability Check and Resilience Trigger
            self._check_and_record_stability(final_stability)

            # 4. Wait for the next interval
            elapsed = time.time() - start_time
            sleep_time = max(0, HEARTBEAT_INTERVAL - elapsed)
            time.sleep(sleep_time)

    def run(self):
        """Starts the kernel orchestration services."""
        try:
            self._initialize_system()
            
            # Start heartbeat in a separate thread so the main thread can handle SIGINT/SIGTERM
            self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self.heartbeat_thread.start()
            
            # Keep the main thread alive until shutdown signal
            while self._running:
                time.sleep(1)

        except KeyboardInterrupt:
            logging.info("Kernel received shutdown signal (KeyboardInterrupt).")
        except Exception as e:
            logging.critical(f"Kernel encountered a fatal error: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully stops all components."""
        logging.info("Starting MisoSyncKernel shutdown sequence.")
        self._running = False
        
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            self.heartbeat_thread.join(timeout=2)
            if self.heartbeat_thread.is_alive():
                logging.warning("Heartbeat thread did not terminate gracefully.")
        
        self.brain_ctrl.terminate()
        self.muscle_ctrl.terminate()
        self.db.close()
        logging.info("MisoSyncKernel shutdown complete.")

if __name__ == "__main__":
    # --- Mock Environment Setup (Required for kernel execution) ---
    # Create dummy companion files if they don't exist for testing purposes
    
    if not os.path.exists(BRAIN_MODULE + ".py"):
        logging.warning(f"Creating dummy {BRAIN_MODULE}.py for testing.")
        with open(BRAIN_MODULE + ".py", "w") as f:
            f.write("""
import time, random, sqlite3, os, json
DB = "miso_backbone.db"
def run_brain():
    conn = sqlite3.connect(DB, check_same_thread=False)
    cursor = conn.cursor()
    i = 0
    while True:
        try:
            # Simulate generating signals and divergence
            divergence = abs(random.gauss(0.1, 0.3)) 
            payload = {"temp_setpoint": 22.5 + random.uniform(-0.1, 0.1)}
            
            signal_data = (time.strftime('%Y-%m-%d %H:%M:%S'), "BRAIN_CORE", hash(time.time()), divergence, json.dumps(payload))
            cursor.execute("INSERT OR IGNORE INTO signals VALUES (?, ?, ?, ?, ?)", signal_data)
            conn.commit()
            
            # Simulate crash based on high divergence
            if divergence > 0.8:
                print("BRAIN: Simulating self-termination due to high divergence.")
                exit(1) 
                
            time.sleep(4) # Send data less frequently than heartbeat
            i += 1
        except Exception as e:
            print(f"BRAIN ERROR: {e}")
            break
    conn.close()

if __name__ == "__main__":
    print("Miso Brain Starting...")
    run_brain()
""")

    if not os.path.exists(MUSCLE_MODULE + ".py"):
        logging.warning(f"Creating dummy {MUSCLE_MODULE}.py for testing.")
        with open(MUSCLE_MODULE + ".py", "w") as f:
            f.write("""
import time, sqlite3, os, json
DB = "miso_backbone.db"
def run_muscle():
    conn = sqlite3.connect(DB, check_same_thread=False)
    cursor = conn.cursor()
    while True:
        try:
            # Check for incoming actions (simulated fetch from another source, here we just insert dummy data)
            action_id = f"ACT_{int(time.time() * 1000)}"
            params = {"motor_id": 1, "power": 0.85}
            
            action_data = (time.strftime('%Y-%m-%d %H:%M:%S'), "MOTOR_ARRAY_1", action_id, "PENDING", json.dumps(params))
            cursor.execute("INSERT OR IGNORE INTO actions VALUES (?, ?, ?, ?, ?)", action_data)
            conn.commit()
            
            time.sleep(5)
        except Exception as e:
            print(f"MUSCLE ERROR: {e}")
            break
    conn.close()

if __name__ == "__main__":
    print("Miso Muscle Starting...")
    run_muscle()
""")

    # --- Execution ---
    kernel = MisoSyncKernel()
    try:
        kernel.run()
    except Exception as e:
        logging.critical(f"Kernel execution failed: {e}")
    finally:
        # Ensure kernel cleans up regardless of how run() exits
        if kernel.db:
            kernel.db.close()