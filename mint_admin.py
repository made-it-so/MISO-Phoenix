from miso_project.core.vault import RevenueVault
vault = RevenueVault()
key = vault.create_user("Admin User", 100.00)
print(f"\n>>> NEW MASTER KEY: {key}\n")
