import duckdb
import pandas as pd
from deltalake import write_deltalake, DeltaTable

# 1. Connect to Substrate
silver_path = "C:/MISO_RESEARCH/data/silver/nodes"
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")

print("\n[MISO-PRUNER] Assessing Node Utility and Justification...")

# 2. Logic: Define "Justified" vs "Dead Wood"
# Justification = Having a Parent, having a Child, or having a Non-Standard Rationale
query = f"""
    WITH node_stats AS (
        SELECT 
            *,
            (SELECT COUNT(*) FROM delta_scan('{silver_path}') s2 WHERE s2.parent_id = s1.node_id) as child_count
        FROM delta_scan('{silver_path}') s1
    )
    SELECT 
        *,
        (CASE WHEN parent_id IS NOT NULL THEN 50 ELSE 0 END +
         CASE WHEN child_count > 0 THEN 50 ELSE 0 END +
         CASE WHEN rationale != 'Standard MISO foundational axiom.' THEN 100 ELSE 0 END) as utility_score
    FROM node_stats
"""
assessed_df = con.execute(query).df()

# 3. Execution: Filter only for Justified Nodes
# We automatically eliminate nodes with a Utility Score of 0
justified_nodes = assessed_df[assessed_df['utility_score'] > 0]
eliminated_count = len(assessed_df) - len(justified_nodes)

print(f"-> Analysis Complete. {len(justified_nodes)} nodes justified. {eliminated_count} nodes identified as Dead Wood.")

# 4. Atomic Sublimation
if eliminated_count > 0:
    print(f"-> Automatically Sublimating {eliminated_count} nodes to Version {DeltaTable(silver_path).version() + 1}...")
    # Using schema_mode="overwrite" to handle any column shifts during pruning
    write_deltalake(silver_path, justified_nodes, mode="overwrite", schema_mode="overwrite")
    
    dt = DeltaTable(silver_path)
    print(f"\n[SUCCESS] Substrate Optimized. Current Version: {dt.version()}")
    print(f"Current Node Count: {len(justified_nodes)}")
else:
    print("[SKIP] No Dead Wood detected. Substrate is already 100% justified.")

print("\n[NOTE] Eliminated nodes are preserved in previous versions and can be retrieved via Time Travel.")
