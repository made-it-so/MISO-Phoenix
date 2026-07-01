## Master Project Manifest (v6.0)
Last updated: 2026-07-01

---

### I. Core Operating Protocols
* Never Say Die, Process Optimization, State Verification First, Incremental Evolution, Definitive QA, "Golden Image" Mandate, The Living Document Protocol.

---

### II. System Architecture (v4 — FastAPI + MoE)

**Entry point:** `miso_architecture.md` — living source of truth for moe_router.py and engineer_daemon.py
**PRD:** `MISO_PRD.md` — the definitive product requirements document, synthesized from all historical docs
**Local scripts root:** `C:/Users/kyle/` — canonical files listed in Section V below.

The system is a polyglot FastAPI backend with:
- Goal Kernel as the organizing center of all autonomous behavior
- PRD Store as the versioned, goal-linked bounty board (16 bounties registered)
- Swarm Orchestrator for LLM routing
- Brain Agent + Consiglieri for grounded reasoning and strategic counsel
- MoE Router (Critic → Consultant → Actor) for PRD generation
- Engineer Daemon for autonomous bounty execution (Docker sandbox)
- Vector Index for semantic substrate retrieval
- Event bus (typed events) connecting all agents

---

### III. Evolutionary Epochs

| Epoch | Name | Status |
|-------|------|--------|
| I | Foundation — FastAPI, CI/CD, stable deploy | COMPLETE |
| II | Security + Goal Kernel + Core Agents | COMPLETE (2026-07-01) |
| III | Orchestration — Chief of Staff, Workflow Templates, Event Bus | NEXT |
| IV | Self-Evolution — Inquisitor, Colosseum, Failure Feedback Loop | BACKLOG |
| V | Discovery — Network Scout, Benchmark Engine | BACKLOG |
| VI | Scale — ECS Fargate, CDK stack | BACKLOG |
| VII | Interface — Morning Briefing, Consiglieri Chat Bridge, Full HUD | BACKLOG |

---

### IV. What Was Built — Session 2026-07-01

#### Security & Bug Fixes (committed ba29e37)
| File | Fix |
|------|-----|
| `miso_core.py` | SQL injection → parameterized; bare except fixed |
| `miso_brain.py` | SQL injection; 10-char truncation removed; module-level connection removed |
| `miso_sovereign.py` | Module-level side effect removed (__main__ guard) |
| `miso_gate.py` | LLM comparator replaced with Python arithmetic |
| `miso_gate_hard.py` | Same |
| `miso_evolution.py` | __main__ guard; backup before overwrite; nonsense parent_id removed |
| `miso_ingest.py` | Processed set persisted to disk; error types distinguished |
| `miso_payload_gen.py` | Rejects duplicate placeholder content |
| `miso_synthesis.py` | Dedup check before axiom append |
| `miso_engine.py` | Missing nodes flagged explicitly; truncation removed |
| `miso_manifold.json` | Deduped 120→53 entries; audited_count fixed |

#### New Core Infrastructure (committed ba29e37)
| File | Purpose |
|------|---------|
| `miso_config.py` | Central config — all paths/URLs via env vars |
| `miso_goal_kernel.py` | Goal registry — create/track/complete goals |
| `miso_vector_index.py` | Semantic retrieval via Ollama embeddings |
| `miso_swarm_orchestrator.py` | Model router |
| `miso_brain_agent.py` | Grounded reasoning with substrate + goal context |
| `miso_consiglieri.py` | Strategic counsel + live call support + trigger detection |
| `miso_prd_store.py` | Versioned PRDs with goal_id FK, completion → goal progress callback |

#### Travel Automation + System Goals (this session)
| File | Purpose |
|------|---------|
| `miso_travel_prd_setup.py` | Registers Sales Call Travel Automation (6 bounties) |
| `miso_system_prd_setup.py` | Registers all missing MISO system goals (10 bounties) |
| `MISO_PRD.md` | Full product requirements document — synthesized from all historical docs |

#### Bounty Board State (16 open bounties)
| # | Title | Goal |
|---|-------|------|
| 1 | Call Transcript Ingestor | G_C90A5A05 |
| 2 | Travel Trigger Intent Detector | G_20A8B0A3 |
| 3 | Flight Booking Agent | G_E94BB2F1 |
| 4 | Hotel Booking Agent | G_E97F7658 |
| 5 | Restaurant Reservation Agent | G_AE717232 |
| 6 | Consiglieri Live Call Support — Zoom Integration | G_4C4D22AB |
| 7 | Multi-Agent Coordinator / Chief of Staff | G_612C9162 |
| 8 | Workflow Template Engine | G_E9BC19B8 |
| 9 | Consiglieri Goal Chat Bridge | G_EEAFDF82 |
| 10 | Inquisitor Protocol + Failure Feedback Loop | G_CC16034D |
| 11 | Council of Elders | G_826AFCD5 |
| 12 | Colosseum — Meritocratic Self-Improvement | G_0D55F1D9 |
| 13 | Network Scout — Process Automation Discovery | G_6C19F60F |
| 14 | Benchmark Engine — Empirical Proof of Superiority | G_C1DA5D8F |
| 15 | Morning Briefing Agent | G_12B2325A |
| 16 | Wire moe_router and engineer_daemon to PRD Store | G_CA0FCDBA |

