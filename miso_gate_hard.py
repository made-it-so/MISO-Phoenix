"""
Hard gate: binary comparator for density thresholds.
Uses Python arithmetic — not an LLM — for deterministic numeric evaluation.
"""


def sovereign_gate_hard(d_actual: float = 0.04, d_min: float = 0.05) -> str:
    result = "PURGE" if d_actual < d_min else "KEEP"
    print(f"\n--- GATE_RESULT: {result} ---")
    return result


if __name__ == "__main__":
    sovereign_gate_hard()
