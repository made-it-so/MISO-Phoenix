# MISO V63 main.py
import sys, os
from pathlib import Path
from miso_engine.agents import Agent
from miso_engine.orchestrator import Orchestrator # Make sure this import matches your project structure
import json
import subprocess
import re

def extract_json(text: str) -> dict | None:
    """Safely extracts the first valid JSON object from a string."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match: return None
    try: return json.loads(match.group(0))
    except json.JSONDecodeError: return None

def generate_file_manifest(root_dir: Path) -> str:
    """V58: Dynamically scans the filesystem and wraps in XML tags."""
    manifest_header = "<SOURCE_OF_TRUTH_FILE_MANIFEST>\n"
    manifest_footer = "\n</SOURCE_OF_TRUTH_FILE_MANIFEST>"

    file_patterns = [
        "*.py", "*.json", "Dockerfile", "*.md", "*.typed", # Root files
        "src/**/*.py", "src/**/*.json", "src/**/*.typed"  # Recursive src files
    ]
    files_found = []

    for pattern in file_patterns:
        files_found.extend(root_dir.glob(pattern))

    path_list = []
    for file_path in sorted(files_found):
        # Exclude venv directory more reliably
        if any(part == 'venv' for part in file_path.parts):
            continue
        relative_path = file_path.relative_to(root_dir)
        path_list.append(str(relative_path))

    manifest_content = json.dumps(path_list, indent=2)
    return f"{manifest_header}{manifest_content}{manifest_footer}"

def execute_shell_command(command: str, project_root: Path, agents: dict, original_task: str) -> (bool, str):
    """Executes a shell command, with V60 venv-aware specialist intervention."""
    cmd_env = os.environ.copy()
    cmd_env['MISO_ROOT'] = str(project_root)
    python_exe = sys.executable # Path to current python interpreter

    original_command = command
    for attempt in range(1, 4): # Try 1 (Original) + 2 Fixes

        run_command = command
        # Ensure python commands use the correct interpreter
        if run_command.startswith("python "):
             run_command = run_command.replace("python ", f"{python_exe} ", 1)

        print(f"      Tactician executing (Attempt {attempt}): `{run_command}`")
        result = subprocess.run(run_command, shell=True, capture_output=True, text=True, env=cmd_env, cwd=project_root) # Run from project root

        stdout_str = result.stdout.strip()
        stderr_str = result.stderr.strip()

        if result.returncode == 0:
            print(f"      ✅ Task complete.")
            if stdout_str: print(f"      STDOUT: {stdout_str}")
            # Successful shell command forces re-evaluation of the original problem
            return True, f"REFINEMENT: {original_task}"

        # --- COMMAND FAILED ---
        print(f"      ⚠️ Command failed. STDOUT: {stdout_str} STDERR: {stderr_str}")
        if attempt == 3:
            return False, f"Command failed after 2 fix attempts. STDOUT: {stdout_str} STDERR: {stderr_str}"

        print("      Delegating to ExecutionEngineerAgent for diagnosis...")
        # Ensure engineer agent exists
        if "ExecutionEngineerAgent" not in agents:
             print("      ❌ ExecutionEngineerAgent not found. Cannot diagnose.")
             return False, "ExecutionEngineerAgent not available."

        engineer = agents["ExecutionEngineerAgent"]

        engineer_prompt = f"""--- FAILED COMMAND ---
{original_command}
--- STDOUT ---
{stdout_str}
--- STDERR ---
{stderr_str}
"""
        if attempt > 1:
            engineer_prompt += f"""
