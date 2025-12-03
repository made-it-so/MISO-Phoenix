import psycopg2
import secrets
import logging
import os
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.vault")

class RevenueVault:
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/miso_db")
        self._init_ledger()

    def _init_ledger(self):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    api_key TEXT UNIQUE NOT NULL,
                    name TEXT,
                    balance DECIMAL(10, 6) DEFAULT 0.000000,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            conn.close()
        except: pass

    def create_user(self, name: str, initial_credit: float = 10.0) -> str:
        new_key = f"sk-miso-{secrets.token_hex(16)}"
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("INSERT INTO users (api_key, name, balance) VALUES (%s, %s, %s)", (new_key, name, initial_credit))
            conn.commit()
            conn.close()
            return new_key
        except Exception as e:
            return str(e)

    def verify_solvency(self, api_key: str) -> Optional[Dict]:
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("SELECT id, name, balance FROM users WHERE api_key = %s AND is_active = TRUE", (api_key,))
            res = cur.fetchone()
            conn.close()
            if res: return {"id": res[0], "name": res[1], "balance": float(res[2])}
            return None
        except: return None

    def charge_user_id(self, user_id: int, cost: float):
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (cost, user_id))
            conn.commit()
            conn.close()
        except Exception as e: logger.error(f"Charge Failed: {e}")
