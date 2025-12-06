import psycopg2
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger("miso.memory.hippocampus")

class InteractionLogger:
    def __init__(self):
        # Default to a safe fallback if DB url is missing
        self.db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miso_db")
        # We wrap init in try/except to prevent boot crash if DB is down
        try:
            self._init_db()
        except Exception as e:
            logger.warning(f"Hippocampus offline (DB Connection Failed): {e}")

    def _init_db(self):
        """Ensures the memory structures exist."""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    task_type TEXT,
                    model_used TEXT,
                    success BOOLEAN,
                    latency_ms INTEGER,
                    tokens_used INTEGER,
                    prompt TEXT,
                    response TEXT
                );
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Memory Initialization Failed: {e}")
            raise e

    def log_synapse(self, task_type, model, success, latency, tokens, prompt, response):
        """Encodes the experience into Continuum Memory."""
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            # Convert dict/list responses to string for storage
            response_str = json.dumps(response) if isinstance(response, (dict, list)) else str(response)
            
            cur.execute(
                "INSERT INTO logs (task_type, model_used, success, latency_ms, tokens_used, prompt, response) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (task_type, model, success, latency, tokens, prompt, response_str)
            )
            conn.commit()
            conn.close()
            logger.info(f"Memory encoded: {task_type} via {model}")
        except Exception as e:
            # We log the error but do not crash the organism
            logger.error(f"Memory Encoding Failed: {e}")
