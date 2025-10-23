import sys
import os
import re
import json
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

# --- FIX: ADD SRC TO SYS.PATH ---
# This ensures 'miso_engine' can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
# --- END FIX ---

from miso_engine.agents import Agent
from miso_engine.util import (
    read_file, write_file, create_file, get_file_manifest,
    run_shell, extract_json
)

# --- GLOBAL AGENT DICT ---
agents: Dict[str, Agent] = {}


def validate_plan(plan_json: Dict[str, Any], auditor: Agent, manifest: str) -> Tuple[bool, str]:
    """
    Validates a plan using the AuditorGeneralAgent.
    This logic now correctly handles the 'audit_passed' key.
    """
    print(f"      Validating plan: ```json\n{json.dumps(plan_json, indent=2)}\n```")
    
    audit_prompt = f"""--- JSON PLAN TO AUDIT ---
{json.dumps(plan_json, indent=2)}
--- FILE MANIFEST ---
{manifest}
--- TASK ---
You are an AI Auditor. Your job is to validate this JSON plan.
1.  Check for semantic errors (e.g., trying to `modify_file` to solve an analysis task).
2.  Check for manifest violations (e.g., `file_path` not in the manifest).
3.  The variable `$MISO_ROOT` is a valid, pre-defined environment variable. Do not flag it.

Respond with ONLY a JSON object.
- If valid, respond with: `{{"audit_passed": true}}`
- If invalid, respond with: `{{"audit_passed": false, "reason": "Your detailed explanation..."}}`
"""
    try:
        audit_result_str = auditor.run(input=audit_prompt)
        audit_result = extract_json(audit_result_str)
    except Exception as e:
        print(f"      ❌ Error running AuditorAgent: {e}")
        return False, f"AuditorAgent execution error: {e}"

    # --- FIX: Handle 'audit_passed' key ---
    if not audit_result or "audit_passed" not in audit_result:
        reason = f"Auditor returned invalid or missing JSON: {audit_result_str}"
        print(f"      ❌ AUDIT FAILED: {reason}")
        return False, reason

    if audit_result.get("audit_passed") != True:
        reason = audit_result.get("reason", "Auditor did not pass the plan.")
        print(f"      ❌ AUDIT FAILED: {reason}")
        return False, reason
    # --- END FIX ---

    print("      ✅ AUDIT PASSED. Proceeding with execution.")
    return True, "Audit passed."


