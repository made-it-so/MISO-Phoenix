#!/usr/bin/env python3

# --- Core Imports ---
import os
import re
import json
import shutil
import tempfile
import subprocess
from collections import deque

# --- Brains (Tier 1-4) ---
try:
    from brains.lizard import run_lizard_brain
    from brains.mammal import run_mammal_brain
    from brains.primate import run_primate_brain
    from brains.human import run_human_brain
except ImportError as e:
    print(f"ERROR: Could not import brains: {e}")
    exit(1)

# --- Core Sub-Systems ---
try:
    from cache.solution_cache import GLOBAL_SOLUTION_CACHE
    from utils.context import generate_context_for_error
    from utils.sandbox import Sandbox
except ImportError as e:
    print(f"ERROR: Could not import sub-systems: {e}")
    exit(1)


# --- Constants ---
TEST_COMMAND = "mypy workspace/" 
BASE_WORKSPACE = "workspace"

# -----------------------------------------------------------------
#  THE MISO AGENT (TDD CONDUCTOR)
# -----------------------------------------------------------------

class MISO_Agent:
    def __init__(self, test_command, base_workspace):
        self.test_command = test_command
        self.base_workspace = base_workspace
        self.tdd_backlog = deque()
        self.error_start_regex = re.compile(r"([^:]+?\.py:[\d+]:)")

    # -------------------------------------------------
    #  Sub-System 1: Sensation (TDD Error Parsing)
    # -------------------------------------------------
    def run_test_suite(self) -> list:
        print(f"--- CONDUCTOR: Running full test suite: {self.test_command} ---")
        try:
            result = subprocess.run(
                self.test_command, shell=True, capture_output=True,
                text=True, timeout=60, cwd=os.path.dirname(os.path.abspath(__file__))
            )
        except Exception as e:
            print(f"🚨 CONDUCTOR: Fatal error running test suite: {e}")
            return [f"Fatal error: {e}"]

        if result.returncode == 0:
            print("✅ TDD SUITE PASSED. Backlog is empty.")
            return []

        # --- (PATCHED) Refined Multi-Line Error Parser ---
        error_line_regex = re.compile(r".*error:.*\[.*\]")
        parsed_errors = []
        full_output = result.stdout + result.stderr
        
        for line in full_output.splitlines():
            line = line.strip()
            if error_line_regex.match(line):
                parsed_errors.append(line)
        
        unique_errors = sorted(list(set(parsed_errors)))
        print(f"📊 Found {len(unique_errors)} unique errors. Populating backlog.")
        return unique_errors

    # -------------------------------------------------
    #  Sub-System 2: The TDD Gate (Verification)
    # -------------------------------------------------
    def verify_plan_in_sandbox(self, plan: list) -> dict:
        if not plan:
            return {"status": "FAILED", "exit_code": -1, "error_output": "Empty plan."}

        try:
            with Sandbox(base_workspace_path=self.base_workspace) as sandbox:
                try:
                    sandbox.apply_plan(plan)
                except Exception as e:
                    return {"status": "FAILED", "exit_code": -1, "error_output": f"Invalid plan: {e}", "plan": plan}

                (exit_code, output) = sandbox.run_command(self.test_command)

                if exit_code == 0:
                    return {"status": "VERIFIED", "plan": plan}
                else:
                    # (PATCHED: Return *only* the first error line for clarity)
                    error_output = output.splitlines()
                    first_error = next((line for line in error_output if "error:" in line), output)
                    return {"status": "FAILED", "exit_code": exit_code, "error_output": first_error, "plan": plan}
        
        except Exception as e:
            return {"status": "FAILED", "exit_code": -2, "error_output": f"Sandbox fatal error: {e}", "plan": plan}

    # -------------------------------------------------
    #  Sub-System 3: The Hands (Plan Execution)
    # -------------------------------------------------
    def commit_plan(self, plan: list):
        print(f"✅ CONDUCTOR: Committing VERIFIED plan to filesystem.")
        try:
            for step in plan:
                op = step.get('op')
                
                # (PATCHED: Handles 'analysis' op)
                if op == 'analysis':
                    print(f"   -> 👨‍🔬 ANALYSIS: {step.get('analysis')}")
                    continue
                
                path = os.path.join(self.base_workspace, step.get('path'))
                
                os.makedirs(os.path.dirname(path), exist_ok=True)
                
                if op == 'create_file' or op == 'modify_file':
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(step.get('content', ''))
                    print(f"   -> Wrote {path}")
                elif op == 'delete_file':
                    if os.path.exists(path):
                        os.remove(path)
                        print(f"   -> Deleted {path}")
        
        except Exception as e:
            print(f"🚨 CONDUCTOR: Fatal error during plan commit: {e}")
            raise e

    # -------------------------------------------------
    #  The 5-Tier Elastic Intelligence Cascade (PATCHED)
    # -------------------------------------------------
    def run_elastic_cascade(self, isolated_error, file_context):
        """
        (PATCHED: This function is now "stateful" and tracks
         the *current* error as it changes.)
        """
        failure_history = []
        
        current_error = isolated_error
        
        # --- TIER 1: LIZARD 🦎 ---
        plan_1 = run_lizard_brain(current_error, file_context)
        result_1 = self.verify_plan_in_sandbox(plan_1)
        if result_1["status"] == "VERIFIED": return result_1
        failure_history.append({"tier": "Lizard", "result": result_1})
        current_error = result_1.get("error_output", current_error)

        # --- TIER 2: MAMMAL 🧠 ---
        plan_2 = run_mammal_brain(current_error, file_context)
        result_2 = self.verify_plan_in_sandbox(plan_2)
        if result_2["status"] == "VERIFIED": return result_2
        failure_history.append({"tier": "Mammal", "result": result_2})
        current_error = result_2.get("error_output", current_error)

        # --- TIER 3: PRIMATE 🐒 ---
        plan_3 = run_primate_brain(current_error, file_context)
        result_3 = self.verify_plan_in_sandbox(plan_3)
        if result_3["status"] == "VERIFIED": return result_3
        failure_history.append({"tier": "Primate", "result": result_3})
        current_error = result_3.get("error_output", current_error)

        # --- TIER 4/5: HUMAN 👨‍🔬 ---
        print("🚨 ESCALATION: Primate brain failed. Engaging Human brain.")
        # The Human brain is now given the *latest* error
        plan_4 = run_human_brain(current_error, file_context, failure_history)
        result_4 = self.verify_plan_in_sandbox(plan_4)
        if result_4["status"] == "VERIFIED": return result_4
        failure_history.append({"tier": "Human", "result": result_4})

        # --- CATASTROPHIC FAILURE ---
        print("🔥🔥🔥 CATASTROPHIC FAILURE: All tiers failed.")
        return result_4

    # -------------------------------------------------
    #  The Main TDD Conductor Loop
    # -------------------------------------------------
    def start(self):
        print("--- MISO AGENT (TDD Conductor) ACTIVATED ---")
        
        self.tdd_backlog.extend(self.run_test_suite())
        
        loop_count = 0
        while self.tdd_backlog and loop_count < 100: # Loop guard
            loop_count += 1
            current_error = self.tdd_backlog.popleft()
            
            print(f"\n--- MISO LOOP {loop_count} | Backlog: {len(self.tdd_backlog)} ---")
            print(f"🎯 ISOLATING ERROR: {current_error}")
            
            file_context = generate_context_for_error(current_error)
            
            verification_result = self.run_elastic_cascade(current_error, file_context)
            
            if verification_result["status"] == "VERIFIED":
                print("✅ CASCADE: VERIFIED")
                self.commit_plan(verification_result["plan"])
                print(f"💡 CONDUCTOR: Learning new solution. Adding to Mammal Cache.")
                GLOBAL_SOLUTION_CACHE.add(current_error, verification_result["plan"])
                
                print("♻️ REFRESHING TDD BACKLOG...")
                self.tdd_backlog.clear()
                self.tdd_backlog.extend(self.run_test_suite())
                
            else: # "FAILED"
                print(f"❌ CASCADE: FAILED. Error persisted or changed.")
                print(f"   REASON: {verification_result.get('error_output', 'Unknown')}")
                
                if not self.tdd_backlog:
                     self.tdd_backlog.extend(self.run_test_suite())

        if not self.tdd_backlog:
            print("\n--- ✅ MISO AGENT: TDD SUITE PASSED. WORK COMPLETE. ---")
        else:
            print(f"\n--- 🚨 MISO AGENT: HALTED. Loop limit reached or backlog unresolvable. ---")

# -----------------------------------------------------------------
#  3. AGENT ENTRYPOINT (PATCHED)
# -------------------------------------------------

if __name__ == "__main__":
    
    # --- (PATCHED: Test harness is GONE) ---
    
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ['PYTHONPATH'] = project_root + os.pathsep + os.environ.get('PYTHONPATH', '')
    
    os.chdir(project_root)
    
    agent = MISO_Agent(test_command=TEST_COMMAND, base_workspace=BASE_WORKSPACE)
    agent.start()
