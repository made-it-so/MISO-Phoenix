#!/usr/bin/env python3
import os
import re
import json
import shutil
import tempfile
import subprocess
from collections import deque

try:
    from brains.lizard import run_lizard_brain
    from brains.mammal import run_mammal_brain
    from brains.primate import run_primate_brain
    from brains.human import run_human_brain
    from cache.solution_cache import GLOBAL_SOLUTION_CACHE
    from utils.context import generate_context_for_error
    from utils.sandbox import Sandbox
    from utils.git_tools import get_current_branch, create_new_branch, commit_plan, abandon_changes, push_branch
except ImportError as e:
    print(f"ERROR: Could not import sub-systems: {e}")
    print("Please ensure all modules (brains, cache, utils) are in the correct directories and __init__.py files exist.")
    exit(1)

# --- (THE FIX: All paths are relative to the GIT ROOT) ---
GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MYPY_COMMAND = f"mypy {os.path.join(GIT_ROOT_DIR, 'miso_project', 'workspace')}"
PYTEST_COMMAND = f"pytest {os.path.join(GIT_ROOT_DIR, 'miso_project', 'workspace')}"
BASE_WORKSPACE = os.path.join("miso_project", "workspace") # Relative path from Git Root

class MISO_Agent:
    def __init__(self, base_workspace):
        self.base_workspace = base_workspace
        self.tdd_backlog = deque()
        self.original_branch = get_current_branch()
        self.feature_branch = None

    def run_test_suite(self) -> list:
        print("--- CONDUCTOR: Running TDD Harness ---")
        
        # --- STAGE 1: MYPY ---
        print("--- 1. Running MYPY (Static Analysis) ---")
        try:
            result_mypy = subprocess.run(
                MYPY_COMMAND, shell=True, capture_output=True,
                text=True, timeout=60, cwd=GIT_ROOT_DIR
            )
        except Exception as e:
            print(f"🚨 CONDUCTOR: Fatal error running mypy: {e}")
            return [f"Fatal error: {e}"]

        if result_mypy.returncode != 0:
            print("📊 Found MYPY failure. Populating backlog.")
            full_output = result_mypy.stdout + result_mypy.stderr
            error_line_regex = re.compile(r".*error:.*\[.*\]")
            parsed_errors = [line.strip() for line in full_output.splitlines() if error_line_regex.match(line.strip())]
            return sorted(list(set(parsed_errors))) if parsed_errors else [full_output]

        # --- STAGE 2: PYTEST ---
        print("--- 2. Running PYTEST (Runtime Analysis) ---")
        try:
            result_pytest = subprocess.run(
                PYTEST_COMMAND, shell=True, capture_output=True,
                text=True, timeout=60, cwd=GIT_ROOT_DIR
            )
        except Exception as e:
            print(f"🚨 CONDUCTOR: Fatal error running pytest: {e}")
            return [f"Fatal error: {e}"]

        if result_pytest.returncode != 0:
            print("📊 Found PYTEST failure. Capturing full traceback.")
            return [result_pytest.stdout + result_pytest.stderr]

        print("✅ TDD SUITE PASSED (Mypy + Pytest). Backlog is empty.")
        return []

    def verify_plan_in_sandbox(self, plan: list) -> dict:
        if not plan:
            return {"status": "FAILED", "exit_code": -1, "error_output": "Empty plan."}

        try:
            # (THE FIX: Sandbox path is now correct)
            sandbox_workspace_path = os.path.join(GIT_ROOT_DIR, self.base_workspace)
            with Sandbox(base_workspace_path=sandbox_workspace_path) as sandbox:
                try:
                    sandbox.apply_plan(plan)
                except Exception as e:
                    return {"status": "FAILED", "exit_code": -1, "error_output": f"Invalid plan: {e}", "plan": plan}

                # (THE FIX: Sandbox commands run from its temp_dir, but paths are absolute)
                sandbox_mypy_cmd = f"mypy {sandbox.sandbox_path}"
                sandbox_pytest_cmd = f"pytest {sandbox.sandbox_path}"

                (exit_code_mypy, out_mypy) = sandbox.run_command(sandbox_mypy_cmd, cwd=sandbox.temp_dir)
                if exit_code_mypy != 0:
                    first_error = next((line for line in out_mypy.splitlines() if "error:" in line), out_mypy)
                    return {"status": "FAILED", "exit_code": exit_code_mypy, "error_output": first_error, "plan": plan}
                
                (exit_code_pytest, out_pytest) = sandbox.run_command(sandbox_pytest_cmd, cwd=sandbox.temp_dir)
                if exit_code_pytest != 0:
                    return {"status": "FAILED", "exit_code": exit_code_pytest, "error_output": out_pytest, "plan": plan}

                return {"status": "VERIFIED", "plan": plan}
        
        except Exception as e:
            return {"status": "FAILED", "exit_code": -2, "error_output": f"Sandbox fatal error: {e}", "plan": plan}

    def run_elastic_cascade(self, isolated_error, file_context) -> (dict, str):
        failure_history = []
        current_error = isolated_error
        
        # --- TIER 1: LIZARD 🦎 ---
        plan_1 = run_lizard_brain(current_error, file_context)
        result_1 = self.verify_plan_in_sandbox(plan_1)
        if result_1["status"] == "VERIFIED": return result_1, "Tier 1 (Lizard)"
        failure_history.append({"tier": "Lizard", "result": result_1})
        if result_1.get("exit_code", -1) > 0:
            current_error = result_1.get("error_output", current_error)

        # --- TIER 2: MAMMAL 🧠 ---
        plan_2 = run_mammal_brain(current_error, file_context)
        result_2 = self.verify_plan_in_sandbox(plan_2)
        if result_2["status"] == "VERIFIED": return result_2, "Tier 2 (Mammal)"
        failure_history.append({"tier": "Mammal", "result": result_2})
        if result_2.get("exit_code", -1) > 0:
            current_error = result_2.get("error_output", current_error)

        # --- TIER 3: PRIMATE 🐒 ---
        plan_3 = run_primate_brain(current_error, file_context)
        result_3 = self.verify_plan_in_sandbox(plan_3)
        if result_3["status"] == "VERIFIED": return result_3, "Tier 3 (Primate)"
        failure_history.append({"tier": "Primate", "result": result_3})
        if result_3.get("exit_code", -1) > 0:
            current_error = result_3.get("error_output", current_error)

        # --- TIER 4/5: HUMAN 👨‍🔬 ---
        print("🚨 ESCALATION: Primate brain failed. Engaging Human brain.")
        plan_4 = run_human_brain(current_error, file_context, failure_history)
        result_4 = self.verify_plan_in_sandbox(plan_4)
        if result_4["status"] == "VERIFIED": return result_4, "Tier 4 (Human)"
        failure_history.append({"tier": "Human", "result": result_4})

        print("🔥🔥🔥 CATASTROPHIC FAILURE: All tiers failed.")
        return result_4, "None"

    def start(self):
        print("--- MISO AGENT (Git-Aware Conductor) ACTIVATED ---")
        
        initial_errors = self.run_test_suite()
        if not initial_errors:
            print("--- ✅ MISO AGENT: No TDD errors found on 'main'. Work complete. ---")
            return

        self.feature_branch = create_new_branch(self.original_branch)
        if not self.feature_branch:
            print("🚨 MISO AGENT: HALTED. Could not create feature branch.")
            return

        self.tdd_backlog.extend(initial_errors)
        
        loop_count = 0
        while self.tdd_backlog and loop_count < 100:
            loop_count += 1
            current_error = self.tdd_backlog.popleft()
            
            print(f"\n--- MISO LOOP {loop_count} | Backlog: {len(self.tdd_backlog)} ---")
            print(f"🎯 ISOLATING ERROR: {current_error[:500]}...")
            
            file_context = generate_context_for_error(current_error)
            
            verification_result, successful_tier = self.run_elastic_cascade(current_error, file_context)
            
            if verification_result["status"] == "VERIFIED":
                print("✅ CASCADE: VERIFIED")
                commit_message = f"MISO {successful_tier}: Fix TDD error"
                commit_plan(verification_result["plan"], commit_message, self.base_workspace)
                print(f"💡 CONDUCTOR: Learning new solution. Adding to Mammal Cache.")
                GLOBAL_SOLUTION_CACHE.add(current_error, verification_result["plan"])
                
                print("♻️ REFRESHING TDD BACKLOG...")
                self.tdd_backlog.clear()
                self.tdd_backlog.extend(self.run_test_suite())
                
            else: # "FAILED"
                print(f"❌ CASCADE: FAILED. Error persisted or changed.")
                print(f"   REASON: {verification_result.get('error_output', 'Unknown')[:1000]}...")
                
                if not self.tdd_backlog:
                     self.tdd_backlog.extend(self.run_test_suite())

        if not self.tdd_backlog:
            print("\n--- ✅ MISO AGENT: TDD SUITE PASSED. ---")
            push_branch(self.feature_branch)
        else:
            print(f"\n--- 🚨 MISO AGENT: HALTED. Loop limit reached. ---")
            print("--- Abandoning all changes and returning to 'main'. ---")
            abandon_changes(self.original_branch)

if __name__ == "__main__":
    # (THE FIX: Change CWD to the Git Root, not the script dir)
    GIT_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(GIT_ROOT_DIR)
    
    # (THE FIX: Set PYTHONPATH to include the project root)
    os.environ['PYTHONPATH'] = GIT_ROOT_DIR + os.pathsep + os.environ.get('PYTHONPATH', '')
    
    agent = MISO_Agent(base_workspace=BASE_WORKSPACE)
    agent.start()
