from app.tenant_manager import Landlord
import json

l = Landlord()
key_gold = l.register_tenant("BETA_USER_GOLD", "GOLD")
key_silver = l.register_tenant("BETA_USER_SILVER", "SILVER")

print(json.dumps({
    "GOLD_KEY": key_gold,
    "SILVER_KEY": key_silver
}, indent=2))
