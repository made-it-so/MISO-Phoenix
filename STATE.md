## Master Project Manifest (v5.0)
Last updated: 2026-07-01

---

### I. Core Operating Protocols
* Never Say Die, Process Optimization, State Verification First, Incremental Evolution, Definitive QA, "Golden Image" Mandate, The Living Document Protocol.

---

### II. System Architecture (v4 — FastAPI + MoE)

**Entry point:** `miso_architecture.md` — the living source of truth for all deployed code.
**Local scripts root:** `C:/Users/kyle/` — canonical files listed in Section V below.

The system is a polyglot FastAPI backend with:
- MoE Router (`moe_router.py`) for intent → blueprint → deploy pipeline
- Engineer Daemon for autonomous PRD execution
- Goal Kernel as the organizing center of all autonomous behavior
- Brain Agent + Consiglieri for grounded reasoning and strategic counsel
- Vector Index for semantic substrate retrieval
- PRD Store as the versioned, goal-linked bounty board

---

### III. Evolutionary Epochs

#### Epochs I–V (COMPLETE)
Established foundational app, CI/CD, Goal Kernel, Council of Elders, Failure Feedback Loop, Inquisitor Protocol.

#### Epoch VI: Scalability & Orchestration (NEXT)
* Migrate to ECS Fargate. CDK stack. Goal registered in `miso_goals.json`.

---

### IV. What Was Built — Session 2026-07-01

#### Security & Bug Fixes (committed)
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

#### New Core Infrastructure (committed)
| File | Purpose |
|------|---------|
| `miso_config.py` | Central config — all paths/URLs via env vars |
| `miso_goal_kernel.py` | **Goal registry** — create/track/complete goals; bootstraps initial goals from STATE.md roadmap |
| `miso_vector_index.py` | Semantic retrieval via Ollama embeddings + cosine similarity |
| `miso_swarm_orchestrator.py` | Model router — was missing, broke moe_router.py on startup |
| `miso_brain_agent.py` | **Brain Agent** — grounded reasoning with substrate + goal context |
| `miso_consiglieri.py` | **Consiglieri** — strategic counsel, action audits, blind spot detection |
| `miso_prd_store.py` | **PRD Store** — versioned PRDs with goal_id FK, completion → goal progress callback |

#### Autonomy Fixes (committed)
| File | Fix |
|------|-----|
| `miso_autonomy.py` | Critical crash (string-as-vector); now goal-directed |
| `miso_daemon.py` | Derives arxiv queries from goal keywords; atomic writes; dedup |

---

### V. Canonical File Map

**DO NOT run the graveyard scripts (miso_v900.py, miso_v1000.py, etc.). These are the live files:**

| Layer | File |
|-------|------|
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
| Architecture doc | `miso_architecture.md` |

---

### VI. Known Issues / Next Session

1. **miso-steel-thread/backend-services/ingest_service.py** — hardcoded Google API key exposed. Rotate and move to .env immediately.
2. **Vector index is empty** — run `python miso_vector_index.py` to index existing manifold axioms.
3. **Goal kernel bootstrap** — run `python miso_goal_kernel.py` once to seed initial goals.
4. **moe_router.py** needs to be updated to import `create_bounty` from `miso_prd_store` and pass `goal_id` from user session context.
5. **engineer_daemon.py** needs to replace inline SQLite with `claim_next_open_bounty()`, `complete_bounty()`, `fail_bounty()` from `miso_prd_store`.
6. **Package restructure** — 100+ flat scripts still need archiving. Move dead files to `miso_archive/`.
7. **Epoch VI** — ECS/Fargate CDK stack not started.

---

### VII. Rotation Required

`miso-steel-thread/backend-services/ingest_service.py` line 16 contains a live Google API key.
**Rotate it at:** console.cloud.google.com → APIs & Services → Credentials
