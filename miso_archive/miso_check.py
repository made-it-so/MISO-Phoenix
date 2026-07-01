import duckdb
SILVER_PATH = "C:/MISO_RESEARCH/data/silver/nodes"
con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")
print("\n--- MISO CURRENT SOVEREIGN INVENTORY (Top 10 Master Axioms) ---")
res = con.execute(f"SELECT node_id, originator, content FROM delta_scan('{SILVER_PATH}') LIMIT 10").df()
print(res)
