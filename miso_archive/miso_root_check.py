import os
import pandas as pd

bronze_path = "C:/MISO_RESEARCH/data/bronze"
print(f"\n--- SCANNING RAW BRONZE SIGNALS ---")

found_in_any = False
for file in os.listdir(bronze_path):
    if file.endswith(".parquet"):
        df = pd.read_parquet(os.path.join(bronze_path, file))
        # Search the entire dataframe for the string "C-SPAN"
        mask = df.apply(lambda row: row.astype(str).str.contains('C-SPAN', case=False).any(), axis=1)
        matches = df[mask]
        
        if not matches.empty:
            print(f"\n[FOUND] Match in raw file: {file}")
            print(matches.head(2))
            found_in_any = True

if not found_in_any:
    print("\n[!] C-SPAN is NOT in the Bronze folder.")
    print("This means the initial signal capture failed to record the text.")
