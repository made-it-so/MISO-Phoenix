# MISO — Product Requirements Document
**Version:** 1.0
**Date:** 2026-07-01
**Status:** Living Document — governed by the Living Document Protocol

---

## I. Mission Statement

MISO is a sovereign, self-evolving AI operating system that autonomously manages a mesh of specialized agents to execute any goal a business operator defines — with empirical proof of superiority over the status quo and zero reliance on human intervention for routine operations.

MISO does not build apps. MISO pursues goals.

---

## II. Core Directive

> Grant every operator the most capable AI-enabled tool possible — grounded in their private data, aligned to their goals, auditable at every step, and continuously improving without human prompting.

---

## III. Design Principles

1. **Goal-first, not artifact-first.** Every action MISO takes must serve an active goal in the Goal Kernel. Undirected work is waste.
2. **Empirical proof before replacement.** MISO does not replace a human process until it can demonstrate measurably superior outcomes (speed, accuracy, cost).
3. **Radical transparency.** All agent reasoning, plans, and actions are auditable. No black boxes.
4. **Self-reliance with strategic escalation.** MISO operates on local models by default. It escalates to frontier APIs (Claude, GPT-4o) only when latency or capability demands it.
5. **Never say die.** Failure is feedback. Every crash, bad output, or goal miss feeds the improvement loop.
6. **Sovereign data.** MISO's knowledge lives on the operator's infrastructure. No data leaves without explicit authorization.
7. **Minimum intervention.** MISO asks for human input only when confidence is below threshold or action is irreversible.

---

## IV. System Architecture

### Layer 0 — Substrate
- **Knowledge Manifold** (`miso_manifold.json`): Axiom store — distilled insights from ingested research
- **Vector Index** (`miso_vector_index.py`): Semantic retrieval via Ollama embeddings
- **DeltaLake Silver Layer**: Raw node storage for structured retrieval via DuckDB

### Layer 1 — Goal Kernel
- **Goal Kernel** (`miso_goal_kernel.py`): The organizing center. All autonomous behavior is goal-directed.
- **PRD Store** (`miso_prd_store.py`): Versioned, goal-linked bounty board. The engineer daemon's work queue.
- **Config** (`miso_config.py`): All paths/URLs via environment variables.

### Layer 2 — Intelligence
- **Brain Agent** (`miso_brain_agent.py`): Grounded Q&A — substrate + goal context. Refuses to hallucinate.
- **Consiglieri** (`miso_consiglieri.py`): Strategic advisor — goal counsel, action audits, blind spot detection, live call support.
- **Swarm Orchestrator** (`miso_swarm_orchestrator.py`): Model router — routes LLM calls by task type to the best available model.

### Layer 3 — Autonomous Loops
- **Autonomy Loop** (`miso_autonomy.py`): Synthesizes new axioms from goal-directed concept pairs.
- **Research Daemon** (`miso_daemon.py`): Harvests arxiv papers matching active goal keywords; distills into manifold.
- **Engineer Daemon** (`engineer_daemon.py` in `miso_architecture.md`): Claims open bounties, generates code, validates in Docker sandbox, deploys.

### Layer 4 — Orchestration (PARTIALLY BUILT / TO BUILD)
- **Chief of Staff / Multi-Agent Coordinator**: Routes work across the agent mesh. Decomposes macro-goals into agent tasks with dependency graphs.
- **MoE Router** (`moe_router.py` in `miso_architecture.md`): Critic → Consultant → Actor pipeline for PRD generation.
- **Workflow Template Engine**: Generic event-driven automation. Triggers → Conditions → Agent sequences as config, not code.

### Layer 5 — Self-Evolution (TO BUILD)
- **Inquisitor Protocol**: Agent's drive to self-analyze — identifies its own weakest success criteria and generates improvement bounties.
- **Colosseum / Meritocratic Crucible**: Prime vs. Challenger OS instances. Challenger runs in resource-constrained sandbox. Coup d'état if Challenger proves faster with fewer tokens.
- **Council of Elders**: Top-level supervisory function for high-risk or irreversible actions. Convenes when Consiglieri confidence is below threshold.
- **Failure Feedback Loop**: Every failed bounty auto-generates a root-cause bounty. Failures drive the roadmap.

### Layer 6 — Discovery (TO BUILD)
- **Network Scout / Process Automation Agent**: Dropped into a network with read access. Discovers running processes, maps workflows, identifies automation candidates, establishes baseline metrics.
- **Benchmark Engine**: Runs MISO against the baseline. Produces empirical proof of superiority (speed, cost, accuracy delta) before any replacement recommendation.

### Layer 7 — Interface
- **ToolForge React UI**: PRD ideation, bounty board, goal tracking.
- **Omni HUD**: Borderless native overlay (pywebview). Global hotkey. Diegetic action cards for destructive operations.
- **Consiglieri Chat Bridge**: Pub/sub bridge between goal-definition chat and decision-support chat. Counsel auto-fires on goal draft submission.
- **Morning Briefing**: Boot-time JARVIS report — overnight Sabbatical telemetry, goal progress, any Coup d'État events.

---

## V. Agent Biome

### Cerebrum-Class (Strategic)
| Agent | Role |
|-------|------|
| Consiglieri | Strategic advisor, blind spot detection, live call support |
| Brain Agent | Grounded knowledge retrieval and reasoning |
| Chief of Staff | Macro-goal decomposition, agent dispatch, dependency management |
| Mission Conductor | Strategic resource allocation — when to use local vs. frontier models |
| Inquisitor | Self-analysis, experiment generation, improvement roadmap |

