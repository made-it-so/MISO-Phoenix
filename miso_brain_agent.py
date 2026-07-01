"""
MISO Brain Agent — grounded knowledge retrieval and reasoning.

The Brain Agent is the epistemic core of MISO. It answers questions by:
1. Retrieving semantically relevant nodes from the knowledge substrate.
2. Grounding the response in those nodes — not generating freely.
3. Flagging when the substrate has no relevant context (rather than hallucinating).
4. Consulting active goals so responses are oriented toward what MISO is working on.

This is a proper agent class, not a standalone script. It is consumed by
moe_router.py, miso_core.py, and any other module that needs grounded reasoning.
"""
import json
from dataclasses import dataclass, field
from miso_config import OLLAMA_URL, DEFAULT_MODEL, MANIFOLD_PATH
from miso_swarm_orchestrator import call_model
from miso_goal_kernel import get_active_goals

try:
    from miso_vector_index import VectorIndex
    _has_vector = True
except ImportError:
    _has_vector = False


@dataclass
class BrainResponse:
    answer: str
    sources: list[dict]          # nodes that grounded the answer
    grounded: bool               # True if substrate context was found
    goal_context: list[str]      # active goal titles this response serves
    confidence: str              # "HIGH" | "MEDIUM" | "LOW" | "NONE"


class BrainAgent:
    """
    Grounded reasoning agent backed by the MISO knowledge substrate.

    Usage:
        brain = BrainAgent()
        result = brain.query("What is the relationship between entropy and intelligence?")
        print(result.answer)
    """

    def __init__(self, top_k: int = 5):
        self.top_k = top_k
        self._vector_index = VectorIndex() if _has_vector else None

    def _retrieve_context(self, question: str) -> list[dict]:
        """Retrieve the most relevant substrate nodes for a question."""
        if self._vector_index and len(self._vector_index) > 0:
            results = self._vector_index.search(question, top_k=self.top_k)
            return [{"id": r["node_id"], "text": r["text"], "score": r["score"],
                     "method": "vector"} for r in results]

        # Fallback: scan manifold axioms with simple substring match
        try:
            with open(MANIFOLD_PATH, "r", encoding="utf-8") as f:
                manifold = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        q_lower = question.lower()
        matches = []
        for i, entry in enumerate(manifold.get("axioms", [])):
            text = entry.get("axiom", "")
            if any(word in text.lower() for word in q_lower.split() if len(word) > 4):
                matches.append({"id": f"AXIOM_{i}", "text": text,
                                "score": entry.get("score", 0.5), "method": "keyword"})
            if len(matches) >= self.top_k:
                break
        return matches

    def _format_context(self, nodes: list[dict]) -> str:
        if not nodes:
            return ""
        lines = []
        for n in nodes:
            score_str = f"{n['score']:.3f}" if isinstance(n['score'], float) else str(n['score'])
            lines.append(f"[{n['id']} | relevance={score_str}]: {n['text']}")
        return "\n".join(lines)

    def query(self, question: str) -> BrainResponse:
        nodes = self._retrieve_context(question)
        active_goals = get_active_goals()
        goal_titles = [g["title"] for g in active_goals]

        grounded = len(nodes) > 0
        context_str = self._format_context(nodes)

        if grounded:
            confidence = "HIGH" if nodes[0]["score"] > 0.8 else "MEDIUM" if nodes[0]["score"] > 0.5 else "LOW"
        else:
            confidence = "NONE"

        goal_str = ""
        if active_goals:
            goal_str = "\n\nACTIVE GOALS (orient your response toward these):\n" + \
                       "\n".join(f"- {g['title']}: {g['description'][:100]}" for g in active_goals[:3])

        if grounded:
            prompt = f"""You are MISO's Brain Agent. You reason only from verified substrate nodes.

SUBSTRATE CONTEXT (these are your ground truth nodes):
{context_str}
{goal_str}

QUESTION: {question}

INSTRUCTIONS:
- Answer using ONLY the substrate context above.
- If the context is insufficient, say "SUBSTRATE INSUFFICIENT: <what is missing>"
- Do NOT hallucinate facts not present in the context.
- Cite the node IDs you used: e.g., [AXIOM_3, AXIOM_7]

BRAIN RESPONSE:"""
        else:
            prompt = f"""You are MISO's Brain Agent. The substrate has no relevant context for this query.
{goal_str}

QUESTION: {question}

INSTRUCTIONS:
- State clearly: "SUBSTRATE INSUFFICIENT: No relevant nodes found."
- Provide a brief 'New Hypothesis' if you can reason from first principles.
- Mark it clearly as hypothesis, not verified substrate knowledge.

BRAIN RESPONSE:"""

        answer = call_model("reason", prompt, priority=1)

        return BrainResponse(
            answer=answer,
            sources=nodes,
            grounded=grounded,
            goal_context=goal_titles,
            confidence=confidence,
        )

    def status(self) -> dict:
        vector_count = len(self._vector_index) if self._vector_index else 0
        return {
            "vector_index_nodes": vector_count,
            "retrieval_method": "vector" if vector_count > 0 else "keyword_fallback",
            "model": DEFAULT_MODEL,
            "active_goals": len(get_active_goals()),
        }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    brain = BrainAgent()
    st = brain.status()
    print(f"\n[BRAIN AGENT] Online")
    print(f"  Retrieval : {st['retrieval_method']}")
    print(f"  Nodes     : {st['vector_index_nodes']}")
    print(f"  Goals     : {st['active_goals']} active\n")

    while True:
        try:
            q = input("[BRAIN] Query > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q.lower() in {"exit", "quit"}:
            break
        if not q:
            continue

        result = brain.query(q)
        print(f"\n[ANSWER] (confidence={result.confidence}, grounded={result.grounded})")
        print(result.answer)
        if result.sources:
            print(f"\n[SOURCES] {[s['id'] for s in result.sources]}")
        print()