def execute_plan_step(plan: Dict[str, Any], project_root: Path) -> Tuple[bool, str]:
    """
    Executes a single, validated plan step.
    Contains the refactored logic for handling shell command failures.
    """
    tool = plan.get("tool")
    
    try:
        if tool == "read_file":
            file_path = project_root / plan["file_path"]
            content = read_file(file_path)
            
            analyst = agents.get(plan["specialist_agent"])
            if not analyst:
                return False, f"Specialist agent '{plan['specialist_agent']}' not found."
            
            analysis_prompt = f"""--- FILE CONTENT ---
{content}
--- ANALYSIS TASK ---
{plan['analysis_task']}
--- RESPONSE FORMAT ---
You MUST respond with a JSON object containing a "problem_statement" key.
"""
            analysis_result = analyst.run(input=analysis_prompt)
            # This result is the new refinement
            return True, f"REFINEMENT: {extract_json(analysis_result).get('problem_statement', 'No problems found.')}"

        elif tool == "modify_file":
            file_path = project_root / plan["file_path"]
            programmer = agents.get("ProgrammerAgent")
            if not programmer:
                return False, "ProgrammerAgent not found."
            
            current_content = read_file(file_path)
            modification_prompt = f"""--- CURRENT FILE CONTENT ---
{current_content}
--- MODIFICATION TASK ---
{plan['modification_task']}
--- RESPONSE ---
Respond with ONLY the new, full file content.
"""
            new_content = programmer.run(input=modification_prompt)
            write_file(file_path, new_content)
            return True, f"Refactoring complete: {file_path.relative_to(project_root)}"

        elif tool == "create_file":
            file_path = project_root / plan["file_path"]
            create_file(file_path, plan["content"])
            return True, f"File created: {file_path.relative_to(project_root)}"

        elif tool == "execute_shell":
            command = plan["command"]
            print(f"      Tactician executing (Attempt 1): `{command}`")
            success, stdout, stderr = run_shell(command, cwd=project_root)
            
            if success:
                return True, f"Command executed successfully. STDOUT: {stdout}"
            
            # --- FAILURE: DELEGATE TO ENGINEER ---
            print(f"      ⚠️ Command failed. STDOUT: {stdout} STDERR: {stderr}")
            print(f"      Delegating to ExecutionEngineerAgent for diagnosis...")
            engineer = agents.get("ExecutionEngineerAgent")
            if not engineer:
                return False, "ExecutionEngineerAgent not found."

            engineer_prompt = f"""--- FAILED COMMAND ---
`{command}`
--- STDOUT ---
{stdout}
--- STDERR ---
{stderr}
--- TASK ---
You are an Execution Engineer. Diagnose this failure.
- If it's a 'command not found' error, respond with a JSON object to install it.
- If it's a Python error (e.g., 'No module named'), respond with a JSON object to `pip install` it.
- If it's a non-fixable error (e.g., a real Python traceback or a tool failure), respond with `SUCCESS`. This indicates the tool ran but found errors, which is a 'successful' analysis.

--- RESPONSE FORMAT ---
`{{"tool": "execute_shell", "command": "pip install ... or apt-get install ..."}}`
OR
`SUCCESS`
"""
            
            # --- FIX: REFACTORED JSON PARSING LOGIC ---
            fix_command_str = engineer.run(input=engineer_prompt).strip()

            # Sanitize potential markdown (e.g., ```json ... ```)
            fix_command_str = re.sub(r"^```(json|bash|sh)?\n?", "", fix_command_str)
            fix_command_str = re.sub(r"\n?```$", "", fix_command_str).strip()

            if fix_command_str == "SUCCESS":
                print(f"      Engineer reports tool ran successfully (found errors).")
                return True, f"REFINEMENT: The analysis tool ran successfully and found errors: {stderr}"

            try:
                # The Engineer is a 'worker' that returns JSON
                fix_data = json.loads(fix_command_str)
                if "command" not in fix_data:
                    raise ValueError("JSON response missing 'command' key")
                fix_command = fix_data["command"]
            except Exception as e:
                # If JSON parsing fails or keys are wrong, it's a failure.
                summary = f"Engineer failed to provide a valid fix command. Error: {e}. Raw output: {fix_command_str}"
                print(f"      ❌ {summary}")
                return False, summary
            # --- END FIX ---

            print(f"      Engineer's fix: `{fix_command}`")
            print(f"      Tactician executing (Attempt 2): `{fix_command}`")
            fix_success, fix_stdout, fix_stderr = run_shell(fix_command, cwd=project_root)
            
            if not fix_success:
                return False, f"Engineer's fix failed. STDOUT: {fix_stdout} STDERR: {fix_stderr}"
            
            print(f"      ✅ Engineer's fix applied. Retrying original command...")
            retry_success, retry_stdout, retry_stderr = run_shell(command, cwd=project_root)
            
            if not retry_success:
                return False, f"Retry after fix failed. STDOUT: {retry_stdout} STDERR: {retry_stderr}"
            
            return True, f"Command executed successfully after fix. STDOUT: {retry_stdout}"

        else:
            return False, f"Unknown tool: {tool}"
            
    except Exception as e:
        print(f"      ❌ CRITICAL ERROR during execution: {e}")
        return False, f"Unhandled exception: {e}"