### Cerebellum-Class (Specialized)
| Agent | Role |
|-------|------|
| Engineer Daemon | PRD → code → sandbox → deploy |
| Research Daemon | arxiv harvest → manifold synthesis |
| Autonomy Loop | Concept synthesis, axiom generation |
| Network Scout | Process discovery, automation opportunity identification |
| Benchmark Engine | Empirical comparison, proof-of-superiority |
| Travel Booker | Flight + hotel + restaurant from sales call trigger |
| Call Transcript Ingestor | Zoom webhook + file drop → structured transcript |
| Travel Trigger Detector | Intent detection → TRAVEL_TRIGGER event |

---

## VI. Event Bus

All agents communicate via typed events. No agent calls another directly.

| Event | Producer | Consumer |
|-------|----------|----------|
| `TRANSCRIPT_READY(call_id)` | Ingestor | Trigger Detector, Consiglieri |
| `TRAVEL_TRIGGER(city, date, attendees)` | Trigger Detector | Flight Booker, Hotel Booker |
| `FLIGHT_BOOKED(confirmation)` | Flight Booker | Hotel Booker, Itinerary Assembler |
| `HOTEL_BOOKED(address, date)` | Hotel Booker | Restaurant Booker |
| `GOAL_CREATED(goal_id)` | Goal Kernel | Consiglieri (auto-counsel), Chief of Staff |
| `BOUNTY_COMPLETED(bounty_id)` | Engineer Daemon | Goal Kernel (progress update) |
| `BOUNTY_FAILED(bounty_id, reason)` | Engineer Daemon | Failure Feedback Loop |
| `INQUISITOR_FINDING(weakness)` | Inquisitor | Goal Kernel (new bounty creation) |
| `BENCHMARK_COMPLETE(delta)` | Benchmark Engine | Consiglieri, Operator notification |

---

## VII. Workflow Template System

The travel automation is one instance of a generic pattern:

```
WorkflowTemplate:
  id: <uuid>
  name: <string>
  trigger:
    type: transcript | schedule | webhook | manual | event
    condition: <regex or LLM-evaluated expression>
  actions:
    - agent: <agent_id>
      input_map: <event fields → agent input>
      on_success: emit <EVENT>
      on_failure: emit <EVENT> | notify_operator
  success_criteria: [<measurable outcomes>]
  goal_id: <FK to goal kernel>
```

This means sales call travel, contract renewal detection, meeting follow-up scheduling, or any other trigger→action sequence is defined as data — not code.

---

## VIII. Success Criteria (System Level)

1. Any goal defined in the Goal Kernel is automatically decomposed into bounties within 60s
2. 80%+ of bounties are completed without human intervention
3. Every completed bounty is linked to measurable goal progress
4. Self-improvement: the system generates at least 1 improvement bounty per week from Inquisitor findings
5. Network discovery: MISO identifies ≥3 automation candidates within 2 hours of network drop-in
6. Empirical proof: every automation recommendation includes a measured baseline and projected improvement
7. Live call support: Consiglieri brief delivered within 5s of trigger on frontier model
8. Zero data exfiltration: all processing runs on operator infrastructure by default

---

## IX. What Is Built vs. What Is Missing

### Built (committed as of 2026-07-01)
- Goal Kernel, PRD Store, Swarm Orchestrator
- Brain Agent, Consiglieri (with live call support)
- Vector Index, Autonomy Loop, Research Daemon
- Travel automation goals + bounties registered
- MoE Router + Engineer Daemon (embedded in miso_architecture.md)
- Security fixes across miso_core, miso_brain, miso_gate, miso_evolution, etc.

### Missing (registered as bounties — build queue)
- Multi-Agent Coordinator / Chief of Staff
- Inquisitor Protocol + Failure Feedback Loop
- Council of Elders
- Workflow Template Engine (generalize travel automation pattern)
- Network Scout + Benchmark Engine
- Colosseum / Meritocratic Crucible
- Consiglieri → Goal Chat pub/sub bridge
- Morning Briefing agent
- moe_router.py → PRD Store wiring
- engineer_daemon.py → PRD Store wiring

---

## X. Open Dependencies

| Dependency | Required By | Status |
|------------|-------------|--------|
| Zoom Webhook Token | Call Transcript Ingestor | Pending |
| Amadeus API Key | Flight Booking Agent | Pending |
| Expedia Rapid / Booking.com Key | Hotel Booking Agent | Pending |
| Resy / OpenTable API | Restaurant Reservation Agent | Pending |
| Yelp Fusion API Key | Restaurant Finder | Pending (free tier) |
| Google Maps Geocoding Key | Hotel proximity search | Pending |
| ANTHROPIC_API_KEY | Frontier escalation (Consiglieri) | Available |
| OPENAI_API_KEY | Frontier escalation fallback | Optional |

---

## XI. Evolutionary Epochs

| Epoch | Name | Status |
|-------|------|--------|
| I | Foundation — FastAPI, CI/CD, stable deploy | COMPLETE |
| II | Security + Goal Kernel + Core Agents | COMPLETE (2026-07-01) |
| III | Orchestration — Chief of Staff, Workflow Templates, Event Bus | NEXT |
| IV | Self-Evolution — Inquisitor, Colosseum, Failure Feedback Loop | BACKLOG |
| V | Discovery — Network Scout, Benchmark Engine | BACKLOG |
| VI | Scale — ECS Fargate, CDK stack | BACKLOG |
| VII | Interface — Morning Briefing, Consiglieri Chat Bridge, Full HUD | BACKLOG |
