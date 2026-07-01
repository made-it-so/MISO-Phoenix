import os
import pandas as pd

bronze_dir = "C:/MISO_RESEARCH/data/bronze"
found_data = False

print("\n--- SCANNING BRONZE (RAW SIGNAL) FOR ACTUAL TEXT ---")

if not os.path.exists(bronze_dir):
    print(f"ERROR: Bronze directory not found at {bronze_dir}")
else:
    for file in os.listdir(bronze_dir):
        if file.endswith(".parquet"):
            path = os.path.join(bronze_dir, file)
            df = pd.read_parquet(path)
            
            # Look for the word 'C-SPAN' or just 'Nancy' or 'David'
            # to see if the content column actually has text
            if 'content' in df.columns:
                # Check if the first row is just 'Axiom X'
                is_placeholder = df['content'].iloc[0].startswith('Axiom')
                
                if not is_placeholder:
                    print(f"\n[!] VALID DATA FOUND in {file}")
                    print(df[['content', 'originator']].head(5))
                    found_data = True
                    break
                else:
                    print(f"[-] {file} contains placeholders (Axiom X). Skipping...")

if not found_data:
    print("\n[CRITICAL] No raw text found in Bronze.")
    print("The ingestion script failed to pass the actual strings to the Parquet files.")
