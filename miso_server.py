"""
MISO MCP Gateway — exposes MISO's core capabilities as MCP tools.

Run:
    python miso_server.py               # SSE transport (default, for Claude Code)
    python miso_server.py --stdio       # stdio transport (for Claude Desktop)

Every MISO capability is an MCP tool so any MCP client (Claude Code, Claude Desktop,
or any third-party agent) can call them directly without a REST wrapper.

Tools exposed:
  Goal Kernel:    create_goal, list_goals, get_goal, complete_goal
  Brain Agent:    ask_brain
  Consiglieri:    get_counsel, audit_action, detect_blind_spots, live_call_support
  PRD Store:      create_bounty, list_bounties, complete_bounty, fail_bounty
  Session Search: search_sessions
  Coordinator:    run_coordinator, coordinator_status
"""
import argparse
from fastmcp import FastMCP

mcp = FastMCP("MISO_Sovereign_Gateway")


# ── Goal Kernel ────────────────────────────────────────────────────────────────

@mcp.tool()
def create_goal(title: str, description: str, priority: int = 2,
                success_criteria: list[str] | None = None,
                parent_id: str | None = None) -> dict:
    """
    Create and activate a new goal in the MISO Goal Kernel.
    Returns the created goal dict including its generated ID.
    priority: 1=critical, 2=high, 3=normal.
    """
    from miso_goal_kernel import create_goal as _create, activate_goal
    goal = _create(
        title=title,
        description=description,
        priority=priority,
        success_criteria=success_criteria or [],
        parent_id=parent_id,
    )
    activate_goal(goal["id"])
    return goal


@mcp.tool()
def list_goals(status: str = "ACTIVE") -> list[dict]:
    """
    List goals from the Goal Kernel filtered by status.
    status options: ACTIVE, PENDING, COMPLETED, FAILED, PAUSED, or ALL.
    """
    from miso_goal_kernel import get_all_goals, get_active_goals
    if status.upper() == "ALL":
        return get_all_goals()
    if status.upper() == "ACTIVE":
        return get_active_goals()
    all_goals = get_all_goals()
    return [g for g in all_goals if g.get("status", "").upper() == status.upper()]


@mcp.tool()
def get_goal(goal_id: str) -> dict | None:
    """Retrieve a single goal by ID. Returns None if not found."""
    from miso_goal_kernel import get_all_goals
    for g in get_all_goals():
        if g["id"] == goal_id:
            return g
    return None


@mcp.tool()
def complete_goal(goal_id: str, note: str = "") -> str:
    """Mark a goal as COMPLETED. Returns confirmation message."""
    from miso_goal_kernel import complete_goal as _complete
    _complete(goal_id, note=note)
    return f"Goal {goal_id} marked COMPLETED."


# ── Brain Agent ────────────────────────────────────────────────────────────────

@mcp.tool()
def ask_brain(question: str) -> dict:
    """
    Ask the MISO Brain Agent a question grounded in the knowledge substrate.
    Returns: { answer, sources, grounded (bool), confidence, goal_context }
    The Brain Agent refuses to hallucinate — if substrate is insufficient it
    explicitly says so and marks the answer as a hypothesis.
    """
    from miso_brain_agent import BrainAgent
    agent = BrainAgent()
    response = agent.query(question)
    return {
        "answer": response.answer,
        "sources": response.sources,
        "grounded": response.grounded,
        "confidence": response.confidence,
        "goal_context": response.goal_context,
    }


# ── Consiglieri ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_counsel(question: str) -> dict:
    """
    Ask the Consiglieri for strategic counsel on a question or decision.
    Returns: { recommendation, reasoning, risks, priority_goal }
    Counsel is grounded in the active goal set.
    """
    from miso_consiglieri import Consiglieri
    c = Consiglieri()
    result = c.advise_on(question)
    return {
        "recommendation": result.recommendation,
        "reasoning": result.reasoning,
        "risks": result.risks,
        "priority_goal": result.priority_goal,
    }


@mcp.tool()
def audit_action(proposed_action: str) -> dict:
    """
    Ask the Consiglieri to audit a proposed action before taking it.
    Returns: { recommendation (PROCEED/MODIFY/ABORT), reasoning, risks, priority_goal }
    Use before any irreversible or high-risk operation.
    """
    from miso_consiglieri import Consiglieri
    c = Consiglieri()
    result = c.audit_action(proposed_action)
    return {
        "recommendation": result.recommendation,
        "reasoning": result.reasoning,
        "risks": result.risks,
        "priority_goal": result.priority_goal,
    }


@mcp.tool()
def detect_blind_spots() -> str:
    """
    Ask the Consiglieri to identify blind spots in the current active goals.
    Returns a structured analysis of: unmeasurable criteria, goal conflicts,
    missing prerequisites, and goals the system should be working toward but isn't.
    """
    from miso_consiglieri import Consiglieri
    return Consiglieri().detect_blind_spots()