---

### V. Canonical File Map

**DO NOT run the graveyard scripts (miso_v900.py, miso_v1000.py, etc.). These are the live files:**

| Layer | File |
|-------|------|
| PRD | `MISO_PRD.md` |
| Config | `miso_config.py` |
| Goals | `miso_goal_kernel.py` |
| PRDs | `miso_prd_store.py` |
| Knowledge retrieval | `miso_vector_index.py` |
| Core query | `miso_core.py` |
| Brain Agent | `miso_brain_agent.py` |
| Consiglieri | `miso_consiglieri.py` |
| Model routing | `miso_swarm_orchestrator.py` |
| Autonomous research | `miso_daemon.py` |
| Autonomous synthesis | `miso_autonomy.py` |
| PDF ingestion | `miso_ingest.py` |
| Manifold state | `miso_manifold.json` |
| Goal state | `miso_goals.json` (auto-created by goal kernel) |
| Bounty DB | `miso_bounty_board.db` (auto-created by prd store) |
| Architecture doc | `miso_architecture.md` |
| Travel automation setup | `miso_travel_prd_setup.py` |
| System goals setup | `miso_system_prd_setup.py` |

---

### VI. Session 2026-07-01 (Part 2) — What Was Built

| File | Change |
|---|---|
| `miso_swarm_orchestrator.py` | Rebuilt as 4-tier compute gradient — Tier1(Ollama)→Tier2(commercial)→Tier3(frontier), no hardcoded model names, `call_code_then_escalate()` added |
| `miso_manifold.json` | Seeded with 12 MISO constitutional axioms; status ACTIVE; kernel epoch3.1 |
| Remote | `evolution/oracle_payload` pushed to `github.com/made-it-so/MISO-Phoenix` |

### VI-B. Hidden Files Not Yet Ingested
- `.miso_workspace/incubator/` — 90+ daily forensic audit files (Mar-Jul 2026)
- `.miso_workspace/miso_roadmap.md` — persistent state ledger
- `Documents/GitHub/MISO_SOVEREIGN/GOLDEN_MANIFESTO.md`
- `Dropbox/MISO_SYNC/SOVEREIGN_STRATEGY.md`
- `MISO-Factory-BROKEN-AUTH/chat_logs/summaries/` — 51 chat summaries
- EC2 (`ubuntu@3.91.130.202`): `/root/arena/miso_v5/devops_agent_spec.md`, `miso_audit.md`, `sysop.py`
- SSH key: `C:\Users\kyle\.ssh\MISO-Ollama-Key.pem`

### VII. Known Issues / Next Session

1. **miso-steel-thread/backend-services/ingest_service.py** — hardcoded Google API key exposed. Rotate at console.cloud.google.com → APIs & Services → Credentials.
2. **Vector index is empty** — run `python miso_vector_index.py` to index existing manifold axioms.
3. **Bounty #16 is highest priority** — wire moe_router.py and engineer_daemon.py to PRD Store.
4. **Bounty #7 is the architectural unlock** — Multi-Agent Coordinator enables Epoch III.
5. **Bounty #8 (Workflow Templates)** — makes travel automation generic; prevents hardcoding.
6. **Package restructure** — 100+ flat scripts still need archiving. Move dead files to `miso_archive/`.

---

### VII. What Is NOT In The Code (needs to be built — bounties registered)

- Multi-Agent Coordinator / Chief of Staff (was lost between sessions, now bounty #7)
- Inquisitor Protocol + Failure Feedback Loop (was "Epoch I-V complete" in STATE.md but files never committed)
- Council of Elders (same — design existed, code never committed)
- Workflow Template Engine (travel automation is hardcoded; needs generalization)
- Network Scout + Benchmark Engine (designed, never built)
- Colosseum / Meritocratic Crucible (designed in Miso_OS_Day2_Archive.md, never built)
- Consiglieri → Goal Chat pub/sub bridge
- Morning Briefing Agent

---

### VIII. Rotation Required

`miso-steel-thread/backend-services/ingest_service.py` line 16 contains a live Google API key.
**Rotate it at:** console.cloud.google.com → APIs & Services → Credentials
