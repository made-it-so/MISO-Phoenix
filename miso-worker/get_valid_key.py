from app.tenant_manager import Landlord
l = Landlord()
# Create a new user to ensure the key exists
key = l.register_tenant("RECOVERY_USER", "GOLD", budget=10.00)
print(key)