@mcp.tool()
def live_call_support(transcript: str, question: str | None = None,
                      prospect_name: str | None = None,
                      company: str | None = None,
                      deal_stage: str | None = None) -> str:
    """
    Get real-time tactical counsel during a sales call.
    transcript: accumulated transcript text so far.
    question: specific question, or leave blank for auto-brief (top 3 things to act on).
    Returns 3-5 bullet points, immediately actionable.
    Flags: TRAVEL TRIGGER, BUYING SIGNAL, OBJECTION if detected.
    Uses frontier models (Claude/GPT-4o) for ~3s latency when API keys present.
    """
    from miso_consiglieri import Consiglieri
    call_context = {}
    if prospect_name:
        call_context["prospect_name"] = prospect_name
    if company:
        call_context["company"] = company
    if deal_stage:
        call_context["stage"] = deal_stage
    return Consiglieri().live_counsel(transcript, question=question,
                                      call_context=call_context or None)


@mcp.tool()
def scan_transcript_chunk(chunk: str) -> dict:
    """
    Lightweight scan of a 30s transcript chunk for triggers (zero LLM cost).
    Returns detected triggers: { travel, buying, objection, structured }
    Only calls LLM if a regex pattern fires first.
    """
    from miso_consiglieri import Consiglieri
    return Consiglieri().watch_for_triggers(chunk)


# ── PRD Store ──────────────────────────────────────────────────────────────────

@mcp.tool()
def create_bounty(title: str, description: str, prd_blueprint: dict,
                  goal_id: str | None = None,
                  success_criteria: list[str] | None = None) -> int:
    """
    Create an OPEN bounty on the PRD bounty board for the engineer daemon.
    goal_id links this PRD to an active Goal Kernel goal (strongly recommended).
    Returns the bounty_id.
    """
    from miso_prd_store import create_bounty as _create
    return _create(title=title, description=description,
                   prd_blueprint=prd_blueprint, goal_id=goal_id,
                   success_criteria=success_criteria)


@mcp.tool()
def list_bounties(status: str = "OPEN") -> list[dict]:
    """
    List bounties from the PRD board.
    status: OPEN, IN_PROGRESS, COMPLETED, FAILED, or ALL (last 20).
    """
    from miso_prd_store import _db
    import json as _json
    with _db() as conn:
        if status.upper() == "ALL":
            rows = conn.execute(
                "SELECT * FROM bounties ORDER BY bounty_id DESC LIMIT 20"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM bounties WHERE status = ? ORDER BY bounty_id DESC",
                (status.upper(),)
            ).fetchall()
    results = []
    for row in rows:
        r = dict(row)
        r["prd_blueprint"] = _json.loads(r.get("prd_blueprint") or "{}")
        r["success_criteria"] = _json.loads(r.get("success_criteria") or "[]")
        results.append(r)
    return results


@mcp.tool()
def mark_bounty_complete(bounty_id: int, deployed_path: str = "",
                         note: str = "") -> str:
    """
    Mark a bounty COMPLETED and close the loop to the Goal Kernel.
    Increments progress on the linked goal.
    """
    from miso_prd_store import complete_bounty as _complete
    _complete(bounty_id, deployed_path=deployed_path, note=note)
    return f"Bounty #{bounty_id} marked COMPLETED."


@mcp.tool()
def mark_bounty_failed(bounty_id: int, reason: str = "") -> str:
    """Mark a bounty FAILED with an optional reason."""
    from miso_prd_store import fail_bounty as _fail
    _fail(bounty_id, reason=reason)
    return f"Bounty #{bounty_id} marked FAILED. Reason: {reason or 'unspecified'}"


# ── Session Search ─────────────────────────────────────────────────────────────

@mcp.tool()
def search_sessions(query: str, top_k: int = 5) -> list[dict]:
    """
    Search across all ingested Claude Code session transcripts.
    Returns the top_k most relevant chunks with session ID and text.
    Use to answer: "What did we decide about X?" or "When was Y built?"
    """
    from miso_session_ingester import search_sessions as _search
    results = _search(query, top_k=top_k)
    return [{"session_id": r.get("metadata", {}).get("session_id", "?")[:16],
             "score": round(r.get("score", 0), 4),
             "text": r.get("text", "")[:500]} for r in results]


# ── Coordinator ────────────────────────────────────────────────────────────────

@mcp.tool()
def run_coordinator(goal_id: str) -> dict:
    """
    Decompose an active goal into a task graph and dispatch all ready tasks.
    The Coordinator acts as Chief of Staff — it calls the LLM to break the goal
    into ≤7 ordered tasks, assigns each to the correct agent (engineer / brain /
    consiglieri / research / autonomy), and respects dependency ordering.
    Returns the resulting task list with status.
    """
    from miso_coordinator import Coordinator
    c = Coordinator()
    c.start()
    c.decompose_and_dispatch(goal_id)
    return {"goal_id": goal_id, "tasks": c.get_status(goal_id)}


@mcp.tool()
def coordinator_status(goal_id: str | None = None) -> list[dict]:
    """
    Return the current task graph for a goal (or all recent tasks if no goal_id).
    Status values: PENDING, READY, IN_PROGRESS, COMPLETED, FAILED, ESCALATED.
    Use to check what the Coordinator is working on and which tasks are blocked.
    """
    from miso_coordinator import Coordinator
    return Coordinator().get_status(goal_id)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MISO MCP Gateway")
    parser.add_argument("--stdio", action="store_true",
                        help="Use stdio transport (for Claude Desktop config)")
    args = parser.parse_args()

    transport = "stdio" if args.stdio else "sse"
    print(f"[MISO MCP] Starting gateway — transport: {transport}")
    mcp.run(transport=transport)