--- PREVIOUS ATTEMPT ---
Your fix '{command}' succeeded, but the original command '{original_command}' failed again.
Provide a new, single command to fix this (e.g., by rewriting the command as a module call).
"""

        fix_command = engineer.run(input=engineer_prompt).strip()

        # Sanitize potential markdown
        fix_command = re.sub(r"^```(bash|sh)\n?", "", fix_command)
        fix_command = re.sub(r"\n?```$", "", fix_command).strip()

        if fix_command == "SUCCESS":
            print(f"      Engineer reports tool ran successfully (found errors).")
            # Analysis tools finding errors is a success, leads to refinement
            return True, f"REFINEMENT: The analysis tool ran successfully and found errors. Review this report and create a plan to fix them: {stdout_str}"

        if not fix_command or fix_command.startswith("{"):
            summary = "Engineer failed to provide a valid fix command."
            print(f"      ❌ {summary}")
            return False, summary

        print(f"      Engineer's fix: `{fix_command}`")

        # Prepare to run the fix command
        run_fix_command = fix_command
        if run_fix_command.startswith("python "):
            run_fix_command = run_fix_command.replace("python ", f"{python_exe} ", 1)

        # Check if the fix is an installation or a command rewrite
        if "install" in run_fix_command: # Simple check for install commands
            print(f"      Tactician executing fix...")
            fix_result = subprocess.run(run_fix_command, shell=True, capture_output=True, text=True, env=cmd_env, cwd=project_root)
            fix_stderr = fix_result.stderr.strip()

            if fix_result.returncode != 0:
                summary = f"Engineer's fix failed. STDERR: {fix_stderr}"
                print(f"      ❌ {summary}")
                # If install fails, don't retry original command in this loop
                return False, summary

            print(f"      ✅ Engineer's fix successful. Re-trying original command...")
            command = original_command # Reset command for the next loop iteration
        else:
            # Assume it's a command rewrite (e.g., 'python -m mypy ...')
            print(f"      Engineer has rewritten the command. Re-trying with new command...")
            command = fix_command # Use the rewritten command for the next loop
            # Update original_command only if the rewrite becomes the new baseline?
            # Sticking with original_command = fix_command for now as per V60 logic
            original_command = command

    return False, "Loop exited unexpectedly." # Should not be reached if max_retries > 0

def execute_task(original_problem: str, current_refinement: str, agents: dict, agent_names: list, project_root: Path, file_manifest_str: str) -> (bool, str):
    """Executes one step of a task and returns a summary/next step."""
    print(f"    - Pursuing Task Focus: '{current_refinement}'")
    planner = agents.get("PlannerAgent")
    auditor = agents.get("AuditorGeneralAgent")

    if not planner or not auditor:
        return False, "Planner or Auditor agent not found."

    planner_prompt = f"""{file_manifest_str}
<ORIGINAL_PROBLEM>
{original_problem}
</ORIGINAL_PROBLEM>
<CURRENT_REFINEMENT>
{current_refinement}
</CURRENT_REFINEMENT>
"""
    try:
        plan_str = planner.run(input=planner_prompt)
        plan = extract_json(plan_str)
    except Exception as e:
        print(f"      ❌ Error running PlannerAgent: {e}")
        return False, f"PlannerAgent execution error: {e}"


    if not plan:
        print("      ⚠️ PlannerAgent failed to generate any parsable JSON.")
        print("      Planner generated no plan. Forcing re-evaluation of original problem.")
        # If no plan, assume current refinement is done or un-plannable, go back to original
        return True, f"REFINEMENT: {original_problem}"

    print(f"      Validating plan: {plan_str}")
    audit_prompt = f"""{file_manifest_str}
