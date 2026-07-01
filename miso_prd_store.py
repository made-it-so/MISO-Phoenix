"""
MISO PRD Store — versioned, goal-linked PRD management.

Single source of truth for all PRD lifecycle operations. Both moe_router.py
and engineer_daemon.py import from here instead of managing inline SQLite.

Schema additions vs the original inline schema:
  goal_id          — FK to miso_goals.json; every PRD must serve a goal
  version          — integer, 1-based; increments when a PRD is revised
  parent_bounty_id — for revised PRDs, points back to the original
  success_criteria — JSON array of measurable completion conditions
  deployed_path    — where the generated artifact lives after deployment

Lifecycle:
  OPEN → IN_PROGRESS → COMPLETED | FAILED
  A COMPLETED bounty triggers a progress update on its linked goal.
  A revised PRD creates a new versioned row (parent_bounty_id set).
"""

import sqlite3
import json
import os
import time
from contextlib import contextmanager
from typing import Optional
from miso_config import BOUNTY_DB_PATH

# ── optional goal kernel integration (graceful if not present) ──────────────
try:
    from miso_goal_kernel import update_progress, get_all_goals
    _goal_kernel_available = True
except ImportError:
    _goal_kernel_available = False


# ── schema ───────────────────────────────────────────────────────────────────

_DDL = """
CREATE TABLE IF NOT EXISTS bounties (
    bounty_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT    NOT NULL,
    description      TEXT,
    prd_blueprint    TEXT,                       -- JSON blob
    success_criteria TEXT    DEFAULT '[]',       -- JSON array of strings
    status           TEXT    DEFAULT 'OPEN',     -- OPEN|IN_PROGRESS|COMPLETED|FAILED
    goal_id          TEXT,                       -- FK → miso_goals.json id
    version          INTEGER DEFAULT 1,
    parent_bounty_id INTEGER REFERENCES bounties(bounty_id),
    deployed_path    TEXT,
    created_at       REAL    DEFAULT (unixepoch()),
    updated_at       REAL    DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_bounties_status  ON bounties(status);
CREATE INDEX IF NOT EXISTS idx_bounties_goal_id ON bounties(goal_id);
"""