def run_miso_system(problem_statement: str):
    """Initializes and runs the MISO V63 system."""
    print(f"🚀 MISO V63 System Initialized.")
    project_root = Path(os.getcwd())
    
    # This list must match the agents defined in personas.py
    agent_names = ["PlannerAgent", "ProgrammerAgent", "DocumentationAgent", "AuditorGeneralAgent", "ExecutionEngineerAgent"]

    global agents
    try:
        agents = { name: Agent(persona_name=name) for name in agent_names }
        print("    All agents initialized.")
    except KeyError as e:
        # This was the 'persona' key error
        print(f"❌ CRITICAL: Failed to initialize agents. A persona is missing a required key (e.g., 'persona'). Error: {e}. Halting.")
        return
    except ValueError as e:
        # This was the original 'PlannerAgent not found' error
        print(f"❌ CRITICAL: {e}. Check 'src/miso_engine/personas.py'. Halting.")
        return
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize agents (check 'src/miso_engine/personas.py'): {type(e).__name__}: {e}. Halting.")
        return

    original_problem = problem_statement
    current_refinement = problem_statement
    last_refinement = ""
    
    planner = agents.get("PlannerAgent")
    auditor = agents.get("AuditorGeneralAgent")
    doc_agent = agents.get("DocumentationAgent")

    if not all([planner, auditor, doc_agent]):
        print("❌ CRITICAL: Core agents (Planner, Auditor, Documentation) are missing. Halting.")
        return

    # --- THIS IS THE FIX: Increased loop limit from 11 to 21 ---
    for i in range(1, 51): # Max 20 loops
        print(f"\n--- MISO LOOP {i} ---")
        
        # --- STATE MANAGER (part 1) ---
        print("    ...regenerating file manifest...")
        manifest_json = get_file_manifest(project_root)
        
        # --- STRATEGIST ---
        print(f"    - Pursuing Task Focus: '{current_refinement}'")
        plan_prompt = f"""<SOURCE_OF_TRUTH_FILE_MANIFEST>
{manifest_json}
</SOURCE_OF_TRUTH_FILE_MANIFEST>

<ORIGINAL_PROBLEM>
{original_problem}
</ORIGINAL_PROBLEM>

<CURRENT_REFINEMENT>
{current_refinement}
</CURRENT_REFINEMENT>

Based on all inputs, generate the single JSON plan for the next logical step.
"""
        try:
            plan_str = planner.run(input=plan_prompt)
            plan = extract_json(plan_str)
            if not plan:
                raise ValueError("Planner returned invalid or empty JSON.")
        except Exception as e:
            print(f"      ❌ Planner failed: {e}. Halting loop.")
            break
            
        # --- AUDITOR (part of Aggregator) ---
        is_valid, reason = validate_plan(plan, auditor, manifest_json)
        if not is_valid:
            print(f"      ❌ Task failed. Halting loop.")
            break
            
        # --- TASK DISPATCHER / EXECUTOR ---
        task_succeeded, execution_summary = execute_plan_step(plan, project_root)
        if not task_succeeded:
            print(f"      ❌ {execution_summary} Skipping.")
        
        # --- RESULT AGGREGATOR / Refinement ---
        print("\n      --- Generating Task Summary ---")
        
        # Default report assumes stagnation
        report = f"REFINEMENT: {original_problem}" 

        if doc_agent:
            report_prompt = f"""--- EXECUTION SUMMARY ---
{execution_summary}
--- ORIGINAL PROBLEM ---
{original_problem}
"""
            try:
                raw_report = doc_agent.run(input=report_prompt).strip()
                
                # Check if doc agent provided a new refinement
                if raw_report.startswith("REFINEMENT:"):
                    report = raw_report
                    print(f"      REFINEMENT FOUND: {report.replace('REFINEMENT: ', '')}")
                else:
                    # This is a simple success. Set the report to the non-refining string.
                    print(f"      REPORT (non-refining): {raw_report}")
                    report = raw_report # <-- This was the fix from last time

            except Exception as e:
                print(f"      ⚠️ Error running DocumentationAgent: {e}. Using default refinement.")
        else:
            print("      ⚠️ DocumentationAgent not found. Using default refinement.")

        # --- STATE MANAGER (part 2) ---
        if not task_succeeded:
            print("      ❌ Task failed. Halting loop.")
            break

        if report.startswith("REFINEMENT:"):
            next_refinement = report.replace("REFINEMENT: ", "").strip()
            
            # V63: Simplified Stagnation Check
            if next_refinement == current_refinement:
                print("      ✅ Refinement stagnated. Assuming task is complete. Halting loop.")
                break

            last_refinement = current_refinement
            current_refinement = next_refinement
            print("      Task step complete. Proceeding to next refined problem.")
        
        # --- THIS IS THE FINAL FIX ---
        else:
            # This is a simple report, not a refinement.
            # DO NOT HALT. Continue the loop.
            # The PlannerAgent will be re-run with the same problem,
            # but a NEW file manifest, and will find the next logical step.
            print(f"      ✅ Simple task step complete: {report}")
            print("      Continuing loop to re-evaluate task...")
            pass # <-- FIX: This was 'break'
        # --- END FIX ---


def main_interactive_shell():
    """Runs the MISO interactive shell."""
    print("🚀 MISO V63 Interactive Shell Initialized.")
    print("   Enter a single, direct task for the MISO council or 'exit' to quit.")
    
    while True:
        print("\n" + "="*80)
        try:
            problem_statement = input("[MISO Task]: ")
            if problem_statement.lower() == 'exit':
                print("🏁 MISO Shutting Down. Goodbye.")
                break
            
            if not problem_statement:
                continue

            print("\n⚠️ IMPORTANT: Ensure workspace is clean (git reset --hard && rm -rf src/plugin_loader src/py.typed) before proceeding.")
            confirmation = input("   Confirm workspace is clean? (yes/no): ").strip().lower()
            
            if confirmation == 'yes':
                run_miso_system(problem_statement)
            else:
                print("   ❌ Task aborted. Please clean the workspace.")

        except KeyboardInterrupt:
            print("\n🏁 MISO Shutting Down. Goodbye.")
            break
        except Exception as e:
            print(f"\n❌ CRITICAL SHELL ERROR: {e}")
            print("Restarting shell...")

        print("\n🏁 MISO Task Concluded. Awaiting next problem.")


if __name__ == "__main__":
    main_interactive_shell()
