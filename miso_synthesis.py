import json
import os
from miso_config import MANIFOLD_PATH

AXIOM = (
    "AXIOM: System Sovereignty is achieved when the Confidence Dichotomy is resolved "
    "via deterministic feedback loops (Verification) rather than noisy evidence (Search)."
)
RIGIDITY = 0.95


def synthesis_stitch():
    print("[+] PERFORMING SYNTHESIS STITCH...")
    try:
        with open(MANIFOLD_PATH, "r") as f:
            data = json.load(f)

        axioms = data.setdefault("axioms", [])

        # Prevent duplicate axiom injection
        existing_texts = {a.get("axiom") for a in axioms}
        if AXIOM in existing_texts:
            print("[=] Axiom already present. No change written.")
            return

        axioms.append({"axiom": AXIOM, "score": RIGIDITY})
        data["rank"] += RIGIDITY * 0.10

        with open(MANIFOLD_PATH, "w") as f:
            json.dump(data, f, indent=4)

        print(f"\n[!] SUCCESS: Synthesis Anchored. New Rank: {data['rank']:.4f}%")

    except Exception as e:
        print(f"[X] STITCH FRACTURE: {e}")


if __name__ == "__main__":
    synthesis_stitch()
