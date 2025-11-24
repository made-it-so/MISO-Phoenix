import json
import os
import logging
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TENANT_FILE = os.path.join(BASE_DIR, "tenants.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [LANDLORD] %(message)s')
logger = logging.getLogger(__name__)

class Landlord:
    def __init__(self):
        self.load_tenants()

    def load_tenants(self):
        if os.path.exists(TENANT_FILE):
            with open(TENANT_FILE, 'r') as f:
                self.tenants = json.load(f)
        else:
            # Seed with default tenants
            self.tenants = {}
            self.register_tenant("CLIENT_ALPHA", "GOLD") # High Priority
            self.register_tenant("CLIENT_BETA", "SILVER") # Low Priority

    def save_tenants(self):
        with open(TENANT_FILE, 'w') as f:
            json.dump(self.tenants, f, indent=2)

    def register_tenant(self, name, tier):
        api_key = f"miso_sk_{secrets.token_hex(8)}"
        self.tenants[api_key] = {
            "name": name,
            "tier": tier,
            "balance": 100.00, # Free credit
            "usage": 0.00
        }
        self.save_tenants()
        logger.info(f"🔑 New Tenant Registered: {name} ({tier}) -> Key: {api_key}")
        return api_key

    def authenticate(self, api_key):
        tenant = self.tenants.get(api_key)
        if not tenant:
            logger.warning(f"⛔ Auth Failure: Invalid Key {api_key}")
            return None
        return tenant

    def charge_rent(self, api_key, cost):
        if api_key in self.tenants:
            self.tenants[api_key]["balance"] -= cost
            self.tenants[api_key]["usage"] += cost
            self.save_tenants()
            return self.tenants[api_key]["balance"]
        return 0

    def get_tier_config(self, tier):
        """
        Class Warfare Logic:
        Gold Tier gets better models and more patience.
        """
        if tier == "GOLD":
            return {"model": "gemini-1.5-pro", "patience": 20}
        else:
            return {"model": "gemini-1.5-flash", "patience": 5}

if __name__ == "__main__":
    l = Landlord()
    # Print keys for the user to see
    print(json.dumps(l.tenants, indent=2))
