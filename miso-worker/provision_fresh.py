from app.tenant_manager import Landlord
l = Landlord()
# Create a wealthy Beta user
key = l.register_tenant("BETA_V42", "GOLD", budget=50.00)
print(key)
