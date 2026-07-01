"""
MISO Session Ingester — vectorizes Claude Code session transcripts into the Brain Agent.

Run after any session to preserve institutional knowledge:
    python miso_session_ingester.py                        # ingest current session
    python miso_session_ingester.py --file path/to/transcript.txt

The Brain Agent can then answer:
  "What did we decide about the Council of Elders?"
  "When was miso_core.py SQL injection fixed?"
  "What is the Inquisitor Protocol?"
"""
import os
import json
import argparse
import glob
import re
from datetime import datetime

SESSION_STORE = os.path.join(os.path.dirname(__file__), "miso_session_store.json")
CLAUDE_PROJECTS = os.path.expandvars(r"C:\Users\kyle\.claude\projects\C--Users-kyle")
CHUNK_CHARS = 1200   # overlap-friendly chunk size for embedding
OVERLAP_CHARS = 200


def _load_store() -> dict:
    if os.path.exists(SESSION_STORE):
        with open(SESSION_STORE) as f:
            return json.load(f)
    return {"sessions": {}, "chunks": []}


def _save_store(store: dict):
    import tempfile
    tmp = SESSION_STORE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(store, f, indent=2)
    os.replace(tmp, SESSION_STORE)


def extract_transcript_from_jsonl(jsonl_path: str) -> list[dict]:
    """
    Parse a Claude Code JSONL session file into a list of
    {"role": "user"|"assistant", "text": str, "timestamp": str} dicts.
    """
    messages = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            ts_ms = obj.get("timestamp", 0)
            try:
                ts = datetime.fromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = str(ts_ms)

            msg = obj.get("message", {})
            content = msg.get("content", "")
            role = "user" if msg_type == "user" else "assistant"

            text_parts = []
            if isinstance(content, str) and content.strip():
                text_parts.append(content.strip())
            elif isinstance(content, list):
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    btype = block.get("type", "")
                    if btype == "text":
                        t = block.get("text", "").strip()
                        if t:
                            text_parts.append(t)
                    elif btype == "tool_use":
                        name = block.get("name", "")
                        inp = json.dumps(block.get("input", {}))[:150]
                        text_parts.append(f"[TOOL: {name}({inp})]")

            text = "\n".join(text_parts).strip()
            if text:
                messages.append({"role": role, "text": text, "timestamp": ts})

    return messages


def chunk_conversation(messages: list[dict], session_id: str) -> list[dict]:
    """
    Turn a list of messages into overlapping text chunks suitable for embedding.
    Each chunk includes enough context to be self-contained.
    """
    chunks = []
    # Build full text with role markers
    full_text = ""
    for m in messages:
        full_text += f"\n\n[{m['role'].upper()} @ {m['timestamp']}]:\n{m['text']}"

    # Sliding window chunks
    pos = 0
    chunk_idx = 0
    while pos < len(full_text):
        end = pos + CHUNK_CHARS
        chunk_text = full_text[pos:end]
        if chunk_text.strip():
            chunks.append({
                "chunk_id": f"{session_id}_{chunk_idx:04d}",
                "session_id": session_id,
                "text": chunk_text.strip(),
                "char_offset": pos,
            })
            chunk_idx += 1
        pos = end - OVERLAP_CHARS  # overlap for context continuity
        if pos >= len(full_text):
            break

    return chunks


