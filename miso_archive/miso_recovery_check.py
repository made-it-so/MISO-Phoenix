import duckdb
SILVER_PATH = "C:/MISO_RESEARCH/data/silver/nodes"
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")

# Broadening the net: Search for ANY partial match in ALL columns
print("\n--- DEEP SUBSTRATE SCAN ---")
query = f"""
    SELECT node_id, originator, content 
    FROM delta_scan('{SILVER_PATH}') 
    WHERE content ILIKE '%SPAN%' 
    OR rationale ILIKE '%SPAN%'
"""
res = con.execute(query).df()

if res.empty:
    print("MISO: Still nothing. The 905 pruned nodes contained the data, and the 1,358 do not.")
    print("ADVICE: We need to ROLL BACK to Version 2 to recover the lost granularity.")
else:
    print(res)
