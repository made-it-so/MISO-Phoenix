import sqlite3
import json
import asyncio
from typing import Dict, Any, Optional, List

# --- Configuration Constants ---
DB_PATH = "miso_backbone.db"
STABILITY_TARGET = 52.0
TASK_QUEUE_TABLE = "task_queue"
STATE_TABLE = "task_states"

class MuscleExecutionError(Exception):
    """Custom exception for muscle execution failures."""
    pass

class MisoMuscle:
    """
    The Muscle component of the MISO architecture.
    Responsible for executing bio-generation tasks, managing state transitions,
    and ensuring stability alignment via asynchronous processing.
    """
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = asyncio.Lock()
        print(f"MisoMuscle Initialized. Target Stability: {STABILITY_TARGET}")

    def _initialize_db(self):
        """Ensures necessary tables exist in the SQLite backbone."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Task Queue: For tasks waiting to be processed
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {TASK_QUEUE_TABLE} (
                    task_id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'QUEUED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Task States: For tracking detailed state transitions and metrics
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {STATE_TABLE} (
                    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    data_json TEXT,
                    stability_metric REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(task_id) REFERENCES {TASK_QUEUE_TABLE}(task_id)
                )
            """)
            conn.commit()

    async def _get_db_connection(self) -> sqlite3.Connection:
        """Provides a thread-safe, async-friendly connection context."""
        # Note: SQLite is inherently blocking, but we manage concurrency externally
        # using asyncio.Lock() and run synchronous operations in a thread pool
        # implicitly via standard asyncio run_in_executor if this were heavily IO bound.
        # For simple read/write in a single process, direct connection management is often used
        # alongside locks to prevent corruption, though multiprocessing might require pooling.
        if self._connection is None:
            # For simplicity and adherence to synchronous nature of sqlite3 module,
            # we rely on the top-level lock for atomicity across API calls.
            # In a high-concurrency multi-process environment, a connection pool manager is required.
            async with self._lock:
                if self._connection is None:
                    self._connection = sqlite3.connect(self.db_path)
                    self._initialize_db()
        return self._connection

    async def fetch_next_task(self) -> Optional[Dict[str, Any]]:
        """
        Asynchronously fetches the highest priority task marked 'QUEUED' 
        and immediately updates its status to 'PROCESSING' to prevent double-pulling.
        """
        await self._initialize_db()
        async with self._lock:
            conn = await self._get_db_connection()
            try:
                # Use SELECT FOR UPDATE logic via locking mechanism
                cursor = conn.cursor()
                
                # 1. Find the next task (highest priority first)
                cursor.execute(f"""
                    SELECT task_id, payload_json FROM {TASK_QUEUE_TABLE}
                    WHERE status = 'QUEUED'
                    ORDER BY priority DESC, created_at ASC
                    LIMIT 1
                """)
                result = cursor.fetchone()

                if not result:
                    return None

                task_id, payload_json = result
                
                # 2. Claim the task by updating status
                cursor.execute(f"""
                    UPDATE {TASK_QUEUE_TABLE}
                    SET status = 'PROCESSING'
                    WHERE task_id = ? AND status = 'QUEUED'
                """, (task_id,))
                
                conn.commit()
                
                payload = json.loads(payload_json)
                payload['task_id'] = task_id
                return payload

            except Exception as e:
                conn.rollback()
                print(f"Error fetching task: {e}")
                return None

    async def update_task_state(self, task_id: str, step_name: str, data: Dict[str, Any], stability: float) -> bool:
        """
        Records a state transition and optionally calculates divergence.
        """
        await self._initialize_db()
        
        # Stability Check: Log divergence if significantly off target
        divergence = abs(stability - STABILITY_TARGET)
        if divergence > 1.0: # Example threshold for logging critical drift
            print(f"[WARNING] Task {task_id} at step '{step_name}' has high D_KL divergence: {divergence:.2f}")

        async with self._lock:
            conn = await self._get_db_connection()
            try:
                cursor = conn.cursor()
                
                # Log the specific step state
                cursor.execute(f"""
                    INSERT INTO {STATE_TABLE} (task_id, step_name, data_json, stability_metric)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_id, 
                    step_name, 
                    json.dumps(data), 
                    stability
                ))
                
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                print(f"Error updating state for {task_id} at {step_name}: {e}")
                return False

    async def finalize_task(self, task_id: str, final_status: str, final_data: Dict[str, Any]) -> bool:
        """Updates the main queue status to DONE or FAILED."""
        async with self._lock:
            conn = await self._get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute(f"""
                    UPDATE {TASK_QUEUE_TABLE}
                    SET status = ?
                    WHERE task_id = ?
                """, (final_status, task_id))
                
                # Log final state (optional, but good for audit)
                await self.update_task_state(task_id, f"FINAL_{final_status}", final_data, STABILITY_TARGET)

                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                print(f"Error finalizing task {task_id} as {final_status}: {e}")
                return False

    async def _simulate_bio_generation(self, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulates the core execution loop (the 'Bio-Generator').
        This function represents the heavy computation/IO that should be asynchronous.
        """
        task_id = task_payload['task_id']
        
        # --- Step 1: Initialization & Stability Calibration ---
        await asyncio.sleep(0.1) # Simulate small IO overhead
        initial_stability = STABILITY_TARGET + 0.5 # Slightly perturbed
        await self.update_task_state(task_id, "CALIBRATION", {"input": task_payload}, initial_stability)

        # --- Step 2: Iterative Molecule Synthesis (Simulated Loop) ---
        max_iterations = task_payload.get('complexity', 5)
        current_result = {"molecules": []}
        
        for i in range(1, max_iterations + 1):
            # Simulate computation time and dynamic stability drift
            await asyncio.sleep(0.2 + (i * 0.05)) 
            
            # Dynamic Stability Calculation (Ensuring compliance with D_KL model)
            # In a real system, this would involve complex metric calculation.
            current_stability = STABILITY_TARGET + (1.0 / i) * (0.1 * (i % 2 - 0.5))
            
            new_molecule = f"MISO_GEN_{task_id[:4]}_{i}"
            current_result['molecules'].append(new_molecule)
            
            await self.update_task_state(
                task_id, 
                f"SYNTHESIS_STEP_{i}", 
                {"iteration": i, "molecules_count": len(current_result['molecules'])}, 
                current_stability
            )
            
            if i == max_iterations // 2 and task_payload.get('fail_halfway'):
                raise MuscleExecutionError(f"Simulated internal error during synthesis at step {i}")

        # --- Step 3: Finalization ---
        final_stability = STABILITY_TARGET - 0.1 # Minor stabilization near the end
        current_result['final_yield'] = len(current_result['molecules'])
        
        await self.update_task_state(task_id, "QC_PASS", {"yield": current_result['final_yield']}, final_stability)
        return current_result

    async def run_worker(self):
        """The main asynchronous worker loop."""
        while True:
            task = await self.fetch_next_task()
            
            if not task:
                # No tasks available, yield control and wait briefly
                await asyncio.sleep(1) 
                continue

            task_id = task['task_id']
            print(f"Muscle processing Task ID: {task_id} (Priority: {task.get('priority')})")

            try:
                # Execute the core bio-generation logic
                final_output = await self._simulate_bio_generation(task)
                
                # Mark as complete
                await self.finalize_task(task_id, "COMPLETE", final_output)
                print(f"Task {task_id} completed successfully.")

            except MuscleExecutionError as e:
                # Handle expected execution failures gracefully
                await self.finalize_task(task_id, "FAILED", {"error": str(e)})
                print(f"Task {task_id} failed: {e}")
            except Exception as e:
                # Handle unexpected critical errors
                await self.finalize_task(task_id, "CRITICAL_ERROR", {"error": f"Unexpected crash: {type(e).__name__}"})
                print(f"Task {task_id} caused a CRITICAL ERROR: {e}")

# --- Example Usage and Bootstrap (For testing setup) ---

async def bootstrap_dummy_tasks(muscle: MisoMuscle):
    """Inserts sample tasks into the queue for testing."""
    print("Bootstrapping dummy tasks...")
    
    # Task 1: High priority, complex, should succeed
    task1 = {
        "task_id": "T_MUSCLE_001",
        "priority": 10,
        "complexity": 7,
        "protocol": "PROTEIN_SYNTH_A",
        "payload": {"sequence": "ACGT..."}
    }
    
    # Task 2: Low priority, simple, will fail halfway
    task2 = {
        "task_id": "T_MUSCLE_002",
        "priority": 1,
        "complexity": 4,
        "protocol": "SCREENING_B",
        "fail_halfway": True,
        "payload": {"sample_id": 123}
    }

    # Task 3: Medium priority, standard run
    task3 = {
        "task_id": "T_MUSCLE_003",
        "priority": 5,
        "complexity": 5,
        "protocol": "CATALYST_C",
        "payload": {"catalyst_id": "X90"}
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"INSERT INTO {TASK_QUEUE_TABLE} (task_id, payload_json, priority, status) VALUES (?, ?, ?, 'QUEUED')",
                       (task1['task_id'], json.dumps(task1), task1['priority']))
        cursor.execute(f"INSERT INTO {TASK_QUEUE_TABLE} (task_id, payload_json, priority, status) VALUES (?, ?, ?, 'QUEUED')",
                       (task2['task_id'], json.dumps(task2), task2['priority']))
        cursor.execute(f"INSERT INTO {TASK_QUEUE_TABLE} (task_id, payload_json, priority, status) VALUES (?, ?, ?, 'QUEUED')",
                       (task3['task_id'], json.dumps(task3), task3['priority']))
        conn.commit()
        print("3 tasks inserted.")
    except sqlite3.IntegrityError:
        print("Tasks already exist, skipping bootstrap.")
    finally:
        conn.close()

if __name__ == '__main__':
    # Clean up old DB file for a fresh run demonstration
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    muscle = MisoMuscle()

    async def main_control():
        await bootstrap_dummy_tasks(muscle)
        
        # Run 3 workers concurrently to demonstrate asynchronous concurrency
        workers = [muscle.run_worker() for _ in range(3)]
        
        # Let the workers run for 10 seconds to process the tasks
        try:
            print("\n--- Starting Muscle Workers (10s Runtime) ---")
            await asyncio.wait_for(asyncio.gather(*workers), timeout=10)
        except asyncio.TimeoutError:
            print("\n--- Workers stopped after timeout ---")
        except KeyboardInterrupt:
            print("\n--- Execution Halted by User ---")
        finally:
            # Gracefully cancel the infinite loops
            for w in workers:
                w.cancel()
            # Wait briefly for cancellation cleanup
            await asyncio.gather(*workers, return_exceptions=True)
            print("Muscle Shutdown Complete.")

    try:
        asyncio.run(main_control())
    except RuntimeError as e:
        if "Event loop is closed" not in str(e):
            raise