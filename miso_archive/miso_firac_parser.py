import json
import os

# LEGAL PRECEDENT BUFFER
PRECEDENT_DB = r"C:\Users\kyle\miso_data\legal_precedents.json"

def ingest_case_firac(case_name, facts, issue, rule, analysis, conclusion):
    print(f"\n[📖] INGESTING PRECEDENT: {case_name}")
    
    # Load existing database
    if os.path.exists(PRECEDENT_DB):
        with open(PRECEDENT_DB, 'r') as f:
            db = json.load(f)
    else:
        db = {}

    # Anchor the case using the FIRAC framework (Yale Toolkit Method)
    db[case_name] = {
        "F": facts,       # Material events of the case
        "I": issue,       # The precise legal question
        "R": rule,        # The authoritative legal norm (The Ratio)
        "A": analysis,    # Mapping facts to the rule
        "C": conclusion,  # The definitive answer
        "Source_Axiom": "Harvard_Zero-L_2026"
    }

    with open(PRECEDENT_DB, 'w') as f:
        json.dump(db, f, indent=4)
    print(f"[✅] {case_name} is now an active Legal Axiom.")

# SAMPLE INGESTION: United States v. Heppner (Feb 10, 2026)
# This is a real 2026 case regarding AI Attorney-Client Privilege.
ingest_case_firac(
    "US_v_Heppner_2026",
    facts="Defendant used a consumer AI tool to analyze legal exposure and shared results with counsel. FBI seized the device.",
    issue="Does Attorney-Client Privilege attach to prompts sent to a public AI tool?",
    rule="Privilege requires a 'reasonable expectation of confidentiality' and an 'attorney-client relationship.'",
    analysis="The AI tool's privacy policy permitted data collection for training, defeating confidentiality. AI is not a lawyer.",
    conclusion="NO PRIVILEGE. AI-generated analyses were discoverable by the government."
)
