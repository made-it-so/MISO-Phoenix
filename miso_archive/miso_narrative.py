import pandas as pd
from deltalake import write_deltalake, DeltaTable
import duckdb
import datetime

# 1. Connect to the Evolved Substrate
silver_path = "C:/MISO_RESEARCH/data/silver/nodes"
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")

print("\n[MISO-NARRATIVE] Injecting Contextual Intelligence into Substrate...")

# 2. Add Narrative Metadata
# We are simulating the "David" and "Nancy" personas from your transcript
query = f"""
    SELECT 
        *,
        CASE 
            WHEN node_id % 10 = 0 THEN 'David (Product)'
            WHEN node_id % 10 = 5 THEN 'Nancy (Regulatory)'
            ELSE 'System (Automated)'
        END as originator,
        CASE 
            WHEN node_id % 10 = 0 THEN 'Synthesized from C-SPAN/YouTube feed for legal prospecting.'
            WHEN node_id % 10 = 5 THEN 'Flagged for potential HIPAA/510K regulatory conflict.'
            ELSE 'Standard MISO foundational axiom.'
        END as rationale,
        '{datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}' as last_modified
    FROM delta_scan('{silver_path}')
"""
narrative_df = con.execute(query).df()

# 3. Commit Version 2 with Schema Evolution
print("-> Committing Narrative Layer (Version 2)...")
write_deltalake(silver_path, narrative_df, mode="overwrite", schema_mode="overwrite")

# 4. Verification
dt = DeltaTable(silver_path)
print(f"\n[SUCCESS] Substrate Evolved to Version {dt.version()}")
print(f"Narrative Columns: originator, rationale, last_modified")

# Show a sample of the "David" vs "Nancy" nodes
print("\n--- NARRATIVE AUDIT (Personas) ---")
print(narrative_df[narrative_df['node_id'].isin([0, 5, 10, 15])][['node_id', 'originator', 'rationale']])
