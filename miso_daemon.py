"""
MISO Research Daemon — goal-directed autonomous ingestion.

Each cycle:
1. Reads active goals to derive arxiv search queries.
2. Downloads papers published in the current year that match.
3. Audits each paper for keyword density against goal criteria.
4. Stitches verified papers into the manifold WITHOUT duplicates.

Previous version bugs fixed:
- Hardcoded search keywords replaced with get_goal_keywords().
- Axiom deduplication: will not append the same title twice.
- Config centralized via miso_config.
- No backup on manifold write — now uses atomic write pattern.
- Bare except removed.
"""
import time
import os
import json
import shutil
import tempfile
from datetime import datetime, timezone

try:
    import arxiv
except ImportError:
    print("[!] arxiv package not installed. Run: pip install arxiv")
    raise

from pypdf import PdfReader
from miso_config import MANIFOLD_PATH
from miso_goal_kernel import get_active_goals, get_goal_keywords, update_progress

RESEARCH_DIR = os.environ.get("MISO_RESEARCH_DIR", r"C:\MISO_RESEARCH\01_Core_Axioms")
NOISE_DIR = os.environ.get("MISO_NOISE_DIR", r"C:\MISO_RESEARCH\00_Noise_Floor")
CURRENT_YEAR = datetime.now(timezone.utc).year


def _load_manifold() -> dict:
    with open(MANIFOLD_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifold_atomic(manifold: dict):
    """Write manifold atomically to avoid partial-write corruption."""
    dir_name = os.path.dirname(MANIFOLD_PATH)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False,
                                     suffix=".tmp", encoding="utf-8") as tmp:
        json.dump(manifold, tmp, indent=4)
        tmp_path = tmp.name
    os.replace(tmp_path, MANIFOLD_PATH)


def _audit_paper(filepath: str, keywords: list[str]) -> bool:
    """
    Return True if the paper's first two pages contain at least 2 of the
    goal-derived keywords. This is stronger than the previous single-page,
    two-keyword hardcoded check.
    """
    try:
        reader = PdfReader(filepath)
        pages_to_check = reader.pages[:2]
        text = " ".join(
            (p.extract_text() or "") for p in pages_to_check
        ).lower()
        hits = sum(1 for kw in keywords if kw in text)
        return hits >= 2
    except Exception as e:
        print(f"  [!] Audit read error: {e}")
        return False


def _build_search_query(keywords: list[str]) -> str:
    """Build an arxiv abs: query from the top goal keywords."""
    top = keywords[:4]
    if not top:
        return "abs:feedback AND abs:verification"
    return " AND ".join(f"abs:{kw}" for kw in top)


def daemon_cycle():
    active_goals = get_active_goals()
    if not active_goals:
        print("[DAEMON] No active goals. Define goals via miso_goal_kernel.py.")
        return

    keywords = get_goal_keywords()
    query = _build_search_query(keywords)

    print(f"\n[DAEMON CYCLE] Query: {query}")
    print(f"[DAEMON CYCLE] Goal keywords: {keywords[:8]}")

    os.makedirs(RESEARCH_DIR, exist_ok=True)
    os.makedirs(NOISE_DIR, exist_ok=True)

    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=5)

    manifold = _load_manifold()
    existing_titles = {a.get("axiom", "") for a in manifold.get("axioms", [])}
    new_stitches = 0

    for result in client.results(search):
        if result.published.year < CURRENT_YEAR:
            continue

        filename = f"AUTO_{result.entry_id.split('/')[-1]}.pdf"
        filepath = os.path.join(RESEARCH_DIR, filename)

        if os.path.exists(filepath):
            continue  # Already downloaded

        print(f"  [→] Detected: {result.title}")
        result.download_pdf(dirpath=RESEARCH_DIR, filename=filename)

        verified = _audit_paper(filepath, keywords)
        axiom_text = f"AUTO-STITCH [{result.entry_id}]: {result.title}"

        if verified:
            if axiom_text in existing_titles:
                print(f"  [=] Already stitched. Skipping.")
            else:
                print(f"  [✓] VERIFIED. Stitching into manifold.")
                manifold.setdefault("axioms", []).append({
                    "axiom": axiom_text,
                    "score": 0.90,
                    "source": result.entry_id,
                    "published": result.published.isoformat(),
                })
                existing_titles.add(axiom_text)
                new_stitches += 1
        else:
            print(f"  [✗] FAILED AUDIT. Sequestering to noise floor.")
            shutil.move(filepath, os.path.join(NOISE_DIR, filename))

    if new_stitches > 0:
        _save_manifold_atomic(manifold)
        print(f"\n[DAEMON] {new_stitches} new node(s) stitched.")

        # Log progress against goal that tracks ingestion
        for goal in active_goals:
            if "substrate" in goal["title"].lower() or "ingest" in goal["title"].lower():
                current = goal["progress"]["percent_complete"]
                update_progress(goal["id"], min(current + new_stitches * 2.0, 99.0),
                                note=f"Daemon stitched {new_stitches} paper(s) from query: {query}")
    else:
        print("[DAEMON] No new verified papers this cycle.")


def main():
    print("[MISO DAEMON] Starting. Press Ctrl+C to stop.")
    while True:
        try:
            daemon_cycle()
            print("[DAEMON] Cooling substrate for 300s...")
            time.sleep(300)
        except KeyboardInterrupt:
            print("\n[DAEMON] Halted by user.")
            break
        except Exception as e:
            print(f"[DAEMON ERROR] {type(e).__name__}: {e}")
            print("[DAEMON] Retrying in 60s...")
            time.sleep(60)


if __name__ == "__main__":
    main()