<JSON_PLAN>
{json.dumps(plan, indent=2)}
</JSON_PLAN>
<AUDIT_TASK>
Validate the <JSON_PLAN> against the <SOURCE_OF_TRUTH_FILE_MANIFEST> using the V58 Chain of Verification rules. Respond ONLY with the JSON output.
</AUDIT_TASK>
"""
    try:
        audit_result_str = auditor.run(input=audit_prompt)
        audit_result = extract_json(audit_result_str)
    except Exception as e:
        print(f"      ❌ Error running AuditorAgent: {e}")
        return False, f"AuditorAgent execution error: {e}"


    if not audit_result or "audit_passed" not in audit_result:
        reason = f"Auditor returned invalid or missing CoV JSON: {audit_result_str}"
        print(f"      ❌ AUDIT FAILED: {reason}")
        return False, reason # Hard fail on bad auditor output

    if audit_result.get("audit_passed") != True:
        reason = audit_result.get("reason", "Auditor did not pass the plan.")
        print(f"      ❌ AUDIT FAILED: {reason}")
        if "verification_log" in audit_result:
            try:
                # Attempt to pretty-print the verification log if it's valid JSON/dict
                log_str = json.dumps(audit_result['verification_log'], indent=2)
                print(f"      Verification Log:\n{log_str}")
            except Exception:
                 print(f"      Verification Log (raw): {audit_result['verification_log']}")

        # If audit fails, generate a refinement asking to re-evaluate original problem including failure reason
        return True, f"REFINEMENT: Audit failed for task focus '{current_refinement}' with reason: {reason}. Re-evaluate the original problem: {original_problem}"


    print("      ✅ AUDIT PASSED. Proceeding with execution.")

    tool = plan.get('tool') # Use .get for safety
    execution_summary = ""
    task_succeeded = False

    try:
        if tool == 'read_file':
            file_path_str = plan.get("file_path")
            analysis_task = plan.get("analysis_task")
            specialist_name = plan.get("specialist_agent")

            if not all([file_path_str, analysis_task, specialist_name]):
                 task_succeeded = False
                 execution_summary = "Read_file plan missing parameters."
                 print(f"      ❌ {execution_summary}")
            elif specialist_name not in agents:
                task_succeeded = False
                execution_summary = f"Unknown specialist agent '{specialist_name}'."
                print(f"      ❌ {execution_summary}")
            else:
                target_file = project_root / file_path_str
                if not target_file.is_file():
                     task_succeeded = False
                     execution_summary = f"File not found: {target_file}"
                     print(f"      ❌ {execution_summary}")
                else:
                    file_contents = target_file.read_text()
                    specialist = agents[specialist_name]
                    analysis_prompt = f"---\nANALYSIS TASK: {analysis_task}\n---\nFILE CONTENTS:\n```\n{file_contents}\n```"
                    result_str = specialist.run(input=analysis_prompt)
                    result_json = extract_json(result_str)

                    if result_json and result_json.get("status") == "REFINED":
                        summary = result_json.get("new_problem_statement", "Analysis complete, but no new problem statement provided.")
                        print(f"      ✅ Analysis generated new refinement: {summary}")
                        execution_summary = f"REFINEMENT: {summary}"
                        task_succeeded = True
                    else:
                        execution_summary = f"Specialist agent ({specialist_name}) failed to return a valid 'REFINED' problem statement. Response: {result_str}"
                        print(f"      ⚠️ {execution_summary}")
                        task_succeeded = False # Treat failure to refine as task failure

        elif tool == 'modify_file':
            file_path_str = plan.get("file_path")
            modification_task = plan.get("modification_task")
            programmer_name = "ProgrammerAgent" # Assuming fixed programmer

            if not all([file_path_str, modification_task]):
                 task_succeeded = False
                 execution_summary = "Modify_file plan missing parameters."
                 print(f"      ❌ {execution_summary}")
            elif programmer_name not in agents:
                task_succeeded = False
                execution_summary = f"{programmer_name} not available."
                print(f"      ❌ {execution_summary}")
            else:
                target_file = project_root / file_path_str

                if not target_file.exists():
                    execution_summary = f"Refactoring failed: Tool 'modify_file' cannot create new files. '{target_file}' does not exist."
                    print(f"      ❌ {execution_summary}")
                    task_succeeded = False
                else:
                    file_contents = target_file.read_text()
                    programmer = agents[programmer_name]
                    programmer_prompt = f"""--- MODIFICATION TASK ---\n{modification_task}\n\n--- ORIGINAL FILE CONTENTS ---\n```python\n{file_contents}\n```\n\nYou MUST respond with only the new, full contents of the file."""
                    new_code = programmer.run(input=programmer_prompt)
                    # Basic cleaning, might need refinement
                    new_code = re.sub(r"^```(python)?\n?", "", new_code).strip()
                    new_code = re.sub(r"\n?```$", "", new_code).strip()
                    target_file.write_text(new_code)
                    summary = f"Refactoring complete: {target_file}"
                    print(f"      ✅ {summary}")
                    task_succeeded = True
                    execution_summary = f"REFINEMENT: {original_problem}" # Force re-eval

        elif tool == 'create_file':
            file_path_str = plan.get("file_path")
            content = plan.get("content", "") # Default to empty content

            if not file_path_str:
                 task_succeeded = False
                 execution_summary = "Create_file plan missing file_path."
                 print(f"      ❌ {execution_summary}")
            else:
                target_file = project_root / file_path_str

                if target_file.exists():
                    execution_summary = f"File creation failed: '{target_file}' already exists."
                    print(f"      ❌ {execution_summary}")
                    task_succeeded = False # Should have been caught by Auditor
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    target_file.write_text(content)
                    summary = f"File created: {target_file}"
                    print(f"      ✅ {summary}")
                    task_succeeded = True
                    execution_summary = f"REFINEMENT: {original_problem}" # Force re-eval

        elif tool == 'execute_shell':
            command = plan.get("command")
            if not command:
                 task_succeeded = False
                 execution_summary = "Execute_shell plan missing command."
                 print(f"      ❌ {execution_summary}")
            else:
                task_succeeded, execution_summary = execute_shell_command(command, project_root, agents, original_problem)

        else:
            execution_summary = f"Unknown tool '{tool}'. Skipping task."
            print(f"      ⚠️ {execution_summary}")
            task_succeeded = False

    except (KeyError, FileNotFoundError) as e:
        execution_summary = f"Execution failed due to a missing parameter or file: '{e}'."
        print(f"      ❌ {execution_summary} Skipping.")
        task_succeeded = False
    except Exception as e:
        execution_summary = f"An unexpected error occurred during tool execution: {e}."
        print(f"      ❌ {execution_summary} Skipping.")
        task_succeeded = False

    # --- Generate Report ---
    print("\n      --- Generating Task Summary ---")
    doc_agent = agents.get("DocumentationAgent")
    report = f"REFINEMENT: {original_problem}" # Default to re-evaluating original problem

    if doc_agent:
        report_prompt = f"""--- EXECUTION SUMMARY ---
{execution_summary if task_succeeded else f'Task failed: {execution_summary}'}
"""
        try:
            raw_report = doc_agent.run(input=report_prompt).strip()
            # Check if doc agent provided a refinement, otherwise use default
            if raw_report.startswith("REFINEMENT:"):
                 report = raw_report
                 print(f"      REFINEMENT FOUND: {report.replace('REFINEMENT: ', '')}")
            else:
                 # If it wasn't a refinement, just log the report but keep the default re-evaluation
                 print(f"      REPORT (non-refining): {raw_report}")
                 # The 'report' variable remains the default refinement back to original_problem

        except Exception as e:
             print(f"      ⚠️ Error running DocumentationAgent: {e}. Using default refinement.")
    else:
        print("      ⚠️ DocumentationAgent not found. Using default refinement.")


    # Ensure we always return a refinement string if task succeeded
    if task_succeeded and not report.startswith("REFINEMENT:"):
        report = f"REFINEMENT: {original_problem}"

    return task_succeeded, report


def run_miso_system(problem_statement: str):
    """Initializes and runs the MISO V63 system."""
    print(f"🚀 MISO V63 System Initialized.")
    project_root = Path(os.getcwd())

    agent_names = ["PlannerAgent", "ProgrammerAgent", "DocumentationAgent", "AuditorGeneralAgent", "ExecutionEngineerAgent"]

    agents = {}
    try:
        agents = { name: Agent(persona_name=name) for name in agent_names }
        print("    All agents initialized.")
    except FileNotFoundError:
        print(f"❌ CRITICAL: Could not find 'src/miso_engine/personas.py'. Make sure it exists and is readable. Halting.")
        return
    except KeyError as e:
        print(f"❌ CRITICAL: Persona '{e}' not found in 'src/miso_engine/personas.py'. Check the file content. Halting.")
        return
    except Exception as e:
        print(f"❌ CRITICAL: Failed to initialize agents (check 'src/miso_engine/personas.py'): {type(e).__name__}: {e}. Halting.")
        return

    original_problem = problem_statement
    current_refinement = problem_statement
    last_refinement = ""

    MAX_LOOPS = 25
    loop_count = 0
    for loop_count in range(1, MAX_LOOPS + 1):
        print(f"\n--- MISO LOOP {loop_count} ---")

        print("    ...regenerating file manifest...")
        file_manifest_str = generate_file_manifest(project_root)

        task_succeeded, report = execute_task(original_problem, current_refinement, agents, agent_names, project_root, file_manifest_str)

        if not task_succeeded:
            print("      ❌ Task failed. Halting loop.")
            break

        if report.startswith("REFINEMENT:"):
            next_refinement = report.replace("REFINEMENT: ", "").strip()
            # V63: Simplified Stagnation Check
            if next_refinement == current_refinement:
                print("      ✅ Refinement stagnated. Assuming task is complete. Halting loop.")
                break

            last_refinement = current_refinement
            current_refinement = next_refinement
            print("      Task step complete. Proceeding to next refined problem.")

            if loop_count == MAX_LOOPS:
                 print(f"      ❌ SAFETY BRAKE: Loop limit ({MAX_LOOPS}) reached after completing loop {loop_count}. Halting.")
        else:
            # This case should ideally not be reached if execute_task always returns REFINEMENT on success
            print("      ✅ Task step complete. No further refinements generated by agents (unexpected). Halting loop.")
            break


if __name__ == "__main__":
    print("🚀 MISO V63 Interactive Shell Initialized.") # Updated version number
    print("   Enter a single, direct task for the MISO council or 'exit' to quit.")
    while True:
        problem = input("\n[MISO Task]: ") # Changed prompt label to match V60+
        if problem.lower() == 'exit':
            print("MISO shutting down.")
            break
        if not problem.strip():
            continue
        print("\n⚠️ IMPORTANT: Ensure workspace is clean (git reset --hard && rm -rf src/plugin_loader src/py.typed) before proceeding.")
        confirm = input("   Confirm workspace is clean? (yes/no): ").lower().strip()
        if confirm == 'yes':
            run_miso_system(problem)
            print("\n🏁 MISO Task Concluded. Awaiting next problem.")
        else:
            print("   ❌ Aborting task. Please clean the workspace.")
