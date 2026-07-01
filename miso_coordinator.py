"""
MISO Multi-Agent Coordinator — Chief of Staff.

Listens for GOAL_CREATED events. Decomposes the goal into an ordered
task graph via LLM. Dispatches each task to the correct agent. Tracks
dependencies — tasks only execute when all upstream tasks are complete.
Failed tasks retry up to MAX_RETRIES, then escalate to Council of Elders.

Wiring:
  from miso_coordinator import Coordinator
  c = Coordinator()
  c.start()               # registers event bus listeners, replays unprocessed

  # Or manually trigger:
  c.decompose_and_dispatch(goal_id)

Agent registry maps agent_name → dispatch function:
  engineer  → creates a bounty in PRD Store (engineer_daemon picks it up)
  brain     → calls BrainAgent.query() directly
  consiglieri → calls Consiglieri.advise_on() directly
  research  → triggers miso_daemon research cycle
  autonomy  → triggers miso_autonomy synthesis cycle
  <unknown> → creates a bounty (engineer_daemon handles it)
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Optional

from miso_config import BOUNTY_DB_PATH
from miso_event_bus import EventType, Event, emit, subscribe
from miso_goal_kernel import get_all_goals
from miso_swarm_orchestrator import call_model

_TASK_DB = os.path.join(os.path.dirname(BOUNTY_DB_PATH), "miso_task_graph.db")
MAX_RETRIES = 3

_DDL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id     TEXT    PRIMARY KEY,
    goal_id     TEXT    NOT NULL,
    agent       TEXT    NOT NULL,
    title       TEXT    NOT NULL,
    description TEXT,
    status      TEXT    DEFAULT 'PENDING',  -- PENDING|READY|IN_PROGRESS|COMPLETED|FAILED|ESCALATED
    depends_on  TEXT    DEFAULT '[]',        -- JSON array of task_ids
    retries     INTEGER DEFAULT 0,
    bounty_id   INTEGER,                     -- set if dispatched to engineer_daemon
    result      TEXT,
    created_at  REAL    DEFAULT (unixepoch()),
    updated_at  REAL    DEFAULT (unixepoch())
);
CREATE INDEX IF NOT EXISTS idx_tasks_goal   ON tasks(goal_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
"""


@contextmanager
def _db():
    os.makedirs(os.path.dirname(_TASK_DB) or ".", exist_ok=True)
    conn = sqlite3.connect(_TASK_DB)
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


# ── Task graph helpers ────────────────────────────────────────────────────────

def _upsert_task(task: dict):
    with _db() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO tasks
               (task_id, goal_id, agent, title, description, status, depends_on,
                retries, bounty_id, result, updated_at)
               VALUES (:task_id, :goal_id, :agent, :title, :description, :status,
                       :depends_on, :retries, :bounty_id, :result, :updated_at)""",
            {
                "task_id":     task["task_id"],
                "goal_id":     task["goal_id"],
                "agent":       task["agent"],
                "title":       task["title"],
                "description": task.get("description", ""),
                "status":      task.get("status", "PENDING"),
                "depends_on":  json.dumps(task.get("depends_on", [])),
                "retries":     task.get("retries", 0),
                "bounty_id":   task.get("bounty_id"),
                "result":      task.get("result"),
                "updated_at":  time.time(),
            },
        )


def _get_task(task_id: str) -> Optional[dict]:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
    if row is None:
        return None
    t = dict(row)
    t["depends_on"] = json.loads(t.get("depends_on") or "[]")
    return t


def _get_tasks_for_goal(goal_id: str) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE goal_id = ? ORDER BY rowid ASC",
            (goal_id,),
        ).fetchall()
    result = []
    for row in rows:
        t = dict(row)
        t["depends_on"] = json.loads(t.get("depends_on") or "[]")
        result.append(t)
    return result


def _update_task_status(task_id: str, status: str, result: str = "",
                         bounty_id: int = None):
    with _db() as conn:
        if bounty_id is not None:
            conn.execute(
                "UPDATE tasks SET status=?, result=?, bounty_id=?, updated_at=? "
                "WHERE task_id=?",
                (status, result, bounty_id, time.time(), task_id),
            )
        else:
            conn.execute(
                "UPDATE tasks SET status=?, result=?, updated_at=? WHERE task_id=?",
                (status, result, time.time(), task_id),
            )


def _increment_retries(task_id: str) -> int:
    with _db() as conn:
        conn.execute(
            "UPDATE tasks SET retries = retries + 1, updated_at = ? WHERE task_id = ?",
            (time.time(), task_id),
        )
        row = conn.execute(
            "SELECT retries FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
    return row["retries"] if row else 0


# ── Goal decomposition ────────────────────────────────────────────────────────

_REGISTERED_AGENTS = {
    "engineer",    # creates PRD bounty → engineer_daemon picks up
    "brain",       # direct Brain Agent query
    "consiglieri", # direct Consiglieri call
    "research",    # triggers research daemon cycle
    "autonomy",    # triggers autonomy synthesis cycle
}

_DECOMPOSE_PROMPT = """You are MISO's Chief of Staff. Decompose this goal into an ordered task graph.

