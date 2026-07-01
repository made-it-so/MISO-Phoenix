import duckdb

con = duckdb.connect()
con.execute("INSTALL delta; LOAD delta;")

print("\n[MISO-EXPLORER] Connected to Sovereign Substrate.")
search_term = input("Enter a keyword to search (or press Enter for 'Axiom 500'): ") or "Axiom 500"

# Query the Silver Layer directly from disk
query = f"""
    SELECT * FROM delta_scan('C:/MISO_RESEARCH/data/silver/nodes') 
    WHERE content LIKE '%{search_term}%'
"""

results = con.execute(query).df()

print(f"\n--- SEARCH RESULTS FOR '{search_term}' ---")
if not results.empty:
    print(results)
else:
    print("No matching nodes found.")
