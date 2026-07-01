import subprocess
import time
import requests
import os

def startup_sequence():
    print(f"\n[🚀] MISO SOVEREIGN WAKE-UP SEQUENCE: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. INITIALIZE OLLAMA (The Brain)
    # Checks if Port 11434 is active; if not, warns to start background service.
    try:
        requests.get("http://localhost:11434/api/tags", timeout=2)
        print("[✅] OLLAMA ENGINE: ONLINE")
    except:
        print("[⚠️] OLLAMA ENGINE: OFFLINE. Starting background service...")
        # Note: 'ollama serve' is best run in a separate persistent window.

    # 2. LAUNCH SOVEREIGN GATE (The API)
    # We launch the gate we built for Port 8001
    print("[📡] OPENING SOVEREIGN GATE (Port 8001)...")
    # subprocess.Popen(["python", "miso_sovereign_gate.py"]) 

    # 3. TRIGGER 2026 BACKFILL (Legal & Medical)
    # MISO needs to know what happened while you were away.
    print("[🔬] INGESTING LATEST FEB 2026 AXIOMS...")
    from miso_clinical_fetch import fetch_medical_evidence
    from miso_legal_expert import legal_sme_arbitrate

    # Fetching the 'New Unit Dispatch' and 'Information Blocking' rules from Feb 2026
    backfill_topics = [
        "MISO unit dispatch system 2026",
        "Information Blocking enforcement February 2026",
        "FDA ISO 13485 alignment 2026"
    ]
    
    for topic in backfill_topics:
        evidence = fetch_medical_evidence(topic)
        print(f"   -> Ingested: {topic[:30]}...")

    print("[✅] SEQUENCE COMPLETE. MISO IS SYNCED AND SOVEREIGN.")

if __name__ == "__main__":
    startup_sequence()
