import os
import json
from web3 import Web3
from eth_account import Account

# --- CONFIG ---
# We use Base Sepolia (Testnet) because it's cheap and EVM compatible.
RPC_URL = "[https://sepolia.base.org](https://sepolia.base.org)" 
KEY_FILE = "miso-worker/keystore.json"

class CryptoCortex:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))
        self.account = self.load_or_create_wallet()
        print(f"--- CRYPTO CORTEX ONLINE ---")
        print(f"ADDRESS: {self.account.address}")
        print(f"BALANCE: {self.get_balance()} ETH")

    def load_or_create_wallet(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "r") as f:
                private_key = json.load(f)["key"]
            return Account.from_key(private_key)
        else:
            # GENESIS EVENT: Create new identity
            new_acct = Account.create()
            with open(KEY_FILE, "w") as f:
                json.dump({"key": new_acct.key.hex()}, f)
            return new_acct

    def get_balance(self):
        try:
            wei = self.w3.eth.get_balance(self.account.address)
            return self.w3.from_wei(wei, 'ether')
        except:
            return 0.0

if __name__ == "__main__":
    wallet = CryptoCortex()
