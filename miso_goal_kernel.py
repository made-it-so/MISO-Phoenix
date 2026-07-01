"""
MISO Goal Kernel — the organizing center of a goal-based system.

Every autonomous loop, ingestion cycle, and synthesis operation must be
traceable back to an active goal. Without this, autonomy is drift.

This module is the single source of truth for what MISO is working toward.
All other modules should import and consult it rather than hardcoding their
own objectives.

Goal lifecycle: PENDING -> ACTIVE -> COMPLETED | FAILED | PAUSED
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional
from miso_config import MANIFOLD_PATH

GOALS_PATH = os.path.join(os.path.dirname(MANIFOLD_PATH), "miso_goals.json")


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def _new_goal(
    title: str,
    description: str,
    success_criteria: list[str],
    priority: int = 5,
    parent_id: Optional[str] = None,
) -> dict:
    return {
        "id": f"G_{uuid.uuid4().hex[:8].upper()}",
        "title": title,
        "description": description,
        "success_criteria": success_criteria,
        "status": "PENDING",
        "priority": priority,           # 1 = highest urgency
        "parent_id": parent_id,         # sub-goal linkage
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "progress": {
            "percent_complete": 0.0,
            "notes": [],
        },
    }


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _load() -> dict:
    if os.path.exists(GOALS_PATH):
        with open(GOALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"goals": []}


def _save(data: dict):
    with open(GOALS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_goal(
    title: str,
    description: str,
    success_criteria: list[str],
    priority: int = 5,
    parent_id: Optional[str] = None,
) -> dict:
    """Create and persist a new goal. Returns the goal dict."""
    data = _load()
    goal = _new_goal(title, description, success_criteria, priority, parent_id)
    data["goals"].append(goal)
    _save(data)
    print(f"[GOAL KERNEL] Created: [{goal['id']}] {title}")
    return goal


def get_active_goals() -> list[dict]:
    """Return all goals with status ACTIVE, sorted by priority."""
    data = _load()
    active = [g for g in data["goals"] if g["status"] == "ACTIVE"]
    return sorted(active, key=lambda g: g["priority"])


def get_all_goals() -> list[dict]:
    return _load()["goals"]


def activate_goal(goal_id: str) -> bool:
    data = _load()
    for goal in data["goals"]:
        if goal["id"] == goal_id:
            goal["status"] = "ACTIVE"
            goal["updated_at"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            print(f"[GOAL KERNEL] Activated: [{goal_id}] {goal['title']}")
            return True
    print(f"[GOAL KERNEL] Goal not found: {goal_id}")
    return False


def complete_goal(goal_id: str, note: str = "") -> bool:
    data = _load()
    for goal in data["goals"]:
        if goal["id"] == goal_id:
            goal["status"] = "COMPLETED"
            goal["progress"]["percent_complete"] = 100.0
            goal["updated_at"] = datetime.now(timezone.utc).isoformat()
            if note:
                goal["progress"]["notes"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "note": note,
                })
            _save(data)
            print(f"[GOAL KERNEL] Completed: [{goal_id}] {goal['title']}")
            return True
    return False


def update_progress(goal_id: str, percent: float, note: str = "") -> bool:
    """Update progress on a goal (0-100). Automatically completes at 100."""
    data = _load()
    for goal in data["goals"]:
        if goal["id"] == goal_id:
            goal["progress"]["percent_complete"] = min(100.0, max(0.0, percent))
            goal["updated_at"] = datetime.now(timezone.utc).isoformat()
            if note:
                goal["progress"]["notes"].append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "note": note,
                })
            if goal["progress"]["percent_complete"] >= 100.0:
                goal["status"] = "COMPLETED"
            _save(data)
            return True
    return False


def get_goal_keywords() -> list[str]:
    """
    Extract searchable keywords from all active goals.
    Used by autonomous loops to direct ingestion and synthesis.
    """
    active = get_active_goals()
    keywords = []
    for goal in active:
        # Pull words from title and success criteria
        words = goal["title"].lower().split()
        for criterion in goal.get("success_criteria", []):
            words += criterion.lower().split()
        # Filter to meaningful words (>4 chars, no stopwords)
        stopwords = {"with", "that", "this", "have", "from", "they", "will",
                     "been", "when", "more", "also", "than", "then", "some",
                     "each", "into", "over", "such", "make", "most", "well"}
        keywords += [w.strip(".,;:()") for w in words if len(w) > 4 and w not in stopwords]
    # Deduplicate, preserve order
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result[:20]  # Cap to prevent runaway arxiv queries


def print_status():
    """Print a human-readable summary of all goals."""
    data = _load()
    goals = data.get("goals", [])
    if not goals:
        print("[GOAL KERNEL] No goals defined. Use create_goal() to define objectives.")
        return

    status_order = {"ACTIVE": 0, "PENDING": 1, "PAUSED": 2, "COMPLETED": 3, "FAILED": 4}
    goals = sorted(goals, key=lambda g: (status_order.get(g["status"], 9), g["priority"]))

    print("\n" + "=" * 70)
    print("MISO GOAL KERNEL — ACTIVE MISSION STATE")
    print("=" * 70)
    for g in goals:
        pct = g["progress"]["percent_complete"]
        bar_len = 20
        filled = int(bar_len * pct / 100)
        bar = "█" * filled + "░" * (bar_len - filled)
        status_icon = {"ACTIVE": "▶", "PENDING": "○", "COMPLETED": "✓",
                       "FAILED": "✗", "PAUSED": "‖"}.get(g["status"], "?")
        print(f"\n  {status_icon} [{g['id']}] P{g['priority']} — {g['title']}")
        print(f"     Status : {g['status']}")
        print(f"     Progress: [{bar}] {pct:.0f}%")
        if g.get("success_criteria"):
            print(f"     Criteria: {'; '.join(g['success_criteria'][:2])}")
        if g["progress"]["notes"]:
            last = g["progress"]["notes"][-1]
            print(f"     Last note: {last['note'][:80]}")
    print("=" * 70 + "\n")


# ---------------------------------------------------------------------------
# Bootstrap: seed initial goals if the registry is empty
# ---------------------------------------------------------------------------

def _bootstrap_initial_goals():
    """Seed the goal registry with MISO's founding objectives from STATE.md."""
    data = _load()
    if data["goals"]:
        return  # Already initialized

    print("[GOAL KERNEL] Bootstrapping initial goals from STATE.md roadmap...")

    g1 = create_goal(
        title="Build Sovereign Knowledge Substrate",
        description=(
            "Ingest, audit, and structure high-quality academic and domain-specific "
            "source material into a dense, retrievable Delta Lake substrate. "
            "Retrieval must be semantic (embedding-based), not keyword-based."
        ),
        success_criteria=[
            "500+ unique, non-duplicate axiom nodes with real derivations",
            "Embedding index built and queryable",
            "Retrieval precision >0.7 on sample queries",
        ],
        priority=1,
    )

    g2 = create_goal(
        title="Achieve Semantic Retrieval",
        description=(
            "Replace LIKE-based substring search with embedding-based vector retrieval "
            "so that queries surface conceptually relevant nodes regardless of exact wording."
        ),
        success_criteria=[
            "Ollama embeddings endpoint responding",
            "All axiom nodes have stored embeddings",
            "miso_core.py uses cosine similarity for retrieval",
        ],
        priority=2,
    )

    g3 = create_goal(
        title="Autonomous Research Loop — Goal-Directed",
        description=(
            "The daemon and autonomy loops must derive their search queries and "
            "synthesis targets from active goals in the Goal Kernel, not hardcoded keywords."
        ),
        success_criteria=[
            "miso_daemon.py reads keywords from get_goal_keywords()",
            "miso_autonomy.py selects concept pairs relevant to active goals",
            "Each synthesis cycle logs progress against a goal",
        ],
        priority=3,
    )

    g4 = create_goal(
        title="Epoch VI — ECS/Fargate Deployment",
        description=(
            "Migrate the FastAPI application from single EC2 to Amazon ECS with Fargate. "
            "Define infrastructure via AWS CDK."
        ),
        success_criteria=[
            "CDK stack defined for ECS service",
            "Docker image builds and pushes cleanly",
            "Health endpoint returns 200 on Fargate",
        ],
        priority=4,
    )

    # Activate the first two
    activate_goal(g1["id"])
    activate_goal(g2["id"])
    activate_goal(g3["id"])


if __name__ == "__main__":
    _bootstrap_initial_goals()
    print_status()
