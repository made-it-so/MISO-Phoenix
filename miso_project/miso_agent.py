import os
import sys
import json
import argparse
from typing import Dict, Any, List

# Add project root to path to allow absolute imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from brains import architect
from utils import git_tools

def load_persona(persona_name: str, personas_dir: str) -> Dict[str, Any]:
    '''Loads a persona JSON file.'''
    # Construct absolute path to persona file
    persona_file = os.path.join(personas_dir, f"{persona_name}.json")
    
    if not os.path.exists(persona_file):
        print(f"FATAL: Persona file not found: {persona_file}")
        sys.exit(1)
        
    try:
        with open(persona_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"FATAL: Could not load or parse persona file {persona_file}: {e}")
        sys.exit(1)

def run_mission(
    repo: 'git.Repo',
    workspace_dir: str,
    tdd_harness: Dict[str, str],
    escalation_chain: List[Dict[str, Any]]
) -> bool:
    '''
    Runs a complete TDD/fix/commit mission, iterating through the
    provided escalation chain.
    '''
    
    if not escalation_chain:
        print("CRITICAL FAILURE: No escalation chain provided.")
        return False

    current_persona = escalation_chain[0]
    chain_index = 0
    
    for i in range(10): # Max 10 total attempts
        print(f"\n--- Mission Cycle {i+1} (Brain: {current_persona['name']}) ---")
        
        # 1. Run TDD
        tdd_status, tdd_output, failed_stage = architect.check_tdd_harness(tdd_harness)
        
        if tdd_status == "PASS":
            print("MISSION SUCCESS: All TDD checks passed.")
            # Commit the successful changes
            git_tools.commit_changes(repo, workspace_dir, current_persona['name'])
            return True # Final success

        print(f"TDD FAILED at stage: {failed_stage}. Generating fix...")
        
        # 2. Generate Fix
        fix_list = architect.generate_fix(workspace_dir, tdd_output, current_persona)
        
        if not fix_list:
            # This is the escalation signal
            print(f"Brain ({current_persona['name']}) returned empty list. Escalating...")
            
            chain_index += 1
            if chain_index >= len(escalation_chain):
                # Already at max escalation, this is a hard failure
                print("CRITICAL FAILURE: Final brain in chain failed to provide a fix.")
                return False
            
            # Escalate to the next persona in the chain
            current_persona = escalation_chain[chain_index]
            print(f"Escalating to {current_persona['name']}...")
            continue # Restart loop with new persona

        # 3. Apply Fix
        architect.apply_fix_to_workspace(workspace_dir, fix_list)
        
        # 4. Commit this attempt
        print("Committing this attempt before re-running TDD...")
        git_tools.commit_changes(repo, workspace_dir, current_persona['name'])
        
        # Loop repeats to re-run TDD
    
    print("MISSION FAILED: Max attempts reached.")
    return False

def main():
    '''
    Main entry point for the MISO agent.
    This now acts as the "Triage Agent".
    '''
    parser = argparse.ArgumentParser(description="MISO Agent (Triage)")
    parser.add_argument(
        '--git-root',
        required=True,
        help="Absolute path to the Git repository root (e.g., MISO-Phoenix/)"
    )
    parser.add_argument(
        '--workspace',
        required=True,
        help="Absolute path to the workspace directory (e.g., .../miso_project/workspace)"
    )
    args = parser.parse_args()
    
    # --- Pass Git Root to LLM Client ---
    os.environ['GIT_ROOT'] = args.git_root

    # --- Path and Environment Setup ---
    personas_dir = os.path.join(PROJECT_ROOT, "personas")

    print("--- MISO Triage Agent Initializing ---")
    print(f"Git Root: {args.git_root}")
    print(f"Workspace: {args.workspace}")

    # --- Load ALL Personas for this test ---
    try:
        lizard_persona = load_persona("lizard_persona", personas_dir)
        human_persona = load_persona("human_persona", personas_dir)
        # We don't load Mammal or Primate, forcing a clean A/B test
    except SystemExit:
        return # Error already printed

    # --- Initialize Git ---
    try:
        import git
    except ImportError:
        print("FATAL: 'gitpython' library not found. Please run 'pip3 install gitpython'")
        sys.exit(1)
        
    repo = git_tools.get_repo(args.git_root)
    
    # --- Define TDD Harness ---
    tdd_harness = {
        "mypy": f"mypy --strict --ignore-missing-imports {args.workspace}",
        "pytest": f"pytest -v --tb=long {args.workspace}"
    }
    print(f"TDD Harness Set:\n  - mypy: {tdd_harness['mypy']}\n  - pytest: {tdd_harness['pytest']}")

    # --- GAUNTLET LEVEL 4: TRIAGE LOGIC ---
    print("Triage: Running initial TDD to determine escalation path...")
    tdd_status, tdd_output, failed_stage = architect.check_tdd_harness(tdd_harness)

    escalation_chain = []
    if tdd_status == "PASS":
        print("Triage: No errors found. Mission is already a success.")
        sys.exit(0)
    
    if failed_stage == "mypy":
        print("Triage: Detected 'mypy' failure. This is a Tier 2 task.")
        
        # This is the core "Cost vs. Quality" logic
        available_brains = [lizard_persona, human_persona]
        # Sort brains by cost, cheapest first
        available_brains.sort(key=lambda b: b.get("cost_per_run", 99.0))
        
        cheapest_brain = available_brains[0]
        print(f"Triage: Analyzing costs... [Lizard (Cost: {lizard_persona['cost_per_run']}), Human (Cost: {human_persona['cost_per_run']})]")
        print(f"Triage: Routing to cheapest viable brain: {cheapest_brain['name']}")
        
        # CRITICAL FIX: The escalation chain MUST include the fallback
        escalation_chain = [lizard_persona, human_persona]
        git_tools.create_branch(repo, cheapest_brain['name'])
    
    elif failed_stage == "pytest":
        print(f"Triage: Detected 'pytest' failure. Routing to Human (only available option).")
        escalation_chain = [human_persona]
        git_tools.create_branch(repo, human_persona['name'])
    
    else:
        print(f"Triage: Unknown failure stage '{failed_stage}'. Aborting.")
        sys.exit(1)

    # --- RUN MISSION ---
    success = run_mission(
        repo,
        args.workspace,
        tdd_harness,
        escalation_chain
    )

    # --- Cleanup ---
    print("Mission complete. Checking out main branch...")
    repo.git.checkout('main') # Or 'master', depending on your repo

    if not success:
        print("CRITICAL FAILURE: Final Mission Status: FAILED")
        sys.exit(1)
    else:
        print("MISSION SUCCESS: Final Mission Status: SUCCESS")
        sys.exit(0)

if __name__ == "__main__":
    main()
