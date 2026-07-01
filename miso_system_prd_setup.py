"""
Registers MISO's own system-level goals and bounties into the Goal Kernel.

Run once:
    python miso_system_prd_setup.py

Creates goals + bounties for every missing system component identified in MISO_PRD.md.
Idempotent — skips goals/bounties that already exist by title check.
"""
from miso_goal_kernel import create_goal, activate_goal, get_all_goals
from miso_prd_store import create_bounty, get_bounties_for_goal, print_board


def _goal_exists(title: str) -> bool:
    return any(g["title"] == title for g in get_all_goals())


def _bounty_exists(goal_id: str, title: str) -> bool:
    return any(b["title"] == title for b in get_bounties_for_goal(goal_id))


def setup():
    print("[SETUP] Registering MISO system goals...\n")

    # ── Epoch III: Orchestration ───────────────────────────────────────────────

    if not _goal_exists("Multi-Agent Coordinator / Chief of Staff"):
        g = create_goal(
            title="Multi-Agent Coordinator / Chief of Staff",
            description=(
                "A top-level orchestration agent that decomposes macro-goals into "
                "agent tasks with dependency graphs, dispatches to the correct "
                "Cerebellum-class agent, and tracks completion. Replaces the missing "
                "40-agent coordination layer."
            ),
            success_criteria=[
                "Accepts a goal_id and decomposes it into ordered agent tasks",
                "Dispatches each task to the correct agent via the event bus",
                "Tracks dependency graph — blocked tasks wait for upstream completion",
                "Re-queues failed tasks up to 3 times before escalating to Council of Elders",
                "Visible in ToolForge as an active orchestration view",
            ],
            priority=1,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Multi-Agent Coordinator / Chief of Staff",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "agent",   "title": "Task Decomposer",    "desc": "LLM breaks goal into ordered agent tasks with dependency edges"},
                    {"id": 2, "type": "agent",   "title": "Agent Dispatcher",   "desc": "Routes each task to the correct registered agent"},
                    {"id": 3, "type": "memory",  "title": "Task Graph Store",   "desc": "SQLite DAG: task_id, agent, status, depends_on, retries"},
                    {"id": 4, "type": "trigger", "title": "GOAL_CREATED event", "desc": "Auto-fires on new active goal"},
                ],
                "mechanics": (
                    "1. On GOAL_CREATED(goal_id): load goal + success_criteria\n"
                    "2. LLM decomposes into task list with agent assignments and dependencies\n"
                    "3. Store as DAG in task_graph.db\n"
                    "4. Dispatch ready tasks (no unmet dependencies) to agent queue\n"
                    "5. On task completion: unlock downstream tasks, emit TASK_COMPLETE\n"
                    "6. On task failure (3 retries): escalate to Council of Elders\n"
                    "7. On all tasks complete: emit GOAL_TASKS_DONE(goal_id)"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Multi-Agent Coordinator [{g['id']}]")

    if not _goal_exists("Workflow Template Engine"):
        g = create_goal(
            title="Workflow Template Engine",
            description=(
                "A generic event-driven workflow system. Triggers, conditions, and "
                "action sequences are stored as config (not code). The sales call "
                "travel automation is one instance; infinite variations are possible "
                "without writing new Python."
            ),
            success_criteria=[
                "WorkflowTemplate schema: trigger type, condition, action sequence, success_criteria",
                "Templates stored in workflow_templates.db, linked to goal_id",
                "Template engine listens on event bus and fires matching action sequences",
                "Travel automation migrated from hardcoded PRD to a WorkflowTemplate instance",
                "New workflows can be created via API or ToolForge UI without code changes",
            ],
            priority=1,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Workflow Template Engine",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "memory",   "title": "Template Store",      "desc": "SQLite: template_id, trigger, condition, actions JSON, goal_id"},
                    {"id": 2, "type": "agent",    "title": "Event Listener",      "desc": "Subscribes to all events; matches against template trigger conditions"},
                    {"id": 3, "type": "agent",    "title": "Action Sequencer",    "desc": "Executes action list in order, passing event fields via input_map"},
                    {"id": 4, "type": "trigger",  "title": "Template CRUD API",   "desc": "POST/GET/PUT /workflow-templates"},
                ],
                "mechanics": (
                    "1. Define WorkflowTemplate schema: {trigger, condition, actions[], goal_id}\n"
                    "2. Event Listener receives all MISO events\n"
                    "3. For each event: check all ACTIVE templates whose trigger matches\n"
                    "4. Evaluate condition (regex or LLM) against event payload\n"
                    "5. If match: execute action sequence, mapping event fields to agent inputs\n"
                    "6. Log execution to workflow_runs.db\n"
                    "7. Migrate travel automation hardcoded PRD into first template instance"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Workflow Template Engine [{g['id']}]")

    if not _goal_exists("Consiglieri Goal Chat Bridge"):
        g = create_goal(
            title="Consiglieri Goal Chat Bridge",
            description=(
                "When a goal is being defined in the goal-definition chat, the "
                "Consiglieri automatically weighs in and the counsel is pushed to "
                "the decision-support chat. Two-chat pub/sub bridge via SSE."
            ),
            success_criteria=[
                "POST /goals/draft endpoint accepts goal text and returns counsel",
                "Counsel auto-pushed to decision-support chat session via SSE",
                "Counsel fires within 5s of goal draft submission on frontier model",
                "Manual trigger: user can request Consiglieri input at any time",
                "Counsel includes: recommendation, risks, and which active goal it serves",
            ],
            priority=2,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Consiglieri Goal Chat Bridge",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "trigger",  "title": "POST /goals/draft",        "desc": "Accepts goal draft text + session_id"},
                    {"id": 2, "type": "agent",    "title": "Consiglieri.advise_on()",  "desc": "Existing method — counsel on the draft goal"},
                    {"id": 3, "type": "trigger",  "title": "SSE push",                 "desc": "Counsel streamed to decision-support chat session"},
                    {"id": 4, "type": "trigger",  "title": "GOAL_CREATED event hook",  "desc": "Auto-fires advise_on() when goal is formally created"},
                ],
                "mechanics": (
                    "1. POST /goals/draft {text, session_id}: call consiglieri.advise_on(text)\n"
                    "2. Stream counsel via SSE to the requesting session\n"
                    "3. Also push counsel to the paired decision-support session (session registry)\n"
                    "4. On formal GOAL_CREATED: auto-call advise_on(goal.description) and push\n"
                    "5. Session registry: in-memory dict {session_id: sse_queue}\n"
                    "6. Two chat windows register as a paired session on connect"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Consiglieri Goal Chat Bridge [{g['id']}]")

    # ── Epoch IV: Self-Evolution ───────────────────────────────────────────────

    if not _goal_exists("Inquisitor Protocol + Failure Feedback Loop"):
        g = create_goal(
            title="Inquisitor Protocol + Failure Feedback Loop",
            description=(
                "Every agent self-analyzes its weakest success criteria and generates "
                "improvement bounties. Every failed bounty auto-generates a root-cause "
                "analysis bounty. Failures drive the roadmap."
            ),
            success_criteria=[
                "Each agent reports its weakest criterion weekly to the Inquisitor",
                "Inquisitor generates ≥1 improvement bounty per agent per week",
                "Failed bounties auto-create a root-cause bounty within 60s",
                "Root-cause bounty includes: failure log, hypothesis, proposed fix",
                "Improvement bounties are goal-linked and appear on the bounty board",
            ],
            priority=2,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Inquisitor Protocol + Failure Feedback Loop",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "agent",    "title": "Inquisitor",           "desc": "Polls agents for self-reported weaknesses; generates improvement bounties"},
                    {"id": 2, "type": "trigger",  "title": "BOUNTY_FAILED event",  "desc": "Auto-fires root-cause analysis"},
                    {"id": 3, "type": "agent",    "title": "Root Cause Analyzer",  "desc": "LLM analyzes failure log → root cause hypothesis → fix bounty"},
                    {"id": 4, "type": "memory",   "title": "Failure Log DB",       "desc": "failure_id, bounty_id, log, root_cause, fix_bounty_id"},
                ],
                "mechanics": (
                    "1. Weekly cron: Inquisitor asks each agent to report its weakest criterion\n"
                    "2. Inquisitor LLM generates a targeted improvement bounty per weakness\n"
                    "3. On BOUNTY_FAILED(bounty_id, reason, log):\n"
                    "4.   LLM analyzes log → root cause hypothesis\n"
                    "5.   Auto-creates 'Fix: <original bounty title>' bounty with hypothesis\n"
                    "6.   Links fix bounty to same goal_id as failed bounty\n"
                    "7.   Notifies operator via Morning Briefing"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Inquisitor Protocol [{g['id']}]")

    if not _goal_exists("Council of Elders"):
        g = create_goal(
            title="Council of Elders",
            description=(
                "Top-level supervisory function for high-risk or irreversible actions. "
                "Convenes when Consiglieri confidence is below threshold or when the "
                "Chief of Staff has exhausted retries. Requires human confirmation for "
                "destructive operations."
            ),
            success_criteria=[
                "Convenes automatically when action has irreversibility_score > 0.8",
                "Presents: proposed action, Consiglieri counsel, risk assessment",
                "Operator can approve, modify, or abort via ToolForge action card",
                "All Council decisions logged with rationale",
                "Escalation path: agent → Chief of Staff → Consiglieri → Council → Operator",
            ],
            priority=2,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Council of Elders",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "agent",    "title": "Irreversibility Scorer", "desc": "Scores proposed action 0-1 for reversibility"},
                    {"id": 2, "type": "agent",    "title": "Council Convener",       "desc": "Assembles action + Consiglieri counsel + risk brief"},
                    {"id": 3, "type": "trigger",  "title": "Operator Action Card",   "desc": "Diegetic UI card: Approve / Modify / Abort"},
                    {"id": 4, "type": "memory",   "title": "Council Log",            "desc": "council_id, action, counsel, decision, rationale, operator"},
                ],
                "mechanics": (
                    "1. Any agent can emit COUNCIL_REQUIRED(action, context, risk)\n"
                    "2. Auto-trigger: if irreversibility_score > 0.8\n"
                    "3. Council Convener: run consiglieri.audit_action() + build brief\n"
                    "4. Push to ToolForge as Diegetic Action Card (blocking)\n"
                    "5. Operator selects: Approve | Modify | Abort\n"
                    "6. Log decision; resume or halt action pipeline\n"
                    "7. Timeout (15 min): auto-abort and notify operator"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Council of Elders [{g['id']}]")

    if not _goal_exists("Colosseum — Meritocratic Self-Improvement"):
        g = create_goal(
            title="Colosseum — Meritocratic Self-Improvement",
            description=(
                "Prime vs. Challenger OS instances compete. Challenger runs in a "
                "resource-constrained sandbox (API firewall, CPU limit). If Challenger "
                "solves Prime's tasks faster and cheaper, a zero-downtime pointer swap "
                "makes Challenger the new Prime."
            ),
            success_criteria=[
                "Challenger instance spun up nightly with resource constraints applied",
                "Same task set run on both Prime and Challenger",
                "Challenger wins if: speed > Prime AND token_cost < Prime on ≥60% of tasks",
                "Zero-downtime swap: Challenger pointers atomically replace Prime",
                "Morning Briefing reports any Coup d'État that occurred overnight",
            ],
            priority=3,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Colosseum — Meritocratic Self-Improvement",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "trigger",  "title": "Nightly Sabbatical",     "desc": "2:00 AM cron: spin up Challenger in constrained container"},
                    {"id": 2, "type": "agent",    "title": "Task Referee",           "desc": "Runs identical task set on Prime and Challenger, measures outcomes"},
                    {"id": 3, "type": "agent",    "title": "Coup d'État Executor",   "desc": "Atomic pointer swap if Challenger wins"},
                    {"id": 4, "type": "memory",   "title": "Colosseum Results DB",   "desc": "run_id, prime_score, challenger_score, winner, swap_executed"},
                ],
                "mechanics": (
                    "1. Nightly cron (2:00 AM): clone current Prime config → Challenger\n"
                    "2. Apply constraints: no external API calls, 3s CPU limit per task\n"
                    "3. Run last 24h task set on both instances, measure: latency, tokens, accuracy\n"
                    "4. If Challenger wins on ≥60% of tasks: execute pointer swap\n"
                    "5. Swap: atomic config replace, health check, rollback if unhealthy\n"
                    "6. Log results to colosseum.db\n"
                    "7. Include in Morning Briefing"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Colosseum [{g['id']}]")

    # ── Epoch V: Discovery ─────────────────────────────────────────────────────

    if not _goal_exists("Network Scout — Process Automation Discovery"):
        g = create_goal(
            title="Network Scout — Process Automation Discovery",
            description=(
                "MISO is dropped into a network with read access. It discovers running "
                "processes and workflows, identifies automation candidates, establishes "
                "a human-process baseline, and produces an empirical automation "
                "recommendation report."
            ),
            success_criteria=[
                "Discovers ≥3 automation candidates within 2 hours of network drop-in",
                "Establishes measurable baseline for each candidate (time, cost, error rate)",
                "Ranks candidates by automation ROI (effort vs. impact)",
                "Produces a structured report: candidate, baseline, projected improvement, confidence",
                "No data written or processes modified — read-only discovery",
            ],
            priority=3,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Network Scout — Process Automation Discovery",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "agent",    "title": "Resource Enumerator",    "desc": "Read-only: discovers APIs, databases, file shares, running services"},
                    {"id": 2, "type": "agent",    "title": "Process Modeler",        "desc": "Maps discovered resources to business process workflows"},
                    {"id": 3, "type": "agent",    "title": "Baseline Measurer",      "desc": "Queries logs/metrics to establish current process performance"},
                    {"id": 4, "type": "agent",    "title": "ROI Ranker",             "desc": "Scores candidates: automation_effort vs. projected_improvement"},
                    {"id": 5, "type": "agent",    "title": "Report Generator",       "desc": "Structured automation recommendation report"},
                ],
                "mechanics": (
                    "1. Operator provides: network credentials (read-only), scope (IP range/domain)\n"
                    "2. Resource Enumerator: scan for APIs, DBs, file shares, service endpoints\n"
                    "3. Process Modeler: LLM maps resources to likely business workflows\n"
                    "4. Baseline Measurer: query available logs/metrics for each candidate\n"
                    "5. ROI Ranker: score each candidate (0-10) on effort and impact\n"
                    "6. Generate structured report with top N candidates\n"
                    "7. CONSTRAINT: zero writes, zero process modifications, read-only throughout"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Network Scout [{g['id']}]")

    if not _goal_exists("Benchmark Engine — Empirical Proof of Superiority"):
        g = create_goal(
            title="Benchmark Engine — Empirical Proof of Superiority",
            description=(
                "Before MISO replaces any human process, it runs a controlled comparison "
                "and produces empirical proof. Human process baseline vs. MISO output "
                "on identical inputs. No replacement without a measured win."
            ),
            success_criteria=[
                "Runs MISO and human process on identical inputs in parallel",
                "Measures: accuracy, speed, cost per unit, error rate",
                "Produces a structured comparison report with statistical confidence",
                "Threshold: MISO must win on ≥2 of 4 metrics at p<0.05 to recommend replacement",
                "Report stored and linked to the relevant goal",
            ],
            priority=3,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Benchmark Engine — Empirical Proof of Superiority",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "agent",    "title": "Test Harness",           "desc": "Runs identical input set through MISO and human process"},
                    {"id": 2, "type": "agent",    "title": "Metrics Collector",      "desc": "Captures: latency, accuracy, cost, error rate for each run"},
                    {"id": 3, "type": "agent",    "title": "Statistical Analyzer",   "desc": "Computes delta, confidence interval, p-value"},
                    {"id": 4, "type": "agent",    "title": "Report Emitter",         "desc": "Structured proof report → BENCHMARK_COMPLETE event"},
                ],
                "mechanics": (
                    "1. Operator defines: process_id, input_set, human_baseline_metrics\n"
                    "2. Test Harness runs MISO on input_set, measures outputs\n"
                    "3. Metrics Collector compares MISO outputs to human_baseline_metrics\n"
                    "4. Statistical Analyzer: compute delta and confidence for each metric\n"
                    "5. If MISO wins ≥2/4 metrics at p<0.05: emit BENCHMARK_COMPLETE(win=True)\n"
                    "6. Else: emit BENCHMARK_COMPLETE(win=False, gaps=[...])\n"
                    "7. Store report in benchmark_results.db, link to goal_id"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Benchmark Engine [{g['id']}]")

    # ── Epoch VII: Interface ───────────────────────────────────────────────────

    if not _goal_exists("Morning Briefing Agent"):
        g = create_goal(
            title="Morning Briefing Agent",
            description=(
                "On boot, MISO generates a dynamic morning briefing: overnight activity "
                "summary, goal progress deltas, any Colosseum results, failed bounties, "
                "and top 3 recommended actions for the day."
            ),
            success_criteria=[
                "Briefing generated within 10s of system boot",
                "Covers: goal progress changes, completed/failed bounties overnight",
                "Includes Colosseum results if a Coup d'État occurred",
                "Top 3 recommended actions derived from Consiglieri.advise_on()",
                "Delivered as desktop notification + stored in briefing_log.db",
            ],
            priority=3,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Morning Briefing Agent",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "trigger",  "title": "Boot hook",              "desc": "Fires on miso_server startup"},
                    {"id": 2, "type": "agent",    "title": "Briefing Assembler",     "desc": "Queries goal kernel, bounty board, colosseum log for overnight delta"},
                    {"id": 3, "type": "agent",    "title": "Consiglieri.advise_on()", "desc": "Generates top 3 recommended actions"},
                    {"id": 4, "type": "trigger",  "title": "Desktop Notification",   "desc": "Win10 toast notification + ToolForge banner"},
                ],
                "mechanics": (
                    "1. On startup: query goal_kernel for progress since last briefing timestamp\n"
                    "2. Query bounty_board for COMPLETED/FAILED since last briefing\n"
                    "3. Query colosseum_results for any overnight Coup d'État\n"
                    "4. Call consiglieri.advise_on('What are the top 3 priorities today?')\n"
                    "5. Assemble brief as structured text\n"
                    "6. Emit as Windows toast notification\n"
                    "7. Store in briefing_log.db with timestamp"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: Morning Briefing Agent [{g['id']}]")

    # ── Engineering debt: wiring ───────────────────────────────────────────────

    if not _goal_exists("Wire moe_router and engineer_daemon to PRD Store"):
        g = create_goal(
            title="Wire moe_router and engineer_daemon to PRD Store",
            description=(
                "moe_router.py and engineer_daemon.py still use inline SQLite instead of "
                "importing from miso_prd_store. This breaks goal linkage and versioning."
            ),
            success_criteria=[
                "moe_router.py imports create_bounty() from miso_prd_store, passes goal_id from session",
                "engineer_daemon.py uses claim_next_open_bounty(), complete_bounty(), fail_bounty()",
                "No inline bounty SQLite in either file",
                "Completed bounties trigger goal progress updates via complete_bounty()",
            ],
            priority=1,
        )
        activate_goal(g["id"])
        create_bounty(
            title="Wire moe_router and engineer_daemon to PRD Store",
            description=g["description"],
            prd_blueprint={
                "architectureNodes": [
                    {"id": 1, "type": "workflow", "title": "moe_router.py refactor",       "desc": "Replace inline INSERT with create_bounty(goal_id=session.goal_id)"},
                    {"id": 2, "type": "workflow", "title": "engineer_daemon.py refactor",  "desc": "Replace inline SELECT/UPDATE with claim/complete/fail_bounty()"},
                ],
                "mechanics": (
                    "1. Read miso_architecture.md: extract moe_router.py and engineer_daemon.py\n"
                    "2. In moe_router.py /deploy endpoint: replace inline bounty INSERT with create_bounty()\n"
                    "3. Add session context to pass goal_id to create_bounty()\n"
                    "4. In engineer_daemon.py: replace SELECT+UPDATE with claim_next_open_bounty()\n"
                    "5. Replace completion UPDATE with complete_bounty(bounty_id, deployed_path)\n"
                    "6. Replace failure UPDATE with fail_bounty(bounty_id, reason)\n"
                    "7. Write updated versions as moe_router.py and engineer_daemon.py flat files"
                ),
            },
            goal_id=g["id"],
            success_criteria=g["success_criteria"],
        )
        print(f"  Registered: moe_router/engineer_daemon wiring [{g['id']}]")

    print("\n" + "=" * 60)
    print("MISO SYSTEM SETUP COMPLETE")
    print_board()


if __name__ == "__main__":
    setup()
