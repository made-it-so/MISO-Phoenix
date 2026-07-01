import pandas as pd
from deltalake import write_deltalake
import duckdb
import os
import shutil

# Define paths
base_path = "C:/MISO_RESEARCH/data"
for layer in ["bronze", "silver", "gold"]:
    os.makedirs(f"{base_path}/{layer}", exist_ok=True)

print("\n[MISO-CENTRIC] Initializing Rust-based Delta Substrate...")

# 1. BRONZE: Create 2,263 Nodes
data = [{"node_id": i, "content": f"Axiom {i}", "category": "Compliance"} for i in range(2263)]
df = pd.DataFrame(data)

print("-> Writing BRONZE (2,263 Nodes to Disk)...")
write_deltalake(f"{base_path}/bronze/nodes", df, mode="overwrite")

# 2. SILVER: Refine via DuckDB
print("-> Refining SILVER (Cleansing Layer)...")
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")
# DuckDB reads the Delta files we just wrote
silver_df = con.execute(f"SELECT * FROM delta_scan('{base_path}/bronze/nodes')").df()
write_deltalake(f"{base_path}/silver/nodes", silver_df, mode="overwrite")

# 3. GOLD: Aggregate Intelligence
print("-> Finalizing GOLD (Sovereign Summary)...")
gold_df = con.execute(f"SELECT category, count(*) as total FROM delta_scan('{base_path}/silver/nodes') GROUP BY 1").df()

print("\n--- GOLD LAYER PREVIEW ---")
print(gold_df)
print("\n[SUCCESS] Medallion Substrate Created (No Spark Required).")
