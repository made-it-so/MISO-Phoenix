import math
from decimal import Decimal, getcontext

getcontext().prec = 60

class MisoEmpiricist:
    def __init__(self):
        # MISO now holds a 'Belief Ledger' where Truth is a function of Logic + Data
        self.knowledge_base = {}

    def teach_grounding(self, node_id, theory_logic, observation_data):
        print(f"\n--- [MISO v125: EMPIRICAL GROUNDING - NODE {node_id}] ---")
        
        # STEP 1: THE AXIOMATIC DERIVATION (Internal Math)
        print(f"[MISO LOGIC]: Deriving expected outcome from First Principles...")
        expected_value = self._derive_logic(theory_logic)
        
        # STEP 2: THE EVIDENCE INGESTION (External Data)
        print(f"[MISO EVIDENCE]: Ingesting raw experimental data from Node {node_id}...")
        observed_value = Decimal(str(observation_data))
        
        # STEP 3: THE CONVERGENCE AUDIT
        # MISO is taught: Belief = 1.0 ONLY if |Logic - Data| < Tolerance
        delta = abs(expected_value - observed_value)
        tolerance = Decimal('0.05') # The '5% Reality Buffer'
        
        print(f"\n[AUDIT RESULTS]:")
        print(f"  > Theoretical Prediction : {expected_value:.4f}")
        print(f"  > Experimental Observation: {observed_value:.4f}")
        print(f"  > Delta (Discrepancy)    : {delta:.4f}")

        if delta <= tolerance:
            print("\n[VERDICT]: CONVERGENCE ACHIEVED. Conclusion is Grounded in Evidence.")
            self.knowledge_base[node_id] = {"status": "VERIFIED", "value": observed_value}
        else:
            print("\n[VERDICT]: DIVERGENCE DETECTED. Logic is hallucinating or Data is flawed.")
            print("[ACTION]: Rejecting Conclusion. Re-initiating First Principles.")

    def _derive_logic(self, theory):
        # Simulated logic derivation (e.g., calculating resistance or energy)
        if "Chiral" in theory: return Decimal('1.0000') # Ideal case
        return Decimal('0.8700')

if __name__ == '__main__':
    miso = MisoEmpiricist()
    
    # CASE STUDY: Graphene Ballistic Transport
    # MISO Logic predicts 1.0 (Ballistic)
    # Expert Data shows 0.982 (Near-Ballistic)
    miso.teach_grounding(1346, "Chiral Symmetry forbidden backscattering", 0.982)
    
    # CASE STUDY: Room Temp Superconductor Claim
    # MISO Logic predicts 1.0 (Possible)
    # Expert Data shows 0.450 (Noisy/Failure)
    miso.teach_grounding(1373, "Standard BCS Theory", 0.450)
