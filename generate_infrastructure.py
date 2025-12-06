from miso_client.client import Miso
import json

# Initialize Client (Key is mocked for local audit)
miso = Miso("test-key")

print(">>> REQUESTING ARCHITECTURAL BLUEPRINT...")

# Trigger the Accountant's Logic
response = miso._send("audit_aws", "generate_tf")

if response.get("status") == "success":
    plan = response["data"]["migration_plan"]
    
    # Save the blueprint to disk
    filename = "miso_spot_fleet.tf"
    with open(filename, "w") as f:
        f.write(plan)
    
    print(f"SUCCESS: Blueprint saved to '{filename}'")
    print("Previewing Configuration:")
    print("-" * 40)
    print(plan.strip())
    print("-" * 40)
else:
    print(f"FAILURE: {response}")
