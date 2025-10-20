import sys, os
from pathlib import Path
from miso_engine.agents import Agent
from miso_engine.orchestrator import Orchestrator
import json
import subprocess

def extract_json(text: str) -> dict | None:
    import re
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if not match: return None
    try: return json.loads(match.group(0))
    except json.JSONDecodeError: return None

def execute_approved_project(bid: dict, agents: dict, agent_names: list):
    """Executes milestones using the V31.13 Roster-Aware Orchestrator."""
    project_root = Path(os.getcwd())
    project_name = bid.get("project_name", "miso_project")
    orchestrator = Orchestrator(
        sandbox_root=project_root / project_name / "sandboxes",
        workspace_root=project_root / project_name / "workspace"
    )
    
    orchestrator.workspace_root.mkdir(parents=True, exist_ok=True)

    print("\n--- Project Execution Commencing ---")
    for milestone in bid["milestones"]:
        milestone_name = milestone.get('milestone_name', 'Unnamed Milestone')
        tasks = milestone.get('tasks', [milestone] if isinstance(milestone, str) else [])

        print(f"\n▶️  Pursuing Milestone: '{milestone_name}'")

        for task in tasks:
            print(f"    - Pursuing Task: '{task}'")
            
            with orchestrator.sandbox() as sandbox_path:
                roster_str = ", ".join(f"'{name}'" for name in agent_names)
                architect_prompt = f"""--- TASK ---
{task}

--- AVAILABLE SPECIALISTS ---
{roster_str}
--- END AVAILABLE SPECIALISTS ---

Based on the task and available specialists, design a JSON plan using the tool manifest from your persona."""

                briefing_str = agents['ArchitectAgent'].run(input=architect_prompt)
                briefing = extract_json(briefing_str)

                if not briefing or 'tool' not in briefing:
                    print("      ⚠️ Architect failed to create a valid plan. Skipping task.")
                    continue

                if briefing['tool'] == 'read_file':
                    file_path_str = briefing.get("file_path")
                    analysis_task = briefing.get("analysis_task")
                    specialist_name = briefing.get("specialist_agent")

                    if not all([file_path_str, analysis_task, specialist_name]):
                        print("      ❌ Architect proposed a 'read_file' task with missing parameters. Skipping.")
                        continue
                    
                    if specialist_name not in agents:
                        print(f"      ❌ Architect delegated to an unknown or unavailable agent: '{specialist_name}'. Skipping.")
                        continue

                    try:
                        target_file = project_root / file_path_str
                        print(f"      Reading file: {target_file}")
                        file_contents = target_file.read_text()
                        
                        specialist = agents[specialist_name]
                        print(f"      Delegating to {specialist_name} for analysis.")
                        
                        analysis_prompt = f"""--- ANALYSIS TASK ---\n{analysis_task}\n\n--- FILE CONTENTS ---\n```\n{file_contents}\n```\n--- END FILE CONTENTS ---\n\nBased on your analysis, provide your response as a JSON object."""
                        
                        analysis_result_str = specialist.run(input=analysis_prompt)
                        analysis_result = extract_json(analysis_result_str)
                        
                        if analysis_result and "problem_statement" in analysis_result:
                            print(f"      ✅ ANALYSIS COMPLETE. New Problem Statement: \"{analysis_result['problem_statement']}\"")
                        else:
                            print("      ⚠️ Specialist agent failed to return a valid problem statement.")

                    except FileNotFoundError:
                        print(f"      ❌ File not found for analysis: {file_path_str}. Skipping task.")
                    except Exception as e:
                        print(f"      ❌ An error occurred during the analysis pipeline: {e}. Skipping task.")

                elif briefing['tool'] == 'execute_shell':
                    command = briefing.get('command')
                    if not command:
                        print(f"      ❌ Architect proposed an 'execute_shell' task but provided no command. Skipping task.")
                        continue
                    try:
                        print(f"      Tactician executing: `{command}`")
                        # --- V31.13 CHANGE: Removed check=True for resilience ---
                        result = subprocess.run(command, shell=True, cwd=orchestrator.workspace_root, capture_output=True, text=True)
                        if result.returncode != 0:
                             print(f"      ⚠️ Command finished with a non-zero exit code. STDERR: {result.stderr.strip()}")
                        if result.stdout:
                            print(f"      STDOUT: {result.stdout.strip()}")
                        print(f"      ✅ Task complete.")
                    except Exception as e:
                        print(f"      ❌ Execution crashed with an exception: {e}. Skipping task.")
                else:
                    print(f"      ⚠️ Unknown tool '{briefing['tool']}'. Skipping task.")
            
    print("\n--- Project Execution Concluded ---")

def run_bidding_system(problem_statement: str):
    """Initializes and runs the MISO V31.13 system."""
    print(f"🚀 MISO V31 Bidding System Initialized.") 
    print(f"    Problem Statement: {problem_statement}")

    try:
        with open('tool_kb.json', 'r') as f:
            tool_kb = json.load(f)
        print("    Loaded 'tool_kb.json' knowledge base.")
    except FileNotFoundError:
        print("❌ CRITICAL: 'tool_kb.json' not found. Halting.")
        return
    except json.JSONDecodeError:
        print("❌ CRITICAL: 'tool_kb.json' is corrupted. Halting.")
        return

    agent_names = ["SolutionsArchitectAgent", "ArchitectAgent", "ProgrammerAgent", "WriterAgent", "AuditorGeneralAgent"]
    agents = { name: Agent(persona_name=name, tool_kb=tool_kb) for name in agent_names }

    print("\n--- Generating Project Bid ---")
    bid_str = agents['SolutionsArchitectAgent'].run(input=problem_statement)
    bid = extract_json(bid_str)

    if not bid or "milestones" not in bid:
        print(f"\n❌ CRITICAL: Solutions Architect failed to generate a valid bid.\n    Halting.")
        return

    print("\n--- MISO PROJECT PROPOSAL ---")
    print(f"  Project Name: {bid.get('project_name', 'Untitled Project')}")
    for i, milestone in enumerate(bid['milestones'], 1):
        print(f"     {i}. {milestone.get('milestone_name', milestone if isinstance(milestone, str) else 'Unnamed Milestone')}")

    approval = input("\nApprove this project? (yes/no): ").lower().strip()

    if approval == 'yes':
        print("\n✅ Project Approved by Operator. Commencing execution.")
        execute_approved_project(bid, agents, agent_names)
    else:
        print("\n❌ Project Rejected by Operator. Halting.")

if __name__ == "__main__":
    print("🚀 MISO V31.13 Interactive Shell Initialized.")
    print("   Enter a problem statement for the MISO council or 'exit' to quit.")
    while True:
        problem = input("\n[Problem Statement]: ")
        if problem.lower() == 'exit':
            print("MISO shutting down.")
            break
        if not problem.strip():
            continue
        
        run_bidding_system(problem)
        print("\n🏁 MISO Task Concluded. Awaiting next problem.")
