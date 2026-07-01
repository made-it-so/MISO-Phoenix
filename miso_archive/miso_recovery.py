from deltalake import DeltaTable, write_deltalake
import pandas as pd

silver_path = "C:/MISO_RESEARCH/data/silver/nodes"

print("\n[MISO-RECOVERY] Executing Direct Version 2 Restore...")

try:
    # 1. Directly load the table at Version 2 (The state BEFORE the lobotomy)
    dt = DeltaTable(silver_path, version=2)
    df_v2 = dt.to_pandas()
    
    # 2. Force an overwrite to the current version
    write_deltalake(silver_path, df_v2, mode="overwrite", schema_mode="overwrite")
    
    print(f"[SUCCESS] Substrate hard-reset to Version 2.")
    print(f"Current Node Count: {len(df_v2)}")
    
    # 3. Check for the actual "C-SPAN" content in the data
    found = df_v2[df_v2['content'].str.contains("C-SPAN", case=False, na=False)]
    if not found.empty:
        print("\n--- FOUND RECOVERED DATA ---")
        print(found[['node_id', 'content', 'originator']])
    else:
        print("\n[!] C-SPAN still missing. Checking head(5) for content labels...")
        print(df_v2[['node_id', 'content']].head(5))

except Exception as e:
    print(f"[CRITICAL ERROR] Restoration failed: {e}")
