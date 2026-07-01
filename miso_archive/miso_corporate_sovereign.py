import json
import os

# SOVEREIGN POLICY REPOSITORY
CORP_DB = r"C:\Users\kyle\miso_data\corporate_policies"
if not os.path.exists(CORP_DB): os.makedirs(CORP_DB)

def corporate_sovereign_arbitrate(user_id, justification, company_id="Aerospace_Corp"):
    print(f"\n[🏢] CORPORATE AUDIT | USER: {user_id} | CORP: {company_id}")
    
    # 1. LOAD SOVEREIGN POLICY
    policy_path = os.path.join(CORP_DB, f"{company_id}_policy.json")
    if not os.path.exists(policy_path):
        return "403: ACCESS DENIED - Corporate Sovereign Policy not found."

    with open(policy_path, 'r') as f:
        policy = json.load(f)

    # 2. INTERNAL CLEARANCE CHECK
    user_clearance = policy.get("users", {}).get(user_id, 0)
    required_clearance = policy.get("min_clearance", 5)
    
    if user_clearance < required_clearance:
        return f"403: CORPORATE REJECTION - User Clearance ({user_clearance}) below required ({required_clearance})."

    # 3. PROJECT-SPECIFIC TOKEN VALIDATION
    # Aerospace projects often require a 'Shadow-Token' not listed in ITAR
    mandatory_tokens = policy.get("mandatory_tokens", [])
    for token in mandatory_tokens:
        if token not in justification:
            return f"403: CORPORATE REJECTION - Missing internal Project Token: {token}"

    # 4. RESTRICTED CORPORATE KEYWORDS
    # e.g., A company might forbid mentioning 'merger' or 'acquisition' in data overrides
    forbidden = policy.get("forbidden_keywords", [])
    if any(word in justification.lower() for word in forbidden):
        return "403: CORPORATE REJECTION - Justification contains restricted internal keywords."

    return f"200 OK: Validated via {company_id} Sovereign Policy."

# SETUP: Create a mock policy for 'Aerospace_Corp'
mock_policy = {
    "min_clearance": 7,
    "users": {"kyle": 10, "guest_user": 3},
    "mandatory_tokens": ["ALPHA-NINER"],
    "forbidden_keywords": ["merger", "acquisition", "layoff"]
}
with open(os.path.join(CORP_DB, "Aerospace_Corp_policy.json"), 'w') as f:
    json.dump(mock_policy, f)

# TEST: Run an audit for Kyle (High Clearance + Correct Token)
print(corporate_sovereign_arbitrate("kyle", "ITAR DS-4076 transfer for ALPHA-NINER"))

# TEST: Run an audit for Guest (Low Clearance)
print(corporate_sovereign_arbitrate("guest_user", "Urgent transfer ALPHA-NINER"))
