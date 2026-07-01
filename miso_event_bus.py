"""
MISO Event Bus — typed pub/sub backbone for inter-agent communication.

All agents communicate via events. No agent calls another directly.

Usage:
    from miso_event_bus import emit, subscribe, EventType

    # Subscribe (at module load time)
    subscribe(EventType.GOAL_CREATED, my_handler)

    # Emit from anywhere
    emit(EventType.GOAL_CREATED, {"goal_id": "G_123", "title": "..."})

Events are persisted to SQLite so they survive process restarts and
can be replayed. Handlers run synchronously in the emitting thread.
For async dispatch, use emit(..., background=True).
"""
import json
import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from miso_config import BOUNTY_DB_PATH

_EVENT_DB = os.path.join(os.path.dirname(BOUNTY_DB_PATH), "miso_events.db")

_DDL = """
CREATE TABLE IF NOT EXISTS events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type  TEXT    NOT NULL,
    payload     TEXT    DEFAULT '{}',
    emitted_at  REAL    DEFAULT (unixepoch()),
    processed   INTEGER DEFAULT 0,
    error       TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_type       ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_processed  ON events(processed);
"""


class EventType(str, Enum):
    # Goal lifecycle
    GOAL_CREATED          = "GOAL_CREATED"
    GOAL_COMPLETED        = "GOAL_COMPLETED"
    GOAL_FAILED           = "GOAL_FAILED"
    GOAL_PROGRESS         = "GOAL_PROGRESS"
    # Bounty / PRD lifecycle
    BOUNTY_CREATED        = "BOUNTY_CREATED"
    BOUNTY_CLAIMED        = "BOUNTY_CLAIMED"
    BOUNTY_COMPLETED      = "BOUNTY_COMPLETED"
    BOUNTY_FAILED         = "BOUNTY_FAILED"
    # Coordinator
    TASK_CREATED          = "TASK_CREATED"
    TASK_COMPLETED        = "TASK_COMPLETED"
    TASK_FAILED           = "TASK_FAILED"
    COUNCIL_REQUIRED      = "COUNCIL_REQUIRED"
    # Research / knowledge
    TRANSCRIPT_READY      = "TRANSCRIPT_READY"
    TRAVEL_TRIGGER        = "TRAVEL_TRIGGER"
    FLIGHT_BOOKED         = "FLIGHT_BOOKED"
    HOTEL_BOOKED          = "HOTEL_BOOKED"
    RESTAURANT_BOOKED     = "RESTAURANT_BOOKED"
    BENCHMARK_COMPLETE    = "BENCHMARK_COMPLETE"
    INQUISITOR_FINDING    = "INQUISITOR_FINDING"


@dataclass
class Event:
    type: EventType
    payload: dict = field(default_factory=dict)
    event_id: int = 0
    emitted_at: float = 0.0


# ── Registry ──────────────────────────────────────────────────────────────────

_handlers: dict[str, list[Callable]] = {}
_lock = threading.Lock()


def subscribe(event_type: EventType, handler: Callable[[Event], None]):
    """Register a handler for an event type. Called at module load time."""
    key = str(event_type)
    with _lock:
        _handlers.setdefault(key, []).append(handler)


def unsubscribe(event_type: EventType, handler: Callable):
    key = str(event_type)
    with _lock:
        handlers = _handlers.get(key, [])
        if handler in handlers:
            handlers.remove(handler)


# ── Storage ───────────────────────────────────────────────────────────────────

@contextmanager
def _db():
    os.makedirs(os.path.dirname(_EVENT_DB) or ".", exist_ok=True)
    conn = sqlite3.connect(_EVENT_DB)
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


def _persist(event_type: str, payload: dict) -> int:
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO events (event_type, payload) VALUES (?, ?)",
            (event_type, json.dumps(payload)),
        )
        return cur.lastrowid


def _mark_processed(event_id: int, error: str = ""):
    with _db() as conn:
        conn.execute(
            "UPDATE events SET processed = 1, error = ? WHERE event_id = ?",
            (error or None, event_id),
        )


# ── Emit ──────────────────────────────────────────────────────────────────────

def emit(event_type: EventType, payload: dict | None = None,
         background: bool = False) -> int:
    """
    Emit an event. Persists to DB, then calls all registered handlers.

    background=True: dispatch handlers in a daemon thread (non-blocking).
    Returns the event_id.
    """
    payload = payload or {}
    event_id = _persist(str(event_type), payload)
    event = Event(type=event_type, payload=payload, event_id=event_id,
                  emitted_at=time.time())

    if background:
        t = threading.Thread(target=_dispatch, args=(event,), daemon=True)
        t.start()
    else:
        _dispatch(event)

    return event_id


def _dispatch(event: Event):
    key = str(event.type)
    with _lock:
        handlers = list(_handlers.get(key, []))

    errors = []
    for handler in handlers:
        try:
            handler(event)
        except Exception as e:
            errors.append(str(e))
            print(f"[EVENT BUS] Handler {handler.__name__} failed for {key}: {e}")

    _mark_processed(event.event_id, error="; ".join(errors) if errors else "")


# ── Replay ────────────────────────────────────────────────────────────────────

def replay_unprocessed(event_type: EventType | None = None, limit: int = 100):
    """
    Re-dispatch any events that were persisted but never processed.
    Call on startup to handle events from a crashed previous run.
    """
    with _db() as conn:
        if event_type:
            rows = conn.execute(
                "SELECT * FROM events WHERE processed = 0 AND event_type = ? "
                "ORDER BY event_id ASC LIMIT ?",
                (str(event_type), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events WHERE processed = 0 "
                "ORDER BY event_id ASC LIMIT ?",
                (limit,),
            ).fetchall()

    print(f"[EVENT BUS] Replaying {len(rows)} unprocessed events...")
    for row in rows:
        event = Event(
            type=EventType(row["event_type"]),
            payload=json.loads(row["payload"] or "{}"),
            event_id=row["event_id"],
            emitted_at=row["emitted_at"],
        )
        _dispatch(event)


def get_recent_events(event_type: EventType | None = None,
                      limit: int = 50) -> list[dict]:
    """Return recent events for monitoring/debugging."""
    with _db() as conn:
        if event_type:
            rows = conn.execute(
                "SELECT * FROM events WHERE event_type = ? "
                "ORDER BY event_id DESC LIMIT ?",
                (str(event_type), limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY event_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(r) for r in rows]
