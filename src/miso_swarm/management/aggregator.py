# src/miso_swarm/management/aggregator.py

import sys
import os
import re # Needed for Attempt 3
import json
import traceback
from typing import List, Dict, Any
from pathlib import Path

# --- Add src to sys.path ---
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    src_path = os.path.join(project_root, 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    if project_root not in sys.path:
         sys.path.insert(0, project_root)
except Exception:
    print("Warning: Could not automatically add project root to sys.path.")
    pass

# Import worker agent(s)
try:
    from miso_swarm import worker_agents
except ImportError as e:
    print(f"Error: Could not import worker_agents module. {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"Error: Unexpected error importing worker_agents module.")
    print(f"Details: {e}")
    traceback.print_exc()
    sys.exit(1)


class ResultAggregator:
    def __init__(self):
        # In later phases, this would manage QA agents, self-correction logic, etc.
        pass

    def assemble_component(self, task_results: List[Dict[str, Any]], component_name: str, file_path_str: str | None = None) -> Dict[str, Any]:
        """
        Assembles a React component from sequential task results, lints it,
        and optionally writes to a file.

        Args:
            task_results: List of result dictionaries from the TaskDispatcher.
            component_name: The name of the component (for export default).
            file_path_str: Optional path to write the final file.

        Returns:
            Dict containing 'success' (bool, overall success), 'final_code' (str, if assembled),
            'lint_passed' (bool | None), 'lint_errors' (list | None), and/or 'message' (str).
        """
        print(f"🧩 Aggregator: Assembling component '{component_name}' from {len(task_results)} results...")
        code_parts = {"signature_snippet": None, "body": None} # Renamed for clarity
        assembly_success = True
        assembly_message = "Assembly successful."
        final_code = None
        lint_passed = None
        lint_errors = None

        # --- Stage 1: Extract parts from results ---
        for i, result in enumerate(task_results):
            if not result.get("success"):
                assembly_message = f"Assembly failed due to error in task {i+1}: {result.get('message')}"
                print(f"   ❌ Error: Task {i+1} failed. Cannot assemble.")
                return {"success": False, "message": assembly_message}

            if "code_snippet" in result:
                snippet = result["code_snippet"].strip()
                # Find signature snippet
                if snippet.startswith("function") and not code_parts["signature_snippet"]:
                    code_parts["signature_snippet"] = result["code_snippet"] # Keep original spacing
                    print(f"      Found signature snippet in result {i+1}.")
                # Find body (last snippet that looks like JSX)
                elif "<" in snippet and not snippet.startswith("function"):
                    code_parts["body"] = result["code_snippet"] # Keep original spacing
                    print(f"      Found potential body JSX in result {i+1}. Overwriting previous if any.")

        # --- Stage 2: Validate and Assemble Code ---
        if not code_parts["signature_snippet"]:
            return {"success": False, "message": "Assembly failed: Component signature snippet not found."}
        if not code_parts["body"]:
            return {"success": False, "message": "Assembly failed: Component body (JSX) not found."}

        # --- CORRECTED BLOCK WITH INDENTATION (Attempt 3) ---
        try:
            print("   Assembling final code...") # This line must be indented under try:

            # Extract props from the *signature task result* for robustness
            signature_task_result = next((r for r in task_results if r.get("code_snippet", "").strip().startswith("function")), None)
            if not signature_task_result:
                 # This check is now redundant due to Stage 2 validation but kept for safety
                 return {"success": False, "message": "Assembly failed: Component signature result not found (internal error)."}

            # Attempt to find the props string within the signature snippet (e.g., "{ title, children }")
            # This regex looks for content between the first '(' and the last ')' before '{'
            props_match = re.search(r'function[^(]*\((.*?)\)\s*\{', code_parts["signature_snippet"], re.DOTALL)
            if not props_match:
                 # Fallback if regex fails - maybe no props? Assume empty props.
                 print("   Warning: Could not reliably parse props from signature snippet. Assuming no props.")
                 props_str = ""
            else:
                 # Extract the content between parentheses
                 props_str = props_match.group(1).strip()


            # Reconstruct the signature line cleanly using component_name and extracted/assumed props_str
            function_signature = f"function {component_name}({props_str}) {{"


            body_indent = "    " # 4 spaces
            # Ensure body snippet itself doesn't have extra leading whitespace
            body_cleaned = code_parts["body"].strip()
            body_indented = body_indent + body_cleaned
            closing_brace = "\n}" # Assumes function signature ends with '{'

            # Add import statement
            final_code = f"import React from 'react';\n\n{function_signature}\n  return (\n{body_indented}\n  );\n{closing_brace}\n\nexport default {component_name};\n"
            print("   ✅ Code assembled successfully.")

        except Exception as e:
            assembly_message = f"Assembly error: {e}"
            print(f"❌ Error during final code assembly: {e}")
            traceback.print_exc()
            return {"success": False, "message": assembly_message}
        # --- END CORRECTED BLOCK ---

        # --- Stage 3: Linting ---
        print("\n   Linting assembled code...")
        lint_language = "jsx" # Assume JSX for now, could be dynamic later
        lint_task = {"code_snippet": final_code, "language": lint_language}
        try:
            lint_result = worker_agents.lint_code_agent(lint_task)
            if lint_result.get("success"):
                lint_passed = lint_result.get("passed")
                lint_errors = lint_result.get("errors", [])
                if lint_passed:
                    print(f"   ✅ Linting passed.")
                    assembly_message += " Linting passed."
                else:
                    print(f"   ❌ Linting failed with {len(lint_errors)} error(s).")
                    assembly_success = False # Overall success is false if lint fails
                    assembly_message = "Assembly successful, but linting failed."
            else:
                print(f"   ⚠️ Linter agent failed to run: {lint_result.get('message')}")
                assembly_message += f" Warning: Linter agent failed: {lint_result.get('message')}"
                # Treat linter failure as non-blocking for now, but flag it

        except Exception as e_lint:
            lint_message = f"Error calling linter agent: {e_lint}"
            print(f"   ❌ {lint_message}")
            traceback.print_exc()
            assembly_message += f" Warning: {lint_message}"
            # Treat linter failure as non-blocking

        # --- Stage 4: Write File (Optional) ---
        file_write_message = ""
        if file_path_str:
            print(f"   Writing file to {file_path_str}...")
            create_task = {"file_path": file_path_str}
            create_result = worker_agents.create_file_agent(create_task)
            if not create_result.get("success"):
                 file_write_message = f"Warning: Code {('assembled' if assembly_success else 'assembled with lint errors')} but failed to ensure file path: {create_result.get('message')}"
                 print(f"   ❌ {file_write_message}")
            else:
                try:
                    target_path = Path(file_path_str)
                    target_path.write_text(final_code, encoding='utf-8')
                    file_write_message = f"File written successfully."
                    print(f"   ✅ {file_write_message}")
                except Exception as e_write:
                    file_write_message = f"Warning: Code {('assembled' if assembly_success else 'assembled with lint errors')} but failed write to file: {e_write}"
                    print(f"   ❌ {file_write_message}")

        # Combine messages
        final_message = f"{assembly_message} {file_write_message}".strip()

        return {
            "success": assembly_success and lint_passed is True, # Overall success requires lint pass
            "final_code": final_code,
            "lint_passed": lint_passed,
            "lint_errors": lint_errors if lint_passed == False else None,
            "message": final_message
        }


# --- Example Usage ---
if __name__ == "__main__":
    # Example results (like those from dispatcher.py)
    example_results_good = [
      {"success": True, "code_snippet": "function InfoCard({ title, children }) {\n  // TODO: Implement component\n}"},
      {"success": True, "code_snippet": "<div>{/* children */}</div>"},
      {"success": True, "code_snippet": "<div className=\"p-4 border rounded-lg\">{/* children */}</div>"}
    ]
    # Example results that might lead to lint errors
    example_results_bad = [
      {"success": True, "code_snippet": "function BadCard({ title }) {\n var unused = 1; // Unused var error \n}"}, # Simplified signature part
      {"success": True, "code_snippet": '<div className="p-4>{title}</div>'} # Used children without React import potentially
    ]

    example_component_name = "InfoCard"
    example_file_path = f"src/components/{example_component_name}.jsx" # Example path

    aggregator = ResultAggregator()

    print("\n--- Testing Assembly (Good Code) ---")
    assembly_result_good = aggregator.assemble_component(
        task_results=example_results_good,
        component_name=example_component_name,
        file_path_str=example_file_path
    )
    print("\n--- Good Assembly Result ---")
    # Avoid printing full code in summary json
    summary_good = assembly_result_good.copy()
    summary_good.pop("final_code", None)
    print(json.dumps(summary_good, indent=2))
    if assembly_result_good.get("success"):
        print("\n--- Good Assembled Code ---")
        print(assembly_result_good.get("final_code"))

    # Optional: Clean up test file
    print("\n--- Cleaning up generated file ---")
    try:
        cleanup_path = Path(example_file_path)
        cleanup_path.unlink(missing_ok=True)
        print(f"   🧹 Deleted {cleanup_path}")
        # Attempt to remove parent directories if they exist and are empty
        try: cleanup_path.parent.rmdir()
        except OSError: pass # Ignore if not empty/doesn't exist
        except FileNotFoundError: pass
        print(f"   🧹 Attempted removal of {cleanup_path.parent}")
        try: cleanup_path.parent.parent.rmdir() # Try removing 'src'
        except OSError: pass
        except FileNotFoundError: pass
        print(f"   🧹 Attempted removal of {cleanup_path.parent.parent}")
    except Exception as e_clean: print(f"Cleanup warning: {e_clean}")


    print("\n\n--- Testing Assembly (Potentially Bad Code) ---")
    # Constructing a minimal bad code snippet for testing linter
    bad_code_for_lint = """
import React from 'react';

function BadCard({ title }) { // Missing children prop if used
  var unusedVar = 1; // Linter error
  return (
    <div className="p-4>{/* Missing quote */}
      {title}
    </div> // Mismatched tags potentially
  );
}
// Missing export default
"""
    # Simulate results leading to bad code (overwriting good results for test)
    example_results_bad_simulated = [
        {"success": True, "code_snippet": "function BadCard({ title }) {\n var unusedVar = 1;\n}"},
        {"success": True, "code_snippet": '<div className="p-4>{title}</div>'}
    ]
    assembly_result_bad = aggregator.assemble_component(
        task_results=example_results_bad_simulated, # Using simulated results
        component_name="BadCard", # Different name for clarity
        file_path_str=None # Don't write bad file
    )
    print("\n--- Bad Assembly Result ---")
    # Avoid printing full code in summary json
    summary_bad = assembly_result_bad.copy()
    summary_bad.pop("final_code", None)
    print(json.dumps(summary_bad, indent=2))
    if not assembly_result_bad.get("success") and assembly_result_bad.get("lint_passed") == False:
        print("\n--- Lint Errors (Expected) ---")
        print(json.dumps(assembly_result_bad.get("lint_errors"), indent=2))
    elif assembly_result_bad.get("final_code"): # Print code if assembled but failed lint
        print("\n--- Bad Assembled Code (Generated before Lint Failure) ---")
        print(assembly_result_bad.get("final_code"))

