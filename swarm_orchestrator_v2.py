# swarm_orchestrator_v2.py - Deconstructed Orchestrator (Phase 2 PoC)

import sys
import os
import argparse
import json
import traceback
from pathlib import Path
from typing import List, Dict, Any # Added typing imports

# --- Add src to sys.path ---
# Assumes this script is run from the project root (e.g., ~/MISO-Phoenix)
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path:
         sys.path.insert(0, project_root)
except Exception:
    print("Warning: Could not automatically add project root to sys.path.")
    pass

# --- Import Management Agents ---
try:
    from miso_swarm.management.strategist import StrategistAgent
    from miso_swarm.management.dispatcher import TaskDispatcher
    from miso_swarm.management.aggregator import ResultAggregator
except ImportError as e:
    print(f"Error: Could not import management agents.")
    print(f"Ensure src/miso_swarm/management/ contains __init__.py (even if empty) and the agent files.")
    print(f"Details: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error: Unexpected error importing management agents.")
    print(f"Details: {e}")
    traceback.print_exc()
    sys.exit(1)


# --- Orchestrator V2 Logic ---
def run_orchestrator_v2(prompt: str):
    """
    Runs the deconstructed orchestrator sequence (Phase 2 PoC).
    """
    print(f"🚀 Starting Orchestrator V2 for prompt: \"{prompt}\"")

    # 1. Instantiate Management Agents
    try:
        strategist = StrategistAgent()
        dispatcher = TaskDispatcher()
        aggregator = ResultAggregator()
        print("   ✅ Management agents initialized.")
    except Exception as e:
        print(f"❌ Error initializing management agents: {e}")
        traceback.print_exc()
        return

    component_name = None # Will try to extract later

    try:
        # 2. Call Strategist to generate the plan
        plan: List[Dict[str, Any]] | None = strategist.generate_plan(prompt) # Add type hint
        if not plan:
            print("❌ Orchestration failed: Strategist did not generate a plan.")
            return

        # Try to extract component name from the first relevant task
        # (This is basic; a better approach would have Strategist return it explicitly)
        for task in plan:
            if task.get("agent") == "write_component_signature_agent":
                component_name = task.get("task_details", {}).get("component_name")
                break
        if not component_name:
             print("   ⚠️ Warning: Could not determine component name from plan. Using 'MyComponent'.")
             component_name = "MyComponent"


        # 3. Call Task Dispatcher to execute the plan
        dispatcher.load_plan(plan)
        results: List[Dict[str, Any]] = dispatcher.run_sequential() # Add type hint

        # Check if dispatcher encountered critical errors or task failures
        if not results or any(not r.get("success") for r in results):
             print("❌ Orchestration failed: Task Dispatcher reported errors.")
             # Optionally print results for debugging
             # print("\n--- Dispatcher Results ---")
             # print(json.dumps(results, indent=2))
             return


        # 4. Call Result Aggregator to assemble the final code
        file_path_str = f"src/components/{component_name}.jsx" # Determine file path
        assembly_result: Dict[str, Any] = aggregator.assemble_component( # Add type hint
            task_results=results,
            component_name=component_name,
            file_path_str=file_path_str # Pass file path for writing
        )

        if not assembly_result.get("success"):
            # Even if assembly failed (e.g., lint error), print the code if generated
            if assembly_result.get("final_code"):
                print("\n--- Partially Assembled Code (before failure) ---")
                print(assembly_result.get("final_code"))
            print(f"❌ Orchestration failed: Result Aggregator reported failure.")
            print(f"   Reason: {assembly_result.get('message')}")
            if assembly_result.get("lint_errors"):
                 print("   Lint Errors:")
                 print(json.dumps(assembly_result.get("lint_errors"), indent=2))
            return

        # 5. Output Final Result (only if assembly AND linting succeeded)
        print("\n--- Final Assembled Code ---")
        print(assembly_result.get("final_code"))
        if "message" in assembly_result and assembly_result.get("success"): # Print warnings only on overall success
             print(f"\n   ⚠️ {assembly_result['message']}")


    except Exception as e:
        print(f"❌ An unexpected error occurred during orchestration: {e}")
        traceback.print_exc()
        return

    print("\n🏁 Orchestrator V2 finished.")


# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Miso Swarm Orchestrator V2 - PoC")
    parser.add_argument("prompt", type=str, help="The prompt describing the component to create.")
    args = parser.parse_args()

    # Ensure OPENAI_API_KEY is set if any agent uses an LLM
    # if not os.environ.get("OPENAI_API_KEY"):
    #     print("Warning: OPENAI_API_KEY environment variable not set. LLM agents may fail.")

    run_orchestrator_v2(args.prompt)

    # Optional: Clean up generated file/dirs after run
    # (Requires dynamic component name extraction to work reliably)
    # print("\n--- Cleaning up generated files ---")
    # extracted_name = "MyComponent" # Default or extract from args.prompt if possible
    # name_match = re.search(r"named '([^']+)'", args.prompt)
    # if name_match: extracted_name = name_match.group(1)
    # try:
    #     cleanup_path = Path(f"src/components/{extracted_name}.jsx")
    #     cleanup_path.unlink(missing_ok=True)
    #     print(f"   🧹 Deleted {cleanup_path}")
    #     # Attempt to remove parent directories if they exist and are empty
    #     try: cleanup_path.parent.rmdir()
    #     except OSError: pass # Ignore if not empty/doesn't exist
    #     except FileNotFoundError: pass
    #     print(f"   🧹 Attempted removal of {cleanup_path.parent}")
    #     try: cleanup_path.parent.parent.rmdir() # Try removing 'src'
    #     except OSError: pass
    #     except FileNotFoundError: pass
    #     print(f"   🧹 Attempted removal of {cleanup_path.parent.parent}")
    # except Exception as e_clean: print(f"Cleanup warning: {e_clean}")

