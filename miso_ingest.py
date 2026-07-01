"""
PDF ingestion daemon. Watches MONITOR_DIR for new PDFs, classifies them
via the auditor LLM, and appends results to the manifold.

Processed file state is persisted to PROCESSED_LOG so restarts don't
re-ingest files already handled.
"""
import os
import time
import json
import re
import requests
from pypdf import PdfReader
from miso_config import MONITOR_DIR, OLLAMA_URL, AUDITOR_MODEL, MANIFOLD_PATH, PROCESSED_LOG


def _load_processed() -> set:
    """Load the set of already-processed filenames from disk."""
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def _save_processed(processed: set):
    """Persist the processed set to disk."""
    with open(PROCESSED_LOG, "w", encoding="utf-8") as f:
        json.dump(sorted(processed), f, indent=2)


def _append_to_manifold(entry: dict):
    """Append an ingestion result to the manifold's ingested_data list."""
    if not os.path.exists(MANIFOLD_PATH):
        return
    with open(MANIFOLD_PATH, "r", encoding="utf-8") as f:
        manifold = json.load(f)
    manifold.setdefault("ingested_data", []).append(entry)
    # Update audited_count to reflect only successful SIGNAL verdicts
    manifold["audited_count"] = sum(
        1 for e in manifold["ingested_data"]
        if e.get("verdict") == "SIGNAL" and "raw" not in e
    )
    with open(MANIFOLD_PATH, "w", encoding="utf-8") as f:
        json.dump(manifold, f, indent=4)


def clean_text(text: str) -> str:
    text = re.sub(r"[^\x00-\x7f]", "", text)
    return " ".join(text.split())


def audit_text(text: str) -> str:
    prompt = (
        f"SYSTEM_AUDIT_v1301.162. DATA: {clean_text(text)[:2000]}. "
        f"VERDICT: SIGNAL or NOISE? (ONE WORD ONLY)"
    )
    payload = {
        "model": AUDITOR_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 5},
    }
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["response"].strip().upper()
    except requests.exceptions.Timeout:
        return "ERROR_TIMEOUT"
    except requests.exceptions.RequestException as e:
        return f"ERROR_{type(e).__name__}"
    except (KeyError, ValueError) as e:
        return f"ERROR_PARSE_{type(e).__name__}"


def start_ingestion():
    print(f"[+] HARDENED INGESTION ACTIVE: Watching {MONITOR_DIR}")
    processed = _load_processed()
    print(f"[+] Resuming — {len(processed)} files already processed.")

    while True:
        try:
            all_files = os.listdir(MONITOR_DIR)
        except FileNotFoundError:
            print(f"[!] Monitor directory not found: {MONITOR_DIR}")
            time.sleep(10)
            continue

        new_files = [f for f in all_files if f.endswith(".pdf") and f not in processed]

        for fname in new_files:
            fpath = os.path.join(MONITOR_DIR, fname)
            print(f"[*] ATOMIZING: {fname}")
            try:
                reader = PdfReader(fpath)
                pages_text = [p.extract_text() for p in reader.pages if p.extract_text()]
                full_text = " ".join(pages_text)
                if not full_text:
                    print(f"[!] FAILED: No text extracted from {fname}")
                    processed.add(fname)
                    _save_processed(processed)
                    continue

                verdict = audit_text(full_text)
                print(f"[>] AUDITOR VERDICT: {verdict}")

                entry = {"file": fname, "verdict": verdict, "timestamp": time.time()}
                _append_to_manifold(entry)

                processed.add(fname)
                _save_processed(processed)

            except Exception as e:
                print(f"[!] FRACTURE on {fname}: {type(e).__name__}: {e}")

        time.sleep(5)


if __name__ == "__main__":
    start_ingestion()
