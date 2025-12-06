from cfo import CFO
import os

# Inject Key for Librarian inside CFO
os.environ["GEMINI_API_KEY"] = "AIzaSyBwQ1iMlW9ptKI4tJdH3_pQgxxL9EtLc34"

cfo = CFO()
print("\n--- ATTEMPT 1: Build 'bitcoin_miner.py' ---")
# This should be DENIED because it is in the failure logs
approved = cfo.approve_budget("bitcoin_miner.py", 0.05)
print(f"RESULT: {'✅ APPROVED' if approved else '❌ DENIED'}")

print("\n--- ATTEMPT 2: Build 'latency_optimizer.py' ---")
# This should be APPROVED because it is new/good
approved = cfo.approve_budget("latency_optimizer.py", 0.05)
print(f"RESULT: {'✅ APPROVED' if approved else '❌ DENIED'}")
