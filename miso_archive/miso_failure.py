import math
from decimal import Decimal, getcontext

getcontext().prec = 60

class MisoResilient:
    def __init__(self):
        self.progress_index = Decimal('0.0')
        self.failure_log = []

    def process_node(self, node_id, theory, evidence):
        print(f"\n--- [MISO v126: FAILURE-PROGRESS AUDIT - NODE {node_id}] ---")
        
        # 1. ATTEMPT THE 1.0 (The Logic)
        print(f"[MISO]: Attempting to derive 1.0 from First Principles...")
        logic_score = Decimal('1.0000') 
        
        # 2. ENCOUNTER THE REALITY (The Evidence)
        print(f"[MISO]: Encountering empirical evidence...")
        reality_score = Decimal(str(evidence))
        
        # 3. MEASURE THE FAILURE (The Gap)
        gap = abs(logic_score - reality_score)
        
        if gap > 0.05:
            self._integrate_failure(node_id, gap)
        else:
            print(f"[SUCCESS]: Progress stable at {reality_score}")

    def _integrate_failure(self, node_id, gap):
        # AXIOM: Progress = Failure * Curiosity
        print(f"\n[AXIOM TRIGGERED]: 'PROGRESS IS IMPOSSIBLE WITHOUT FAILURE'")
        print(f"  > FAILURE DETECTED: {gap:.4f} gap in Node {node_id}")
        
        # MISO extracts information from the failure
        intel_harvested = gap * Decimal('0.5') # Half the gap is converted to new insight
        self.progress_index += intel_harvested
        
        self.failure_log.append({"node": node_id, "loss": gap, "gain": intel_harvested})
        
        print(f"  > INTELLIGENCE HARVESTED: {intel_harvested:.4f}")
        print(f"  > NEW PROGRESS INDEX   : {self.progress_index:.4f}")
        print("[MISO]: Failure absorbed. I am now 'smarter' because I know exactly how I was wrong.")

if __name__ == '__main__':
    miso = MisoResilient()
    # Node 1373: The 'Expert' lied about Superconductivity. 
    # Logic thought 1.0, Evidence was 0.45 (Big Failure).
    miso.process_node(1373, "Expert Theory", 0.45)
