"""
Central configuration for MISO. All hardcoded paths and constants live here.
Override any value by setting the corresponding environment variable.
"""
import os

# --- Paths ---
SILVER_PATH = os.environ.get(
    "MISO_SILVER_PATH",
    "C:/MISO_RESEARCH/data/silver/nodes"
)

SHARED_BUFFER = os.environ.get(
    "MISO_SHARED_BUFFER",
    r"C:\Users\kyle\miso_data\miso_shared_buffer.json"
)

MANIFOLD_PATH = os.environ.get(
    "MISO_MANIFOLD_PATH",
    os.path.join(os.path.dirname(__file__), "miso_manifold.json")
)

MONITOR_DIR = os.environ.get(
    "MISO_MONITOR_DIR",
    r"C:\MISO_RESEARCH\01_Core_Axioms"
)

PROCESSED_LOG = os.environ.get(
    "MISO_PROCESSED_LOG",
    os.path.join(os.path.dirname(__file__), "miso_processed_files.json")
)

# --- Databases ---
BOUNTY_DB_PATH = os.environ.get(
    "MISO_BOUNTY_DB",
    os.path.join(os.path.dirname(__file__), "miso_bounty_board.db")
)

# --- Services ---
OLLAMA_URL = os.environ.get("MISO_OLLAMA_URL", "http://127.0.0.1:11434")
DEFAULT_MODEL = os.environ.get("MISO_MODEL", "llama3")
AUDITOR_MODEL = os.environ.get("MISO_AUDITOR_MODEL", "miso-auditor:latest")
