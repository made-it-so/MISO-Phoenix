import pandas as pd
import os
from datetime import datetime

VAULT_PATH = "C:/MISO_RESEARCH/vault.parquet"

def add_to_vault(text, source="User"):
    if not text.strip(): return
    
    new_entry = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": source,
        "content": text
    }])
    
    if os.path.exists(VAULT_PATH):
        df = pd.concat([pd.read_parquet(VAULT_PATH), new_entry], ignore_index=True)
    else:
        df = new_entry
        
    df.to_parquet(VAULT_PATH)
    print(f"\n[MISO] Real-world data committed to Vault.")

if __name__ == "__main__":
    content = input("Paste the raw text/note you want MISO to learn: ")
    add_to_vault(content)
