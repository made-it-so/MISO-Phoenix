import json
import os

# REPOSITORY FOR NESTED POLICIES
POLICY_DB = r"C:\Users\kyle\miso_data\governance_policies"
if not os.path.exists(POLICY_DB): os.makedirs(POLICY_DB)

def pure_governance_arbitrate(company_id: str, justification: str):
    print(f"\n[⚖️] AUDITING GOVERNANCE FOR: {company_id}")
    
    # 1. LOAD THE SOVEREIGN POLICY (Customized for each user/company)
    policy_file = os.path.join(POLICY_DB, f"{company_id}_rules.json")
    if not os.path.exists(policy_file):
        return "403: ACCESS DENIED - No policy defined for this entity."

    with open(policy_file, 'r') as f:
        rules = json.load(f)

    # 2. EVALUATE GLOBAL REGULATORY LAYER (e.g., ITAR)
    # 2026 ITAR requirement: Must cite a valid DS-4076 or DSP-5
    requires_itar = rules.get("enforce_itar", False)
    has_itar = "DS-4076" in justification or "DSP-5" in justification
    
    if requires_itar and not has_itar:
        return "403: REJECTED - Violation of Federal ITAR standards."

    # 3. EVALUATE CORPORATE SOVEREIGN LAYER (Specific to the user)
    # The company can define ANY key-value pair here
    required_token = rules.get("mandatory_internal_token")
    if required_token and required_token not in justification:
        return f"403: REJECTED - Missing internal company token: {required_token}"

    return f"200 OK: Justification satisfies both Global and {company_id} Internal policies."

# SETUP: Create a custom policy for 'Aerospace_Global'
aerospace_rules = {
    "enforce_itar": True,
    "mandatory_internal_token": "ALPHA-9-CLEARANCE"
}
with open(os.path.join(POLICY_DB, "Aerospace_Global_rules.json"), 'w') as f:
    json.dump(aerospace_rules, f)

# TEST: Run a clean, logic-only check
print(pure_governance_arbitrate("Aerospace_Global", "Authorized via DS-4076 for ALPHA-9-CLEARANCE"))
