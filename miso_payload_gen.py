"""
HLE payload generator.

WARNING: The previous version of this script injected 100 nodes with
identical, hardcoded placeholder content — every node had the same axiom
and derivation string. This pollutes the knowledge base and degrades
retrieval quality. Nodes must carry unique, source-derived content.

This version requires a source_map: a dict mapping node_id -> real content
derived from the actual source material. It will refuse to write if the
source_map contains duplicated content.
"""
import json
import os
from miso_config import SHARED_BUFFER


def generate_hle_payload(source_map: dict):
    """
    Write HLE nodes to the shared buffer.

    Args:
        source_map: dict mapping node_id (str, e.g. "HLE_1901") to a dict
                    with keys: source, verification, axiom, derivation.
                    All values must be unique — duplicate content is rejected.
    """
    if not source_map:
        raise ValueError("source_map is empty — nothing to write.")

    # Reject duplicate content
    derivations = [v.get("derivation", "") for v in source_map.values()]
    if len(set(derivations)) != len(derivations):
        raise ValueError(
            "Duplicate derivation content detected in source_map. "
            "Each node must carry unique, source-derived content."
        )

    print(f"[🧬] GENERATING HLE PAYLOAD: {len(source_map)} nodes")

    with open(SHARED_BUFFER, "r", encoding="utf-8-sig") as f:
        brain = json.load(f)

    # Check for overwrites
    existing_keys = set(brain.keys()) & set(source_map.keys())
    if existing_keys:
        print(f"[!] WARNING: Overwriting {len(existing_keys)} existing nodes: {sorted(existing_keys)[:5]}...")

    brain.update(source_map)

    with open(SHARED_BUFFER, "w", encoding="utf-8") as f:
        json.dump(brain, f, indent=4)

    print(f"[✅] PAYLOAD ANCHORED: {len(source_map)} nodes written to buffer.")


if __name__ == "__main__":
    # Example: populate this dict from your actual source material.
    # Do NOT use identical placeholder strings for every node.
    example_map = {
        "HLE_1901": {
            "source": "MIT_8.333_Statistical_Mechanics",
            "verification": "Primary Source Verified",
            "axiom": "REPLACE WITH REAL AXIOM FROM SOURCE",
            "derivation": "REPLACE WITH REAL DERIVATION FROM SOURCE",
        }
    }
    print("[!] This is an example. Populate source_map with real content before running.")
    # generate_hle_payload(example_map)
