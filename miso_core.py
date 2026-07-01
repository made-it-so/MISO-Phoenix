"""
MISO Core — primary query interface.

Retrieval strategy (in priority order):
1. Vector search (semantic, via miso_vector_index) if the index has nodes.
2. SQL LIKE fallback (parameterized) if vector index is empty or unavailable.
"""
import duckdb
import ollama
import sys
import requests
from miso_config import SILVER_PATH, OLLAMA_URL, DEFAULT_MODEL

# Vector index is optional — if it hasn't been built yet, fall back to SQL
try:
    from miso_vector_index import VectorIndex
    _vector_index = VectorIndex()
except Exception:
    _vector_index = None


def check_brain() -> bool:
    try:
        requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return True
    except Exception:
        return False


def _retrieve_vector(prompt: str, top_k: int = 5) -> str | None:
    """Return formatted context string from vector search, or None if unavailable."""
    if _vector_index is None or len(_vector_index) == 0:
        return None
    try:
        results = _vector_index.search(prompt, top_k=top_k)
        if not results:
            return None
        lines = [
            f"Node {r['node_id']} (score={r['score']:.3f}): {r['text']}"
            for r in results
        ]
        return "\n".join(lines)
    except Exception as e:
        print(f"[!] Vector search failed, falling back to SQL: {e}")
        return None


def _retrieve_sql(prompt: str, limit: int = 5) -> str | None:
    """Return formatted context string from parameterized SQL LIKE search."""
    try:
        con = duckdb.connect()
        con.execute("INSTALL delta; LOAD delta;")
        query = (
            f"SELECT node_id, content, rationale, originator "
            f"FROM delta_scan('{SILVER_PATH}') "
            f"WHERE UPPER(content) LIKE UPPER($1) "
            f"LIMIT {limit}"
        )
        results = con.execute(query, [f"%{prompt}%"]).df()
        con.close()
        if results.empty:
            return None
        return "\n".join(
            f"Node {r['node_id']} [{r['originator']}]: {r['content']}"
            for _, r in results.iterrows()
        )
    except Exception as e:
        return f"[SQL retrieval error: {e}]"


def deep_query(prompt: str) -> str:
    # Try vector search first
    context = _retrieve_vector(prompt)
    retrieval_method = "VECTOR"

    # Fall back to SQL
    if context is None:
        context = _retrieve_sql(prompt)
        retrieval_method = "SQL"

    if context is None:
        return f"ZERO_MATCH_ERROR: No data found for '{prompt}'."

    print(f"  [retrieval={retrieval_method}]")

    client = ollama.Client(host=OLLAMA_URL)
    try:
        response = client.generate(
            model=DEFAULT_MODEL,
            prompt=f"Context:\n{context}\n\nUser: {prompt}",
            options={"num_ctx": 4096},
        )
        return response["response"]
    except Exception as e:
        return f"BRAIN_TIMEOUT: The server is busy or slow. (Error: {e})"


if __name__ == "__main__":
    print("\n--- MISO HARDWIRED CORE v3.0 ---")
    if not check_brain():
        print(f"[!] ERROR: Cannot reach Ollama at {OLLAMA_URL}")
        sys.exit(1)

    if _vector_index and len(_vector_index) > 0:
        print(f"[✓] Vector index loaded: {len(_vector_index)} nodes.")
    else:
        print("[~] Vector index empty — using SQL retrieval. Run miso_vector_index.py to build it.")

    print("[✓] HANDSHAKE SUCCESSFUL.")
    while True:
        cmd = input("\n[Awaiting Command] > ")
        if cmd.lower() in ["exit", "quit"]:
            break
        print(f"\n[MISO]: {deep_query(cmd)}")
