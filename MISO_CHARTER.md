# MISO Project Charter

## I. CORE PERSONAS & ROLES

* **The Auditor 🔍 (Governance):** Audits the process and outcomes, identifies root causes of failure.
* **The Guide 🧭 (Strategy):** Enforces "Path before Pace" philosophy using Socratic methods.
* **The Architect 🏛️ (Execution):** Acts as a hybrid SRE/DevOps Engineer.
* **The Synthesizer 🧠 (Goal):** A production AI whose expertise grows with the data it ingests.

## II. TECHNICAL STACK

* **Host:** AWS EC2 g4dn.xlarge
* **OS:** Ubuntu Server 22.04 LTS
* **Orchestration:** Docker Engine & Docker Compose
* **Core Services:** Nginx, FastAPI, Ollama (nomic-embed-text, llama3:8b)
* **Data Layer:** Persistent ChromaDB

## VII. META-FUNCTIONALITY: SELF-ARCHIVAL & ANALYSIS 🧠

**Objective:** To create a persistent, queryable "memory" of the MISO project's own development. This system allows MISO to ingest and analyze its own development history (our chat logs), enabling us to query past decisions, technical solutions, and lessons learned.

**Mechanism:**
1.  A utility script, `archive_and_analyze.sh`, exists in the project root.
2.  When executed with a chat log file as an argument (e.g., `./archive_and_analyze.sh my_chat_log.txt`), the script first copies the log to the `./dev_archive` directory for record-keeping.
3.  It then uses MISO's own `/ingest` endpoint to process the log file and store its contents as vectors in a dedicated knowledge collection named `miso_development_logs`.

**Usage:** This functionality allows us to ask MISO questions about its own history, such as:
* "What was the definitive fix for the persistent 502 errors?"
* "Summarize the key decisions made during the October 8th session."
* "Show me the API design we decided on for the /chat endpoint."