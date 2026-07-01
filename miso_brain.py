import duckdb
import ollama
from miso_config import SILVER_PATH, OLLAMA_URL, DEFAULT_MODEL


def _get_connection():
    """Return a fresh DuckDB connection with delta loaded."""
    con = duckdb.connect()
    con.execute("INSTALL delta; LOAD delta;")
    return con


def ask_miso(question: str) -> str:
    print(f"\n[MISO-BRAIN] Querying Substrate for: '{question}'...")

    con = _get_connection()
    # Parameterized query using the full question — not truncated to 10 chars
    search_query = (
        f"SELECT content, rationale "
        f"FROM delta_scan('{SILVER_PATH}') "
        f"WHERE UPPER(content) LIKE UPPER($1) "
        f"   OR UPPER(rationale) LIKE UPPER($1) "
        f"LIMIT 3"
    )
    results = con.execute(search_query, [f"%{question}%"]).df()
    con.close()

    if not results.empty:
        context = "\n".join(
            f"Axiom: {row['content']} (Why: {row['rationale']})"
            for _, row in results.iterrows()
        )
    else:
        context = "No specific Master Axioms found for this query."

    prompt = f"""You are MISO, a Sovereign Product Engine.
Use the following Master Axioms to answer the user's question.
If the context doesn't have the answer, use your logic but state it's a 'New Hypothesis'.

CONTEXT FROM SUBSTRATE:
{context}

USER QUESTION:
{question}

MISO RESPONSE:"""

    response = ollama.generate(model=DEFAULT_MODEL, prompt=prompt)
    return response["response"]


if __name__ == "__main__":
    user_input = input("What do you want to ask MISO? ")
    answer = ask_miso(user_input)
    print(f"\n--- MISO RESPONSE ---\n{answer}")
