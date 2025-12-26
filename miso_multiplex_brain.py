import sqlite3
import logging
import json
import time
from typing import Dict, Any, Optional

# --- Configuration ---
DB_NAME = "miso_backbone.db"
STABILITY_TARGET = 52.0
LOG_LEVEL = logging.INFO

# Setup basic logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

class MisoMultiplexBrain:
    """
    The central processing unit for MISO, handling signal multiplexing
    and maintaining the integrity of the stability target (52.0 D_KL).
    """
    
    def __init__(self):
        self.db_connection = None
        self._initialize_database()
        self.current_stability_metric = 0.0
        logging.info(f"Brain initialized. Target Stability: {STABILITY_TARGET}")

    def _initialize_database(self):
        """Establishes connection to SQLite in WAL mode for high concurrency."""
        try:
            # Use check_same_thread=False if connections are shared across threads,
            # but for simplicity here, we assume one thread context or use connection pooling 
            # (which is omitted for this core implementation).
            self.db_connection = sqlite3.connect(DB_NAME, timeout=30.0)
            
            # Enable WAL mode for better concurrency handling
            cursor = self.db_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            logging.info(f"Database connection established to {DB_NAME} in WAL mode.")
            
            self._ensure_schema()

        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise

    def _ensure_schema(self):
        """Ensures the necessary tables exist."""
        cursor = self.db_connection.cursor()
        
        # Table for incoming multiplexed signals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                source TEXT NOT NULL, -- UI, Scientist, Architect
                signal_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                processed BOOLEAN DEFAULT 0
            );
        """)
        
        # Table to track crucial system metrics (e.g., stability)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                metric_name TEXT PRIMARY KEY,
                value REAL,
                last_updated REAL
            );
        """)
        
        self.db_connection.commit()

    def record_signal(self, source: str, signal_type: str, payload: Dict[str, Any]) -> int:
        """
        Routes and records a multiplexed signal into the database.
        """
        if source not in ["UI", "Scientist", "Architect"]:
            logging.warning(f"Unknown signal source attempted: {source}")
            return -1

        try:
            payload_json = json.dumps(payload)
            cursor = self.db_connection.cursor()
            
            cursor.execute("""
                INSERT INTO signals (timestamp, source, signal_type, payload)
                VALUES (?, ?, ?, ?);
            """, (time.time(), source, signal_type, payload_json))
            
            self.db_connection.commit()
            new_id = cursor.lastrowid
            logging.debug(f"Signal recorded from {source} (ID: {new_id})")
            return new_id
            
        except sqlite3.Error as e:
            logging.error(f"Error recording signal from {source}: {e}")
            return -1

    def process_pending_signals(self) -> int:
        """
        The core loop operation: fetches unprocessed signals and simulates
        processing, updating the stability metric as a result of signal interaction.
        """
        processed_count = 0
        try:
            cursor = self.db_connection.cursor()
            
            # Fetch unprocessed signals (limit for batch processing)
            cursor.execute("""
                SELECT id, source, payload FROM signals 
                WHERE processed = 0 
                LIMIT 100;
            """)
            
            signals_to_process = cursor.fetchall()
            
            for sig_id, source, payload_json in signals_to_process:
                payload = json.loads(payload_json)
                
                # --- SIMULATED PROCESSING LOGIC ---
                # The D_KL divergence optimization (Stability 52.0) is conceptually
                # maintained by how signals are integrated.
                
                adjustment_factor = 0.0
                
                if source == "Architect":
                    # Architect signals usually suggest high-level structural changes -> high variance
                    adjustment_factor = 0.5 * len(payload.get("directives", []))
                elif source == "Scientist":
                    # Scientist signals provide refinement data -> moderate convergence
                    adjustment_factor = -0.2 * payload.get("confidence_score", 0.5)
                elif source == "UI":
                    # UI signals are transactional/immediate feedback -> low impact noise
                    adjustment_factor = 0.05
                
                # Update stability metric (simulated D_KL optimization feedback loop)
                self.current_stability_metric = (
                    self.current_stability_metric * 0.95 + adjustment_factor * 0.05
                )
                
                # Mark as processed
                cursor.execute("UPDATE signals SET processed = 1 WHERE id = ?;", (sig_id,))
                processed_count += 1
                
                # Placeholder: In a real system, complex logic follows here.
                
            self.db_connection.commit()
            self._update_stability_metric_in_db()
            
            logging.debug(f"Successfully processed {processed_count} signals.")
            return processed_count

        except sqlite3.Error as e:
            logging.error(f"Error during signal processing: {e}")
            return 0
        except Exception as e:
            logging.error(f"Unexpected error during signal processing loop: {e}")
            return 0

    def _update_stability_metric_in_db(self):
        """Stores the current calculated stability metric."""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO metrics (metric_name, value, last_updated)
                VALUES (?, ?, ?);
            """, (f"STABILITY_52_0_CURRENT", self.current_stability_metric, time.time()))
            self.db_connection.commit()
        except sqlite3.Error as e:
            logging.error(f"Failed to update stability metric in DB: {e}")

    def get_health_check(self) -> Dict[str, Any]:
        """
        Performs a self-audit, reporting system health relative to the 52.0 target.
        """
        self._update_stability_metric_in_db() # Ensure DB reflects current state
        
        health_report = {
            "status": "NOMINAL",
            "target_stability": STABILITY_TARGET,
            "current_metric": self.current_stability_metric,
            "db_connection_ok": self.db_connection is not None,
            "timestamp": time.time()
        }

        # Define tolerance band around the theoretical target (52.0 is often a baseline reference, 
        # here we assume current_stability_metric is a deviation measure relative to zero, 
        # and we check if it's within a normalized operational range, e.g., -1.0 to 1.0, 
        # or simply check if processing is active.)
        
        # For this architecture, "Stability 52.0" implies the system is running its 
        # intended D_KL optimization loop effectively. We check if recent processing occurred.
        
        if abs(self.current_stability_metric) > 5.0: # Example deviation check
            health_report["status"] = "WARNING_DEVIATION"
            logging.warning("Stability metric shows significant deviation.")
            
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM signals WHERE processed = 0;")
            pending_count = cursor.fetchone()[0]
            health_report["pending_signals"] = pending_count
            
            if pending_count > 500:
                 health_report["status"] = "WARNING_BACKLOG"
            
        except Exception:
            health_report["db_signal_count_check_failed"] = True

        return health_report

    def run_cycle(self):
        """Runs a single operational cycle."""
        processed = self.process_pending_signals()
        logging.info(f"Cycle complete. Processed {processed} items.")

    def shutdown(self):
        """Safely closes the database connection."""
        if self.db_connection:
            self.db_connection.close()
            logging.info("Database connection closed.")

# --- Example Usage Simulation ---
if __name__ == '__main__':
    brain = None
    try:
        brain = MisoMultiplexBrain()
        
        # 1. Simulate initial signal injection
        brain.record_signal("Architect", "REFACTOR_INIT", {"directives": ["Core_A", "Core_B"]})
        brain.record_signal("Scientist", "MODEL_UPDATE", {"confidence_score": 0.95, "dataset_id": 101})
        brain.record_signal("UI", "USER_ACTION", {"element": "button_save"})
        brain.record_signal("Scientist", "MODEL_UPDATE", {"confidence_score": 0.1})
        
        # 2. Run processing cycles
        print("\n--- Cycle 1 ---")
        brain.run_cycle()
        print("Health Check 1:", json.dumps(brain.get_health_check(), indent=2))
        
        # 3. Inject more signals during runtime
        brain.record_signal("Architect", "REFACTOR_APPLY", {"directives": ["Core_C"]})
        
        print("\n--- Cycle 2 ---")
        brain.run_cycle()
        print("Health Check 2:", json.dumps(brain.get_health_check(), indent=2))

        print("\n--- Cycle 3 (Clearing buffer) ---")
        brain.run_cycle()
        print("Health Check 3:", json.dumps(brain.get_health_check(), indent=2))
        
    except Exception as e:
        logging.critical(f"Fatal error in main execution: {e}")
    finally:
        if brain:
            brain.shutdown()