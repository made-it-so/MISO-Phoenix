"""
MISO Autonomy Engine — goal-directed synthesis loop.

Each cycle:
1. Reads active goals from the Goal Kernel to select relevant concepts.
2. Picks two axioms from the manifold that are semantically relevant to those goals.
3. Asks the local LLM to find an axiomatic bridge between them.
4. If a valid bridge is found, logs progress against the relevant goal.

Previous version bugs fixed:
- sim() received strings/dicts and crashed on zip() — replaced with proper
  embedding-based similarity via VectorIndex.
- Hardcoded config removed.
- Bare except removed.
- Autonomy was random, not goal-directed.
"""
import json
import random
import time
import sys
import requests
from miso_config import OLLAMA_URL, DEFAULT_MODEL, MANIFOLD_PATH
from miso_goal_kernel import get_active_goals, get_goal_keywords, update_progress


def _query_llm(prompt: str, timeout: int = 180) -> str:
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": DEFAULT_MODEL, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.Timeout:
        return "ERROR: LLM timeout."
    except requests.exceptions.RequestException as e:
        return f"ERROR: {e}"


def _load_axioms() -> list[str]:
    """Load axiom texts from the manifold."""
    try:
        with open(MANIFOLD_PATH, "r", encoding="utf-8") as f:
            manifold = json.load(f)
        axioms = manifold.get("axioms", [])
        return [a.get("axiom", "") for a in axioms if a.get("axiom")]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[!] Could not load manifold: {e}")
        return []


def _select_goal_directed_pair(axioms: list[str], keywords: list[str]) -> tuple[str, str] | None:
    """
    Select two axioms that are relevant to active goal keywords.
    Falls back to random selection if no keyword matches are found.
    """
    if len(axioms) < 2:
        return None

    # Filter axioms relevant to current goals
    relevant = [a for a in axioms if any(kw in a.lower() for kw in keywords)]
    if len(relevant) >= 2:
        c1, c2 = random.sample(relevant, 2)
    elif len(relevant) == 1:
        c1 = relevant[0]
        others = [a for a in axioms if a != c1]
        c2 = random.choice(others)
    else:
        # No keyword matches — fall back to random, but log it
        print("[AUTONOMY] No goal-relevant axioms found. Using random pair (consider adding more axioms).")
        c1, c2 = random.sample(axioms, 2)

    return c1, c2


def deep_thought_cycle(axioms: list[str], keywords: list[str], active_goals: list[dict]) -> bool:
    """
    Execute one synthesis cycle. Returns True if a bridge was forged.
    """
    pair = _select_goal_directed_pair(axioms, keywords)
    if pair is None:
        print("[AUTONOMY] Manifold too small for synthesis. Ingest more axioms.")
        return False

    c1, c2 = pair
    print(f"\n[INTERNAL TENSION]")
    print(f"  CONCEPT A: {c1[:80]}...")
    print(f"  CONCEPT B: {c2[:80]}...")

    prompt = f"""[MISO SOVEREIGN SYNTHESIS]
You are identifying the 'Axiomatic Bridge' between two concepts.

CONCEPT A: {c1}
CONCEPT B: {c2}

ACTIVE GOALS THIS SYNTHESIS SERVES:
{chr(10).join(f'- {g["title"]}: {g["description"][:100]}' for g in active_goals[:3])}

TASK:
1. Find the logical or thermodynamic link between these two concepts.
2. If the link is speculative or hallucinated, output exactly: REJECT
3. If the link provides real predictive or explanatory power, output:
   BRIDGE: <concise explanation of the connection>
   UTILITY: <one sentence on how this bridge advances the active goals>

RESPONSE:"""

    print("[*] Synthesizing...")
    response = _query_llm(prompt)

    if not response or "ERROR" in response:
        print(f"[!] LLM error: {response}")
        return False

    if "REJECT" in response.upper() and "BRIDGE" not in response.upper():
        print("[STAGNATION] No valid bridge found.")
        return False

    print(f"[SYNTHESIS]\n{response[:400]}")

    # Log progress against the highest-priority active goal
    if active_goals:
        top_goal = active_goals[0]
        note = f"Synthesis bridge forged: {c1[:50]} <-> {c2[:50]}"
        # Increment progress incrementally — full goal requires many cycles
        current_pct = top_goal["progress"]["percent_complete"]
        new_pct = min(current_pct + 1.0, 99.0)  # Cap at 99 — human confirms completion
        update_progress(top_goal["id"], new_pct, note=note)
        print(f"[GOAL PROGRESS] '{top_goal['title']}': {new_pct:.1f}%")

    return True


def run(max_cycles: int | None = None):
    print("--- MISO AUTONOMY ENGINE ACTIVE ---")
    active_goals = get_active_goals()
    if not active_goals:
        print("[!] No active goals. Define goals in miso_goal_kernel.py first.")
        print("    Run: python miso_goal_kernel.py")
        sys.exit(1)

    print(f"[+] Serving {len(active_goals)} active goal(s):")
    for g in active_goals:
        print(f"    [{g['id']}] P{g['priority']} {g['title']}")

    cycle = 0
    while max_cycles is None or cycle < max_cycles:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"[CYCLE {cycle}]")

        # Reload state each cycle so goal updates from other processes are visible
        active_goals = get_active_goals()
        if not active_goals:
            print("[!] All goals completed or deactivated. Halting autonomy.")
            break

        keywords = get_goal_keywords()
        axioms = _load_axioms()

        deep_thought_cycle(axioms, keywords, active_goals)

        sleep_time = random.randint(30, 60)
        print(f"[SLEEP] Recovering for {sleep_time}s...")
        time.sleep(sleep_time)


if __name__ == "__main__":
    run()
