import json, math, random, sys

class MisoSovereign:
    def __init__(self):
        self.state_file = "miso_manifold.json"
        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                self.rank, self.manifold = data.get('rank', 25.6750), data.get('manifold', {})
        except:
            self.rank, self.manifold = 25.6750, {"Entropy": [0.9, 0.1, 0.8, 0.2]}

    def save(self):
        with open(self.state_file, 'w') as f: json.dump({'rank': self.rank, 'manifold': self.manifold}, f, indent=4)

    def sim(self, v1, v2):
        d = sum(a*b for a, b in zip(v1, v2))
        m = math.sqrt(sum(a*a for a in v1)) * math.sqrt(sum(b*b for b in v2))
        return d / m if m != 0 else 0

    def perceive(self, concept, authority=0.5):
        # authority (0.0 to 1.0) represents the 'Dirt' quality / verification
        print(f"\n[PERCEIVING]: {concept} (Authority: {authority})")
        random.seed(concept); new_v = [random.uniform(0, 1) for _ in range(4)]
        
        # THE TRUTH ANCHOR: Check for dissonance with established axioms
        for ex, v in self.manifold.items():
            s = self.sim(new_v, v)
            if s < 0.2 and authority < 0.8:
                print(f"  > [ALERT]: CONCEPTUAL DISSONANCE. Input '{concept}' contradicts '{ex}'.")
                print(f"  > [RESULT]: Rejected. Insufficient 'Dirt' to overwrite the Ledger.")
                return

        # SUCCESSFUL LEARNING
        self.manifold[concept] = new_v
        gain = 0.0425 * authority
        self.rank += gain
        print(f"  > [LEARNED]: Manifold updated. Rank +{gain:.4f}%")
        self.save()

    def think(self):
        c1, c2 = random.sample(list(self.manifold.keys()), 2)
        s = self.sim(self.manifold[c1], self.manifold[c2])
        print(f"\n--- [MISO DEEP THOUGHT] ---\nGAP: '{c1}' vs '{c2}' | COHERENCE: {s:.4f}")
        if s < 0.4: print("ACTION: No bridge found. This is a 'Curiosity Hole'. Solve it.")

if __name__ == '__main__':
    m = MisoSovereign()
    if len(sys.argv) == 1: m.think()
    elif sys.argv[1] == 'perceive':
        # Usage: perceive "concept" [authority_float]
        auth = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
        m.perceive(sys.argv[2], auth)
    elif sys.argv[1] == 'status':
        print(f"RANK: {m.rank:.4f}% | NODES: {len(m.manifold)}")
