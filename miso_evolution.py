"""
Schema evolution for the silver Delta Lake substrate.

IMPORTANT: This script overwrites the substrate. It creates a timestamped
backup before writing. Run manually — do NOT import this as a module.
"""
import shutil
import time
import pandas as pd
from deltalake import write_deltalake, DeltaTable
import duckdb
from miso_config import SILVER_PATH


def evolve_substrate():
    # 1. Backup before any destructive operation
    backup_path = f"{SILVER_PATH}_backup_{int(time.time())}"
    print(f"[MISO-EVOLUTION] Creating backup at: {backup_path}")
    shutil.copytree(SILVER_PATH, backup_path)
    print(f"[✓] Backup complete.")

    # 2. Connect and load current data
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    print("\n[MISO-EVOLUTION] Upgrading Silver Layer Schema...")

    # 3. Generate linked data
    # NOTE: parent_id is set to None for all nodes until a real parent
    # relationship is defined. Using modular arithmetic on node_id
    # (odd/even) creates a meaningless graph structure.
    query = f"""
        SELECT
            node_id,
            content,
            category,
            NULL::BIGINT AS parent_id
        FROM delta_scan('{SILVER_PATH}')
    """
    linked_df = con.execute(query).df()
    con.close()

    # 4. Commit with schema overwrite
    print("-> Committing Linked Axioms (Schema Evolution)...")
    write_deltalake(SILVER_PATH, linked_df, mode="overwrite", schema_mode="overwrite")

    # 5. Verify
    dt = DeltaTable(SILVER_PATH)
    print(f"\n[SUCCESS] Substrate evolved to version {dt.version()}")
    print(f"Schema: {len(dt.schema().fields)} columns present.")
    print(f"Backup retained at: {backup_path}")


if __name__ == "__main__":
    evolve_substrate()
