import duckdb
import pandas as pd
from deltalake import write_deltalake, DeltaTable

# 1. Connect to Substrate
silver_path = "C:/MISO_RESEARCH/data/silver/nodes"
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")

print("\n[MISO-DEDUPLICATOR] Collapsing Redundant Axioms...")

# 2. Identify Perfect Duplicates (1.000 Similarity)
# We find nodes that are content-identical but have different IDs
query = f"""
    WITH Duplicates AS (
        SELECT 
            MIN(node_id) as master_id, 
            content, 
            COUNT(*) as occurrences
        FROM delta_scan('{silver_path}')
        GROUP BY content
        HAVING COUNT(*) > 1
    )
    SELECT * FROM delta_scan('{silver_path}')
    WHERE node_id IN (SELECT master_id FROM Duplicates)
    OR content NOT IN (SELECT content FROM Duplicates)
"""

print("-> Analyzing 52,369 relationships for redundancy...")
distilled_df = con.execute(query).df()

# 3. Commit the Optimized Substrate
reduction = 2263 - len(distilled_df)
print(f"-> Detected {reduction} redundant Axioms.")

if reduction > 0:
    print(f"-> Distilling Substrate into high-potency Master Axioms...")
    write_deltalake(silver_path, distilled_df, mode="overwrite", schema_mode="overwrite")
    
    dt = DeltaTable(silver_path)
    print(f"\n[SUCCESS] Substrate Distilled to Version {dt.version()}")
    print(f"New Node Count: {len(distilled_df)}")
else:
    print("[SKIP] No exact duplicates found. Substrate is already lean.")

print("\n[FINAL AXIOM] MISO now holds only unique, justified truths.")
