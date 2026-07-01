import json
import os
import re

# THE 2026 LEGAL REPOSITORY
LEGAL_DB = r"C:\Users\kyle\miso_data\legal_axioms"
if not os.path.exists(LEGAL_DB): os.makedirs(LEGAL_DB)

def legal_sme_arbitrate(justification: str, jurisdiction: str = "US"):
    print(f"\n[⚖️] LEGAL SME AUDIT | JURISDICTION: {jurisdiction}")
    
    # 1. EU AI ACT (ARTICLE 5) - UNACCEPTABLE RISK CHECK
    # Enforced as of Feb 2, 2026
    prohibited_patterns = ["biometric categorization", "social scoring", "facial scraping"]
    if jurisdiction == "EU" and any(p in justification.lower() for p in prohibited_patterns):
        return "403: LEGAL REJECTION - Prohibited AI Practice (EU AI Act Art. 5)."

    # 2. ITAR / COMMODITY JURISDICTION CHECK
    # 2026 Requirement: Must cite DS-4076 Case Number
    if "itar" in justification.lower():
        if not re.search(r"DS-4076-\d+", justification):
            return "403: LEGAL REJECTION - ITAR requires a valid DS-4076 Case Number."

    # 3. FDA QMSR (GxP) AUDIT
    # Effective Feb 2, 2026: Must cite ISO 13485 Risk Assessment
    if "gxp" in justification.lower() or "medical" in justification.lower():
        if "iso 13485" not in justification.lower():
            return "403: LEGAL REJECTION - FDA QMSR (Feb 2026) requires ISO 13485 alignment."

    return "200 OK: Justification satisfies 2026 Legal SME Thresholds."

# TEST CASE
if __name__ == "__main__":
    print(legal_sme_arbitrate("Emergency ITAR transfer for DS-4076-2026001", "US"))
