# src/miso_swarm/management/dispatcher.py

import sys
import os
import json
import traceback
from typing import List, Dict, Any

# --- Add src to sys.path ---
# Assumes this script might be run directly from root for testing
# Adjust if necessary based on your project structure and how you run tests
try:
    # Try adding project root if this file is in src/miso_swarm/management
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path:
         sys.path.insert(0, project_root) # May need root for certain imports/configs
except Exception:
    print("Warning: Could not automatically add project root to sys.path.")
    pass


# --- Import Worker Agents ---
# Need to dynamically import based on task['agent'] name
# For now, import explicitly for simplicity in PoC
try:
    from miso_swarm import worker_agents
except ImportError as e:
    print(f"Error: Could not import worker_agents module. Ensure 'src' is in sys.path.")
    print(f"Current sys.path: {sys.path}")
    print(f"Details: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error: Unexpected error importing worker_agents module.")
    print(f"Details: {e}")
    traceback.print_exc()
    sys.exit(1)


# --- Map Agent Names to Functions ---
# This allows calling the correct function dynamically
AGENT_FUNCTION_MAP = {
    "create_file_agent": worker_agents.create_file_agent,
    "write_component_signature_agent": worker_agents.write_component_signature_agent,
    "render_jsx_element_agent": worker_agents.render_jsx_element_agent,
    "apply_css_classes_agent": worker_agents.apply_css_classes_agent,
    # Add other worker agents here as they are created
}

class TaskDispatcher:
    def __init__(self):
        self.task_queue: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        # In a more complex system, this would manage worker availability, etc.
        pass

    def load_plan(self, plan: List[Dict[str, Any]]):
        """Loads a plan (list of tasks) into the dispatcher's queue."""
        if not isinstance(plan, list):
            print("Error: Plan must be a list of task dictionaries.")
            self.task_queue = []
            return
        self.task_queue = plan[:] # Copy the plan
        self.results = []
        print(f"📬 Dispatcher: Plan loaded with {len(self.task_queue)} tasks.")

    def run_sequential(self):
        """Executes tasks sequentially from the queue."""
        print("🚀 Dispatcher: Starting sequential task execution...")
        if not self.task_queue:
            print("   ⚠️ Dispatcher: No tasks in the queue.")
            return self.results

        # Simple state for passing results between steps (e.g., jsx_snippet for CSSApplier)
        # This simulates what the Result Aggregator will handle more robustly
        intermediate_state = {}

        for i, task in enumerate(self.task_queue):
            agent_name = task.get("agent")
            task_details = task.get("task_details", {})
            print(f"\n   [Task {i+1}/{len(self.task_queue)}] Executing '{agent_name}'...")

            if agent_name not in AGENT_FUNCTION_MAP:
                print(f"   ❌ Error: Unknown agent '{agent_name}'. Skipping task.")
                result = {"success": False, "message": f"Unknown agent: {agent_name}"}
                self.results.append(result)
                continue # Skip to next task

            # --- Dynamic Placeholder Filling (Simple version for Phase 2 PoC) ---
            # If CSSApplier needs jsx_snippet, try to get it from previous result
            if agent_name == "apply_css_classes_agent" and task_details.get("jsx_snippet") == "PLACEHOLDER":
                if intermediate_state.get("last_jsx_snippet"):
                    task_details["jsx_snippet"] = intermediate_state["last_jsx_snippet"]
                    print(f"      Injecting jsx_snippet from previous step.")
                else:
                    print(f"   ❌ Error: CSSApplier requires 'jsx_snippet', but none found in intermediate state.")
                    result = {"success": False, "message": "Missing required jsx_snippet for CSSApplier."}
                    self.results.append(result)
                    continue
            # --- End Placeholder Filling ---

            try:
                worker_function = AGENT_FUNCTION_MAP[agent_name]
                print(f"      Input Details: {json.dumps(task_details, indent=2)}")
                result = worker_function(task_details)
                print(f"      Result: {json.dumps(result, indent=2)}")
                self.results.append(result)

                # Update intermediate state (simple version)
                if result.get("success"):
                    # Capture the output of JSX rendering
                    if "code_snippet" in result and agent_name == "render_jsx_element_agent":
                        intermediate_state["last_jsx_snippet"] = result["code_snippet"]
                    # Update with the output after CSS is applied
                    if "code_snippet" in result and agent_name == "apply_css_classes_agent":
                         intermediate_state["last_jsx_snippet"] = result["code_snippet"] # Update after CSS applied

                if not result.get("success"):
                    print(f"   ❌ Task '{agent_name}' failed. Stopping execution.")
                    # In Phase 2, this might trigger re-queueing via Result Aggregator
                    break # Stop sequence on failure for now

            except Exception as e:
                print(f"   ❌ CRITICAL Error during task execution: {e}")
                error_details = traceback.format_exc()
                print(error_details)
                result = {"success": False, "message": f"Dispatcher execution error: {e}"}
                self.results.append(result)
                break # Stop sequence on critical error

        print("\n🏁 Dispatcher: Task execution finished.")
        return self.results

# --- Example Usage ---
if __name__ == "__main__":
    # Example plan (similar to what Strategist would output)
    example_plan = [
        {"agent": "write_component_signature_agent", "task_details": {"component_name": "InfoCard", "props": ["title", "children"]}},
        {"agent": "render_jsx_element_agent", "task_details": {"element_type": "div", "add_children_placeholder": True}},
        {"agent": "apply_css_classes_agent", "task_details": {"jsx_snippet": "PLACEHOLDER", "css_classes": ["p-4", "border", "rounded-lg"]}}
    ]

    dispatcher = TaskDispatcher()
    dispatcher.load_plan(example_plan)
    final_results = dispatcher.run_sequential()

    print("\n--- Final Results ---")
    print(json.dumps(final_results, indent=2))

    # Next step would be passing these results to the Result Aggregator
