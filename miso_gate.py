"""
Density gate: determines whether a node should be PURGED or INTEGRATED
based on whether its actual density meets the minimum threshold.

Replaced the previous implementation which used an LLM to evaluate a
simple numeric comparison — a language model is the wrong tool for arithmetic.
"""
from miso_config import MANIFOLD_PATH
import json
import os


def density_gate(d_actual: float, d_min: float) -> str:
    """Return 'PURGE' if d_actual is below d_min, else 'INTEGRATE'."""
    return "PURGE" if d_actual < d_min else "INTEGRATE"


def sovereign_gate():
    d_min = 0.05
    d_actual = 0.04

    result = density_gate(d_actual, d_min)
    print(f"\n--- GATE_RESULT: {result} ---")
    return result


if __name__ == "__main__":
    sovereign_gate()
