# MISO Triage Agent - "UNIFIED COORDINATOR" (Tier 0)
# This is the final, production-ready agent.
# It uses the "Critic" brain to decide where to route single tasks.

import re
import os
import asyncio
from miso_brains import CriticBrain, LizardBrain, HumanBrain, EinsteinBrain

class MisoTriageAgent:
    def __init__(self):
        # The coordinator has access to all brain types
        self.critic_brain = CriticBrain() # <-- NEW: Tier 0 Brain
        self.lizard_brain = LizardBrain()
        self.human_brain = HumanBrain()
        self.einstein_brain = EinsteinBrain()
        
        # Regex to parse 'filename.py:line: error: message'
        self.mypy_error_regex = re.compile(
            r"^(.*?\.py):\d+: error: (.*?) \[", re.MULTILINE
        )

    # --- METHOD 1: SINGLE-TASK ESCALATION (NEW "CRITIC" LOGIC) ---
    def decide_brain(self, error_log):
        """
        This is the new "Tier 0" routing logic.
        It calls the Critic brain (async) to assess difficulty,
        then routes to the correct specialist.
        """
        print(f"[TRIAGE_AGENT]: Analyzing single task...")
        
        if not error_log:
            print("[TRIAGE_AGENT]: No errors found. Standing by.")
            return None
            
        # --- Step 1: Assess Difficulty (Call Tier 0) ---
        # We must create a new asyncio event loop to run our
        # async 'assess_difficulty' method from a sync method.
        try:
            print("[TRIAGE_AGENT]: Calling Tier 0 Critic to assess difficulty...")
            tier_assessment = asyncio.run(
                self.critic_brain.assess_difficulty(error_log)
            )
        except Exception as e:
            print(f"[TRIAGE_AGENT]: CRITICAL. Tier 0 Critic call failed: {e}")
            print("[TRIAGE_AGENT]: Defaulting to Tier 5 (Human).")
            tier_assessment = "Tier 5"

        # --- Step 2: Route to Specialist ---
        print(f"[TRIAGE_AGENT]: Critic assessed task as {tier_assessment}.")
        if "Tier 2" in tier_assessment:
            print("[TRIAGE_AGENT]: Routing to Tier 2 (Lizard).")
            return self.lizard_brain
        elif "Tier 6" in tier_assessment:
            print("[TRIAGE_AGENT]: Routing to Tier 6 (Einstein).")
            return self.einstein_brain
        else: # "Tier 5" or any other fallback
            print("[TRIAGE_AGENT]: Routing to Tier 5 (Human).")
            return self.human_brain

    # --- METHOD 2: PARALLEL SWARM (Unchanged) ---
    async def coordinate_fix_swarm(self, error_log: str) -> (float, int):
        """
        This is the "Async Swarm" logic.
        It parses a mypy log and uses asyncio.gather
        to dispatch all LizardBrain fixes in parallel.
        """
        print("[COORDINATOR]: Received new batch of errors. Analyzing for async swarm execution...")
        total_cost = 0
        tasks_fixed = 0
        
        all_errors = self.mypy_error_regex.findall(error_log)
        files_to_fix = sorted(list(set([filename for filename, msg in all_errors])))
        
        if not files_to_fix:
            print("[COORDINATOR]: No parseable mypy errors found in log.")
            return 0.0, 0

        print(f"[COORDINATOR]: Identified {len(files_to_fix)} unique files. Building task list...")

        tasks = []
        file_order = []
        
        for filename in files_to_fix:
            file_error_msg = ""
            for err_file, err_msg in all_errors:
                if err_file == filename:
                    file_error_msg = err_msg
                    break

            if "missing a type annotation" in file_error_msg:
                try:
                    with open(filename, 'r') as f:
                        original_code = f.read()
                    tasks.append(self.lizard_brain.fix(original_code, file_error_msg))
                    file_order.append(filename)
                except Exception as e:
                    print(f"  [COORDINATOR]: Error reading {filename}: {e}")
            else:
                print(f"  [COORDINATOR]: No agent available for error in {filename}: '{file_error_msg}'")

        print(f"[COORDINATOR]: Dispatching swarm of {len(tasks)} Lizard agents...")
        try:
            results = await asyncio.gather(*tasks)
        except Exception as e:
            print(f"[COORDINATOR]: *** CRITICAL SWARM FAILURE: {e}")
            return 0.0, 0

        print("[COORDINATOR]: Swarm execution complete. Processing results...")
        
        for filename, result in zip(file_order, results):
            fixed_code, cost = result
            if fixed_code:
                try:
                    with open(filename, 'w') as f:
                        f.write(fixed_code)
                    print(f"  [LIZARD_RESULT -> {filename}]: Fix applied successfully.")
                    total_cost += cost
                    tasks_fixed += 1
                except Exception as e:
                    print(f"  [COORDINATOR]: Error writing {filename}: {e}")
            else:
                print(f"  [LIZARD_RESULT -> {filename}]: FAILED to apply fix.")

        print(f"[COORDINATOR]: Swarm task complete. {tasks_fixed} files fixed.")
        return total_cost, tasks_fixed