def ingest_session(jsonl_path: str = None, text_path: str = None) -> int:
    """
    Ingest a session into the session store and vector index.
    Returns number of new chunks added.
    """
    store = _load_store()

    # Determine session ID and source
    if jsonl_path:
        session_id = os.path.splitext(os.path.basename(jsonl_path))[0]
        if session_id in store["sessions"]:
            print(f"[SESSION INGESTER] Session {session_id[:8]}... already indexed. Skipping.")
            return 0
        print(f"[SESSION INGESTER] Parsing JSONL: {jsonl_path}")
        messages = extract_transcript_from_jsonl(jsonl_path)
        source = jsonl_path
    elif text_path:
        session_id = os.path.splitext(os.path.basename(text_path))[0]
        if session_id in store["sessions"]:
            print(f"[SESSION INGESTER] Session {session_id} already indexed. Skipping.")
            return 0
        print(f"[SESSION INGESTER] Parsing text transcript: {text_path}")
        with open(text_path, encoding="utf-8") as f:
            raw = f.read()
        # Parse USER/CLAUDE blocks from extracted transcript format
        messages = []
        for block in re.split(r'\n{2}-{80}\n{2}', raw):
            match = re.match(r'\[(.+?)\] (USER|CLAUDE):\n(.*)', block, re.DOTALL)
            if match:
                ts, role, text = match.groups()
                if text.strip():
                    messages.append({"role": role.lower().replace("claude", "assistant"),
                                     "text": text.strip(), "timestamp": ts})
        source = text_path
    else:
        # Auto-discover latest JSONL
        pattern = os.path.join(CLAUDE_PROJECTS, "*.jsonl")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        if not files:
            print("[SESSION INGESTER] No JSONL files found.")
            return 0
        jsonl_path = files[0]
        return ingest_session(jsonl_path=jsonl_path)

    if not messages:
        print("[SESSION INGESTER] No messages extracted.")
        return 0

    print(f"[SESSION INGESTER] Extracted {len(messages)} messages. Chunking...")
    chunks = chunk_conversation(messages, session_id)
    print(f"[SESSION INGESTER] Generated {len(chunks)} chunks. Indexing...")

    # Add to vector index
    try:
        from miso_vector_index import VectorIndex
        vi = VectorIndex()
        indexed = 0
        for chunk in chunks:
            added = vi.add(
                node_id=chunk["chunk_id"],
                text=chunk["text"],
                metadata={"type": "session_chunk", "session_id": session_id,
                          "char_offset": chunk["char_offset"]},
            )
            if added:
                indexed += 1
        print(f"[SESSION INGESTER] Vectorized {indexed} new chunks.")
    except ImportError:
        print("[SESSION INGESTER] WARNING: miso_vector_index not available. Storing text only.")
        indexed = len(chunks)

    # Persist to session store
    store["sessions"][session_id] = {
        "source": source,
        "message_count": len(messages),
        "chunk_count": len(chunks),
        "indexed_at": datetime.now().isoformat(),
    }
    store["chunks"].extend(chunks)
    _save_store(store)

    print(f"[SESSION INGESTER] Done. Session {session_id[:8]}... ingested ({len(chunks)} chunks).")
    return len(chunks)


def search_sessions(query: str, top_k: int = 5) -> list[dict]:
    """
    Semantic search across all ingested session chunks.
    Falls back to keyword search if vector index unavailable.
    """
    try:
        from miso_vector_index import VectorIndex
        vi = VectorIndex()
        results = vi.search(query, top_k=top_k)
        # Filter to session chunks only
        return [r for r in results if r.get("metadata", {}).get("type") == "session_chunk"]
    except ImportError:
        # Keyword fallback
        store = _load_store()
        query_lower = query.lower()
        matches = []
        for chunk in store.get("chunks", []):
            if query_lower in chunk["text"].lower():
                score = chunk["text"].lower().count(query_lower) / len(chunk["text"])
                matches.append({"node_id": chunk["chunk_id"], "text": chunk["text"],
                                 "score": score, "metadata": {"session_id": chunk["session_id"]}})
        return sorted(matches, key=lambda x: -x["score"])[:top_k]


def list_sessions():
    store = _load_store()
    sessions = store.get("sessions", {})
    if not sessions:
        print("[SESSION INGESTER] No sessions indexed yet.")
        return
    print(f"\n{'='*60}")
    print("MISO SESSION STORE")
    print(f"{'='*60}")
    for sid, info in sessions.items():
        print(f"  {sid[:16]}... | {info['message_count']} msgs | {info['chunk_count']} chunks | {info['indexed_at'][:10]}")
        print(f"    source: {info['source']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MISO Session Ingester")
    parser.add_argument("--file", help="Path to JSONL or transcript .txt to ingest")
    parser.add_argument("--search", help="Search across ingested sessions")
    parser.add_argument("--list", action="store_true", help="List all indexed sessions")
    parser.add_argument("--ingest-all", action="store_true", help="Ingest all available JSONL sessions")
    args = parser.parse_args()

    if args.list:
        list_sessions()
    elif args.search:
        results = search_sessions(args.search)
        print(f"\n[SEARCH: '{args.search}'] Top {len(results)} results:\n")
        for r in results:
            sid = r.get("metadata", {}).get("session_id", "?")[:12]
            print(f"  [{sid}...] score={r.get('score', 0):.3f}")
            print(f"  {r['text'][:300]}\n")
    elif args.ingest_all:
        pattern = os.path.join(CLAUDE_PROJECTS, "*.jsonl")
        files = glob.glob(pattern)
        total = 0
        for f in files:
            total += ingest_session(jsonl_path=f)
        print(f"\n[SESSION INGESTER] Total new chunks ingested: {total}")
    elif args.file:
        if args.file.endswith(".jsonl"):
            ingest_session(jsonl_path=args.file)
        else:
            ingest_session(text_path=args.file)
    else:
        # Default: ingest current session
        ingest_session()
        list_sessions()