@contextmanager
def _db():
    os.makedirs(os.path.dirname(BOUNTY_DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(BOUNTY_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        conn.executescript(_DDL)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── public API ────────────────────────────────────────────────────────────────

def create_bounty(
    title: str,
    description: str,
    prd_blueprint: dict,
    goal_id: Optional[str] = None,
    success_criteria: Optional[list[str]] = None,
) -> int:
    """
    Create a new OPEN bounty. Returns the bounty_id.

    goal_id is strongly recommended — PRDs without a goal link are
    uncoupled from the system's mission.
    """
    if goal_id is None:
        print("[PRD STORE] WARNING: bounty created without a goal_id. "
              "This PRD is not linked to any active mission goal.")

    with _db() as conn:
        cur = conn.execute(
            """INSERT INTO bounties
               (title, description, prd_blueprint, goal_id, success_criteria)
               VALUES (?, ?, ?, ?, ?)""",
            (
                title,
                description,
                json.dumps(prd_blueprint),
                goal_id,
                json.dumps(success_criteria or []),
            ),
        )
        bounty_id = cur.lastrowid

    print(f"[PRD STORE] Created bounty #{bounty_id}: '{title}'"
          + (f" → goal {goal_id}" if goal_id else " (no goal linked)"))
    return bounty_id


def revise_bounty(
    parent_bounty_id: int,
    updated_blueprint: dict,
    updated_criteria: Optional[list[str]] = None,
) -> int:
    """
    Create a new version of an existing PRD.

    The parent bounty is marked SUPERSEDED; a new row is created with
    version = parent.version + 1 and parent_bounty_id set.
    Returns the new bounty_id.
    """
    with _db() as conn:
        parent = conn.execute(
            "SELECT * FROM bounties WHERE bounty_id = ?", (parent_bounty_id,)
        ).fetchone()
        if parent is None:
            raise ValueError(f"Bounty #{parent_bounty_id} not found.")

        # Mark parent superseded
        conn.execute(
            "UPDATE bounties SET status = 'SUPERSEDED', updated_at = ? WHERE bounty_id = ?",
            (time.time(), parent_bounty_id),
        )

        new_version = (parent["version"] or 1) + 1
        criteria = updated_criteria if updated_criteria is not None \
            else json.loads(parent["success_criteria"] or "[]")

        cur = conn.execute(
            """INSERT INTO bounties
               (title, description, prd_blueprint, goal_id, success_criteria,
                version, parent_bounty_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                parent["title"],
                parent["description"],
                json.dumps(updated_blueprint),
                parent["goal_id"],
                json.dumps(criteria),
                new_version,
                parent_bounty_id,
            ),
        )
        new_id = cur.lastrowid

    print(f"[PRD STORE] Revised bounty #{parent_bounty_id} → "
          f"#{new_id} (v{new_version})")
    return new_id


def claim_next_open_bounty() -> Optional[dict]:
    """
    Atomically claim the oldest OPEN bounty, setting it IN_PROGRESS.
    Returns the full row as a dict, or None if queue is empty.
    Used by engineer_daemon.
    """
    with _db() as conn:
        row = conn.execute(
            """SELECT * FROM bounties
               WHERE status = 'OPEN'
               ORDER BY bounty_id ASC
               LIMIT 1"""
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE bounties SET status = 'IN_PROGRESS', updated_at = ? WHERE bounty_id = ?",
            (time.time(), row["bounty_id"]),
        )
        result = dict(row)
        result["prd_blueprint"] = json.loads(result.get("prd_blueprint") or "{}")
        result["success_criteria"] = json.loads(result.get("success_criteria") or "[]")
    return result


def complete_bounty(bounty_id: int, deployed_path: str = "", note: str = ""):
    """
    Mark a bounty COMPLETED, record its deployed path, and close the loop
    back to the Goal Kernel — incrementing progress on the linked goal.
    """
    with _db() as conn:
        conn.execute(
            """UPDATE bounties
               SET status = 'COMPLETED', deployed_path = ?, updated_at = ?
               WHERE bounty_id = ?""",
            (deployed_path, time.time(), bounty_id),
        )
        row = conn.execute(
            "SELECT goal_id, title, success_criteria FROM bounties WHERE bounty_id = ?",
            (bounty_id,),
        ).fetchone()

    if row is None:
        return

    print(f"[PRD STORE] Bounty #{bounty_id} COMPLETED: '{row['title']}'")

    # ── close the loop to the Goal Kernel ────────────────────────────────────
    goal_id = row["goal_id"]
    if goal_id and _goal_kernel_available:
        criteria = json.loads(row["success_criteria"] or "[]")
        progress_note = note or f"PRD bounty #{bounty_id} ('{row['title']}') deployed to {deployed_path or 'unknown path'}."
        if criteria:
            progress_note += f" Criteria covered: {'; '.join(criteria[:2])}"
        # Each completed bounty advances the goal by 20% (capped at 99 — human confirms 100)
        update_progress(goal_id, _calculate_goal_progress(goal_id, increment=20.0),
                        note=progress_note)
        print(f"[PRD STORE] Goal {goal_id} progress updated.")
    elif goal_id and not _goal_kernel_available:
        print(f"[PRD STORE] WARNING: Goal kernel unavailable. "
              f"Goal {goal_id} not updated for bounty #{bounty_id}.")


def fail_bounty(bounty_id: int, reason: str = ""):
    with _db() as conn:
        conn.execute(
            "UPDATE bounties SET status = 'FAILED', updated_at = ? WHERE bounty_id = ?",
            (time.time(), bounty_id),
        )
    print(f"[PRD STORE] Bounty #{bounty_id} FAILED. Reason: {reason or 'unspecified'}")


def get_bounty(bounty_id: int) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM bounties WHERE bounty_id = ?", (bounty_id,)
        ).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["prd_blueprint"] = json.loads(result.get("prd_blueprint") or "{}")
    result["success_criteria"] = json.loads(result.get("success_criteria") or "[]")
    return result


def get_bounties_for_goal(goal_id: str) -> list[dict]:
    """Return all bounties (any status) linked to a goal, newest first."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM bounties WHERE goal_id = ? ORDER BY bounty_id DESC",
            (goal_id,),
        ).fetchall()
    results = []
    for row in rows:
        r = dict(row)
        r["prd_blueprint"] = json.loads(r.get("prd_blueprint") or "{}")
        r["success_criteria"] = json.loads(r.get("success_criteria") or "[]")
        results.append(r)
    return results


def get_bounty_log_path(bounty_id: int) -> str:
    log_dir = os.path.join(os.path.dirname(BOUNTY_DB_PATH), "bounty_logs")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"bounty_{bounty_id}.log")


def print_board():
    """Print a human-readable view of the bounty board."""
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM bounties ORDER BY bounty_id DESC LIMIT 20"
        ).fetchall()

    if not rows:
        print("[PRD STORE] Bounty board is empty.")
        return

    print("\n" + "=" * 70)
    print("MISO BOUNTY BOARD — PRD QUEUE")
    print("=" * 70)
    status_icons = {"OPEN": "○", "IN_PROGRESS": "▶", "COMPLETED": "✓",
                    "FAILED": "✗", "SUPERSEDED": "↑"}
    for row in rows:
        icon = status_icons.get(row["status"], "?")
        goal_str = f" → {row['goal_id']}" if row["goal_id"] else " (no goal)"
        ver_str = f" v{row['version']}" if row["version"] and row["version"] > 1 else ""
        print(f"  {icon} #{row['bounty_id']}{ver_str} [{row['status']}]{goal_str} — {row['title']}")
        if row["deployed_path"]:
            print(f"      deployed → {row['deployed_path']}")
    print("=" * 70 + "\n")


# ── helpers ───────────────────────────────────────────────────────────────────

def _calculate_goal_progress(goal_id: str, increment: float) -> float:
    """Return new progress % for a goal, capped at 99 (human confirms 100)."""
    if not _goal_kernel_available:
        return increment
    goals = get_all_goals()
    for g in goals:
        if g["id"] == goal_id:
            current = g["progress"]["percent_complete"]
            return min(current + increment, 99.0)
    return increment


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print_board()
