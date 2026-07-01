"""
MISO Vector Index — semantic retrieval layer.

Replaces LIKE-based substring search with embedding-based cosine similarity.
Embeddings are generated via Ollama's /api/embeddings endpoint (no external
dependencies beyond what's already installed).

The index is stored as a JSON file alongside the manifold:
  miso_vector_index.json  ->  { "node_id": { "text": "...", "embedding": [...] } }

Usage:
    from miso_vector_index import VectorIndex
    idx = VectorIndex()
    idx.add("G_001", "Entropy is a measure of disorder in a system.")
    results = idx.search("what is thermodynamic entropy?", top_k=5)
"""
import json
import math
import os
import requests
from miso_config import OLLAMA_URL, DEFAULT_MODEL, MANIFOLD_PATH

INDEX_PATH = os.path.join(os.path.dirname(MANIFOLD_PATH), "miso_vector_index.json")
EMBED_MODEL = os.environ.get("MISO_EMBED_MODEL", DEFAULT_MODEL)


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def _embed(text: str) -> list[float]:
    """Call Ollama embeddings endpoint. Returns a float vector.

    Tries /api/embeddings (legacy) then /api/embed (v0.3+).
    Returns empty list if no embedding model is available — callers
    should check for empty list and degrade to keyword search.
    """
    for endpoint, payload in [
        (f"{OLLAMA_URL}/api/embeddings", {"model": EMBED_MODEL, "prompt": text}),
        (f"{OLLAMA_URL}/api/embed",      {"model": EMBED_MODEL, "input": text}),
    ]:
        try:
            r = requests.post(endpoint, json=payload, timeout=30)
            r.raise_for_status()
            data = r.json()
            vec = data.get("embedding") or (data.get("embeddings") or [[]])[0]
            if vec:
                return vec
        except Exception:
            continue
    return []  # no embedding model available — caller degrades gracefully


class VectorIndex:
    """
    In-memory vector index backed by a JSON file.
    Thread-safety note: load/save is not atomic. For concurrent writes,
    use a proper vector DB (e.g., chroma, qdrant) in production.
    """

    def __init__(self, index_path: str = INDEX_PATH):
        self.path = index_path
        self._index: dict[str, dict] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._index = json.load(f)

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._index, f)

    def add(self, node_id: str, text: str, metadata: dict | None = None, force: bool = False) -> bool:
        """
        Embed `text` and store under `node_id`.
        Skips if node_id already exists unless force=True.
        Returns True if added, False if skipped.
        If embedding is unavailable, stores text-only (keyword fallback still works).
        """
        if node_id in self._index and not force:
            return False
        embedding = _embed(text)
        self._index[node_id] = {
            "text": text,
            "embedding": embedding,  # may be [] if no embed model
            "metadata": metadata or {},
        }
        self._save()
        return True

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Return the top_k most semantically similar nodes to `query`.
        Falls back to keyword search if no embedding model available.
        Each result: { "node_id", "score", "text", "metadata" }
        """
        if not self._index:
            return []

        query_vec = _embed(query)

        # Keyword fallback when embedding unavailable
        if not query_vec:
            query_lower = query.lower()
            results = []
            for node_id, entry in self._index.items():
                text = entry.get("text", "")
                count = text.lower().count(query_lower)
                if count > 0:
                    score = count / max(len(text), 1)
                    results.append({"node_id": node_id, "score": score,
                                    "text": text, "metadata": entry.get("metadata", {})})
            return sorted(results, key=lambda x: -x["score"])[:top_k]

        scored = []
        for node_id, entry in self._index.items():
            stored_vec = entry.get("embedding", [])
            if not stored_vec:
                continue  # skip text-only entries in vector search
            score = _cosine(query_vec, stored_vec)
            scored.append({
                "node_id": node_id,
                "score": score,
                "text": entry["text"],
                "metadata": entry.get("metadata", {}),
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._index)

    def node_ids(self) -> list[str]:
        return list(self._index.keys())


def build_index_from_manifold():
    """
    One-time indexing pass: embed all axioms in miso_manifold.json
    that aren't yet in the vector index.
    """
    with open(MANIFOLD_PATH, "r", encoding="utf-8") as f:
        manifold = json.load(f)

    idx = VectorIndex()
    axioms = manifold.get("axioms", [])
    new_count = 0

    for i, entry in enumerate(axioms):
        text = entry.get("axiom", "")
        if not text:
            continue
        node_id = f"MANIFOLD_AXIOM_{i}"
        if node_id not in idx.node_ids():
            try:
                idx.add(node_id, text, metadata={"score": entry.get("score"), "type": entry.get("type")})
                new_count += 1
                print(f"  [+] Indexed {node_id}")
            except RuntimeError as e:
                print(f"  [!] Failed to embed {node_id}: {e}")

    print(f"\n[VECTOR INDEX] Done. {new_count} new nodes indexed. Total: {len(idx)}")


if __name__ == "__main__":
    print("[VECTOR INDEX] Building index from manifold axioms...")
    build_index_from_manifold()