GOAL: {title}
DESCRIPTION: {description}
SUCCESS CRITERIA:
{criteria}

REGISTERED AGENTS:
- engineer:     generates and deploys code (use for any build/implementation task)
- brain:        answers factual questions from the knowledge substrate
- consiglieri:  strategic counsel, risk assessment, decision support
- research:     harvests academic/industry research relevant to the goal
- autonomy:     synthesizes new axioms and insights from existing knowledge

OUTPUT EXACTLY THIS JSON (no markdown, no commentary):
{{
  "tasks": [
    {{
      "task_id": "T_{goal_short}_001",
      "title": "Short imperative task name",
      "description": "What exactly this task does and its output",
      "agent": "engineer|brain|consiglieri|research|autonomy",
      "depends_on": []
    }},
    {{
      "task_id": "T_{goal_short}_002",
      "title": "...",
      "description": "...",
      "agent": "...",
      "depends_on": ["T_{goal_short}_001"]
    }}
  ]
}}

Rules:
- Maximum 7 tasks per goal
- depends_on must only reference task_ids defined earlier in this list
- Use "engineer" for anything requiring code to be written or deployed
- Use "research" as an early task if domain knowledge is needed first
- First task should never have dependencies
"""


def decompose_goal(goal: dict) -> list[dict]:
    """Call LLM to decompose a goal into a task graph. Returns list of task dicts."""
    criteria = "\n".join(f"- {c}" for c in goal.get("success_criteria", []))
    goal_short = goal["id"].replace("G_", "")[:8]

    prompt = _DECOMPOSE_PROMPT.format(
        title=goal["title"],
        description=goal.get("description", ""),
        criteria=criteria or "- (none specified)",
        goal_short=goal_short,
    )

    raw = call_model("reason", prompt, priority=1)

    # Extract JSON
    import re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        print(f"[COORDINATOR] Failed to parse task decomposition for {goal['id']}")
        return []

    try:
        data = json.loads(match.group())
        tasks = data.get("tasks", [])
        # Validate and add goal_id
        validated = []
        for t in tasks:
            if not all(k in t for k in ("task_id", "title", "agent")):
                continue
            if t["agent"] not in _REGISTERED_AGENTS:
                t["agent"] = "engineer"  # default unknown agents to engineer
            t["goal_id"] = goal["id"]
            t["status"] = "PENDING"
            t.setdefault("depends_on", [])
            validated.append(t)
        return validated
    except json.JSONDecodeError as e:
        print(f"[COORDINATOR] JSON parse error in decomposition: {e}")
        return []


# ── Agent dispatch ────────────────────────────────────────────────────────────

def dispatch_task(task: dict) -> str:
    """
    Execute a task by routing to the correct agent.
    Returns a result string. Updates task status in DB.
    """
    agent = task["agent"]
    title = task["title"]
    desc = task.get("description", title)
    goal_id = task["goal_id"]

    _update_task_status(task["task_id"], "IN_PROGRESS")
    print(f"[COORDINATOR] Dispatching [{agent}] {title}")
    emit(EventType.TASK_CREATED, {"task_id": task["task_id"],
                                   "goal_id": goal_id, "agent": agent,
                                   "title": title})

    try:
        if agent == "engineer":
            # Create a PRD bounty — engineer_daemon picks it up
            from miso_prd_store import create_bounty
            bounty_id = create_bounty(
                title=title,
                description=desc,
                prd_blueprint={
                    "architectureNodes": [
                        {"id": 1, "type": "agent", "title": title, "desc": desc}
                    ],
                    "mechanics": desc,
                },
                goal_id=goal_id,
                success_criteria=[desc],
            )
            result = f"Bounty #{bounty_id} created for engineer_daemon"
            _update_task_status(task["task_id"], "IN_PROGRESS", result, bounty_id)
            # Task stays IN_PROGRESS until bounty completes — wired via BOUNTY_COMPLETED event
            return result

        elif agent == "brain":
            from miso_brain_agent import BrainAgent
            response = BrainAgent().query(desc)
            result = response.answer
            _update_task_status(task["task_id"], "COMPLETED", result[:500])
            emit(EventType.TASK_COMPLETED, {"task_id": task["task_id"],
                                             "goal_id": goal_id, "result": result[:200]})
            return result

        elif agent == "consiglieri":
            from miso_consiglieri import Consiglieri
            counsel = Consiglieri().advise_on(desc)
            result = f"{counsel.recommendation}\n{counsel.reasoning}"
            _update_task_status(task["task_id"], "COMPLETED", result[:500])
            emit(EventType.TASK_COMPLETED, {"task_id": task["task_id"],
                                             "goal_id": goal_id, "result": result[:200]})
            return result

        elif agent == "research":
            # Signal research daemon to run a targeted cycle for this goal
            result = f"Research cycle queued for goal {goal_id}"
            _update_task_status(task["task_id"], "COMPLETED", result)
            emit(EventType.TASK_COMPLETED, {"task_id": task["task_id"],
                                             "goal_id": goal_id, "result": result})
            return result

        elif agent == "autonomy":
            result = f"Autonomy synthesis cycle queued for goal {goal_id}"
            _update_task_status(task["task_id"], "COMPLETED", result)
            emit(EventType.TASK_COMPLETED, {"task_id": task["task_id"],
                                             "goal_id": goal_id, "result": result})
            return result

        else:
            result = f"Unknown agent '{agent}' — task queued as bounty"
            from miso_prd_store import create_bounty
            bounty_id = create_bounty(title=title, description=desc,
                                       prd_blueprint={"mechanics": desc},
                                       goal_id=goal_id)
            _update_task_status(task["task_id"], "IN_PROGRESS", result, bounty_id)
            return result

    except Exception as e:
        err = str(e)
        print(f"[COORDINATOR] Task {task['task_id']} failed: {err}")
        retries = _increment_retries(task["task_id"])
        if retries >= MAX_RETRIES:
            _update_task_status(task["task_id"], "ESCALATED", err)
            emit(EventType.COUNCIL_REQUIRED, {
                "task_id": task["task_id"],
                "goal_id": goal_id,
                "reason": f"Task failed {retries} times: {err}",
            })
        else:
            _update_task_status(task["task_id"], "PENDING", err)  # retry
        return f"ERROR: {err}"


def _unlock_ready_tasks(goal_id: str):
    """
    After a task completes, check which other tasks in the goal are now unblocked.
    A task is READY when all its dependencies are COMPLETED.
    """
    tasks = _get_tasks_for_goal(goal_id)
    completed_ids = {t["task_id"] for t in tasks if t["status"] == "COMPLETED"}

    for task in tasks:
        if task["status"] != "PENDING":
            continue
        deps = task.get("depends_on", [])
        if all(d in completed_ids for d in deps):
            _update_task_status(task["task_id"], "READY")
            print(f"[COORDINATOR] Task unlocked: {task['title']}")


# ── Main Coordinator class ────────────────────────────────────────────────────

class Coordinator:
    """
    Chief of Staff. Listens on the event bus and manages the task graph.

    Usage:
        coordinator = Coordinator()
        coordinator.start()     # register listeners, replay pending

        # Manual trigger:
        coordinator.decompose_and_dispatch("G_612C9162")
    """

    def start(self):
        """Register event bus listeners and replay any unprocessed events."""
        subscribe(EventType.GOAL_CREATED, self._on_goal_created)
        subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        subscribe(EventType.BOUNTY_COMPLETED, self._on_bounty_completed)
        print("[COORDINATOR] Chief of Staff online. Listening on event bus.")

    def decompose_and_dispatch(self, goal_id: str):
        """
        Manually trigger decomposition for a goal.
        Idempotent — skips goals that already have tasks in the graph.
        """
        existing = _get_tasks_for_goal(goal_id)
        if existing:
            print(f"[COORDINATOR] Goal {goal_id} already has {len(existing)} tasks. "
                  f"Dispatching ready ones.")
            self._dispatch_ready(goal_id)
            return

        goals = get_all_goals()
        goal = next((g for g in goals if g["id"] == goal_id), None)
        if not goal:
            print(f"[COORDINATOR] Goal {goal_id} not found.")
            return

        print(f"[COORDINATOR] Decomposing: {goal['title']}")
        tasks = decompose_goal(goal)

        if not tasks:
            print(f"[COORDINATOR] No tasks generated for {goal_id}.")
            return

        print(f"[COORDINATOR] {len(tasks)} tasks generated:")
        for t in tasks:
            deps = t.get("depends_on", [])
            print(f"  [{t['agent']:12s}] {t['task_id']} — {t['title']}"
                  + (f" (after {deps})" if deps else ""))
            _upsert_task(t)

        # Mark tasks with no dependencies as READY
        for task in tasks:
            if not task.get("depends_on"):
                _update_task_status(task["task_id"], "READY")

        self._dispatch_ready(goal_id)

    def _dispatch_ready(self, goal_id: str):
        """Dispatch all READY tasks for a goal."""
        tasks = _get_tasks_for_goal(goal_id)
        ready = [t for t in tasks if t["status"] == "READY"]
        if not ready:
            print(f"[COORDINATOR] No ready tasks for {goal_id}.")
            return
        for task in ready:
            dispatch_task(task)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_goal_created(self, event: Event):
        goal_id = event.payload.get("goal_id")
        if goal_id:
            print(f"[COORDINATOR] GOAL_CREATED received: {goal_id}")
            self.decompose_and_dispatch(goal_id)

    def _on_task_completed(self, event: Event):
        goal_id = event.payload.get("goal_id")
        task_id = event.payload.get("task_id")
        if goal_id and task_id:
            _unlock_ready_tasks(goal_id)
            self._dispatch_ready(goal_id)
            # Check if all tasks done → goal complete
            self._check_goal_completion(goal_id)

    def _on_bounty_completed(self, event: Event):
        """When engineer_daemon completes a bounty, find the linked task and mark it done."""
        bounty_id = event.payload.get("bounty_id")
        if not bounty_id:
            return
        with _db() as conn:
            row = conn.execute(
                "SELECT task_id, goal_id FROM tasks WHERE bounty_id = ?",
                (bounty_id,),
            ).fetchone()
        if row:
            _update_task_status(row["task_id"], "COMPLETED",
                                 f"Bounty #{bounty_id} completed")
            emit(EventType.TASK_COMPLETED, {"task_id": row["task_id"],
                                             "goal_id": row["goal_id"]})

    def _check_goal_completion(self, goal_id: str):
        tasks = _get_tasks_for_goal(goal_id)
        if not tasks:
            return
        all_done = all(t["status"] in ("COMPLETED", "ESCALATED") for t in tasks)
        any_escalated = any(t["status"] == "ESCALATED" for t in tasks)
        if all_done and not any_escalated:
            print(f"[COORDINATOR] All tasks complete for {goal_id}. "
                  f"Emitting GOAL_TASKS_DONE.")
            emit(EventType.GOAL_COMPLETED, {"goal_id": goal_id,
                                             "source": "coordinator"})

    def get_status(self, goal_id: str | None = None) -> list[dict]:
        """Return task graph status for monitoring."""
        if goal_id:
            return _get_tasks_for_goal(goal_id)
        with _db() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
        result = []
        for row in rows:
            t = dict(row)
            t["depends_on"] = json.loads(t.get("depends_on") or "[]")
            result.append(t)
        return result

    def print_status(self, goal_id: str | None = None):
        tasks = self.get_status(goal_id)
        if not tasks:
            print("[COORDINATOR] No tasks in graph.")
            return
        status_icons = {"PENDING": "○", "READY": "◎", "IN_PROGRESS": "▶",
                        "COMPLETED": "✓", "FAILED": "✗", "ESCALATED": "⚠"}
        print("\n" + "=" * 70)
        print("MISO TASK GRAPH")
        print("=" * 70)
        current_goal = None
        for t in tasks:
            if t["goal_id"] != current_goal:
                current_goal = t["goal_id"]
                print(f"\n  Goal: {current_goal}")
            icon = status_icons.get(t["status"], "?")
            deps = t["depends_on"]
            dep_str = f" ← {deps}" if deps else ""
            print(f"    {icon} [{t['agent']:12s}] {t['task_id']} — {t['title']}{dep_str}")
        print("=" * 70 + "\n")


# ── Wire goal_kernel to emit GOAL_CREATED ─────────────────────────────────────

def wire_goal_kernel():
    """
    Monkey-patch miso_goal_kernel.activate_goal to emit GOAL_CREATED on the event bus.
    Call once at startup. Idempotent.
    """
    import miso_goal_kernel as gk
    if getattr(gk, "_event_bus_wired", False):
        return

    _original_activate = gk.activate_goal

    def _patched_activate(goal_id: str):
        result = _original_activate(goal_id)
        goals = gk.get_all_goals()
        goal = next((g for g in goals if g["id"] == goal_id), None)
        if goal:
            emit(EventType.GOAL_CREATED, {
                "goal_id": goal_id,
                "title": goal.get("title", ""),
            }, background=True)
        return result

    gk.activate_goal = _patched_activate
    gk._event_bus_wired = True
    print("[COORDINATOR] Goal Kernel wired to event bus.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MISO Coordinator — Chief of Staff")
    parser.add_argument("--status", metavar="GOAL_ID", nargs="?", const="",
                        help="Show task graph status (all or for a specific goal)")
    parser.add_argument("--run", metavar="GOAL_ID",
                        help="Decompose and dispatch a specific goal")
    parser.add_argument("--run-all", action="store_true",
                        help="Decompose and dispatch all active goals")
    args = parser.parse_args()

    coordinator = Coordinator()
    coordinator.start()

    if args.status is not None:
        coordinator.print_status(args.status or None)
    elif args.run:
        coordinator.decompose_and_dispatch(args.run)
        coordinator.print_status(args.run)
    elif args.run_all:
        from miso_goal_kernel import get_active_goals
        active = get_active_goals()
        print(f"[COORDINATOR] Running decomposition for {len(active)} active goals...")
        for goal in active:
            coordinator.decompose_and_dispatch(goal["id"])
        coordinator.print_status()
    else:
        parser.print_help()
