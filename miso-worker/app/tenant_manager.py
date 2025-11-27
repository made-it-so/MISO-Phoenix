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
            self.tenants = {}

    def save_tenants(self):
        with open(TENANT_FILE, 'w') as f:
            json.dump(self.tenants, f, indent=2)

    def register_tenant(self, name, tier, budget=5.00):
        """Creates a new user with a HARD budget cap."""
        api_key = f"miso_sk_{secrets.token_hex(8)}"
        self.tenants[api_key] = {
            "name": name,
            "tier": tier,
            "balance": budget,
            "total_spend": 0.00
        }
        self.save_tenants()
        logger.info(f"🔑 Tenant Created: {name} | Budget: ${budget}")
        return api_key

    def authenticate(self, api_key):
        """Verifies validity of API Key."""
        tenant = self.tenants.get(api_key)
        if not tenant:
            logger.warning(f"⛔ Auth Failure: Invalid Key {api_key}")
            return None
        return tenant

    def check_solvency(self, api_key):
        """Returns False if the user is broke."""
        tenant = self.tenants.get(api_key)
        if not tenant: return False
        
        if tenant['balance'] <= 0:
            logger.warning(f"⛔ INSOLVENT: {tenant['name']} has ${tenant['balance']:.4f}")
            return False
        return True

    def charge_rent(self, api_key, cost):
        if api_key in self.tenants:
            self.tenants[api_key]["balance"] -= cost
            self.tenants[api_key]["total_spend"] += cost
            self.save_tenants()
            return self.tenants[api_key]["balance"]
        return 0

    def get_tier_config(self, tier):
        return {"model": "gemini-1.5-flash", "patience": 5}
