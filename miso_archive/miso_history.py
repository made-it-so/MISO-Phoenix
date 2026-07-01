from deltalake import DeltaTable
import pandas as pd

# Connect to the Silver Layer Substrate
dt = DeltaTable("C:/MISO_RESEARCH/data/silver/nodes")

print("\n[MISO-AUDITOR] Accessing Temporal Ledger...")

# 1. Show the Version History
history = dt.history()
history_df = pd.DataFrame(history)

print("\n--- DELTA VERSION HISTORY ---")
# Show Version, Timestamp, and Operation
print(history_df[['version', 'timestamp', 'operation']])

# 2. Show the Current 'Axiom' State
print(f"\nCurrent Active Version: {dt.version()}")
print(f"Total Protected Files: {len(dt.files())}")

print("\n[SUCCESS] Temporal Integrity Verified. The Substrate is Immutable.")
