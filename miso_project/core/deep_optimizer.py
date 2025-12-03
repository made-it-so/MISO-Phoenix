import os
import json
import logging
import pandas as pd
import psycopg2
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.optimizer")

class DeepOptimizer:
    """
    Implements Nested Learning 'Offline Consolidation'.
    Now tuned for Gemini 2.5 economics.
    """
    
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miso_db")
        self.weights_path = "miso_project/config/routing_weights.json"
        
        # Economic Efficiency Map (Cost per 1K tokens)
        # Updated for 2025 Era Models
        self.model_costs = {
            "gpt-4o": 0.03,
            "claude-3-opus": 0.075,
            "gemini-2.5-pro": 0.03,   # Competitive with GPT-4o
            "gemini-2.5-flash": 0.0001, # Extremely efficient (The new Reflex)
            "haiku": 0.00025
        }

    def _get_db_connection(self):
        try:
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"Failed to connect to Continuum Memory: {e}")
            return None

    def fetch_context_flow(self):
        conn = self._get_db_connection()
        if not conn: return pd.DataFrame()
        query = "SELECT model_used, success, latency_ms, tokens_used FROM logs WHERE timestamp >= NOW() - INTERVAL '24 HOURS'"
        try:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        except Exception:
            return pd.DataFrame()

    def calculate_efficiency_score(self, row):
        cost = self.model_costs.get(row['model_used'], 0.01)
        if cost == 0: cost = 0.0001
        performance = 1.0 if row['success'] else 0.1
        return performance / cost

    def sleep_cycle(self):
        logger.info(">>> INITIATING SLEEP CYCLE (Gemini 2.5 Optimization)...")
        df = self.fetch_context_flow()
        if df.empty:
            logger.warning("No new memories. Retaining rigid weights.")
            return
        
        df['score'] = df.apply(self.calculate_efficiency_score, axis=1)
        stats = df.groupby('model_used')['score'].mean().to_dict()
        total = sum(stats.values())
        new_weights = {k: v / total for k, v in stats.items()}
        
        logger.info(f"New Routing Weights: {new_weights}")
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        with open(self.weights_path, 'w') as f:
            json.dump(new_weights, f, indent=4)
