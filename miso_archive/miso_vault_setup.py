import os

def setup_vault():
    print(f"\n[🔐] INITIALIZING SOVEREIGN CREDENTIAL VAULT...")
    
    # In 2026, these are the standard keys for Deep Medical Ingestion
    nature_key = input("Enter Springer Nature API Key: ")
    nejm_token = input("Enter NEJM Institutional Token: ")
    
    with open(".env", "w") as f:
        f.write(f"NATURE_API_KEY={nature_key}\n")
        f.write(f"NEJM_INSTITUTIONAL_TOKEN={nejm_token}\n")
    
    print("[✅] VAULT SECURED. MISO now has 'Key-Card' access to paid journals.")

if __name__ == "__main__":
    setup_vault()
