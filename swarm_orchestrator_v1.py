# swarm_orchestrator_v1.py - Monolithic Orchestrator Proof-of-Concept

import sys
import os
import re # For simple parsing
from pathlib import Path
import json # For structured output/logging
import traceback # Added for better error reporting
import argparse # <-- ADDED for CLI arguments

# --- Add src to sys.path ---
# Assumes this script is run from the project root (e.g., ~/MISO-Phoenix)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# --- Import Worker Agents ---
try:
    from miso_swarm.worker_agents import (
        create_file_agent,
        write_component_signature_agent,
        render_jsx_element_agent,
        apply_css_classes_agent
    )
except ImportError as e:
    print(f"Error: Could not import worker agents. Make sure src/miso_swarm/worker_agents.py exists.")
    print(f"Details: {e}")
    sys.exit(1)
except Exception as e: # Catch potential syntax errors in worker_agents.py too
    print(f"Error: Could not import worker agents due to an unexpected error.")
    print(f"Details: {e}")
    traceback.print_exc() # Print full traceback for debugging
    sys.exit(1)


# --- Simple Input Parsing (Example) ---
def parse_simple_prompt(prompt: str) -> dict | None:
    """Very basic parsing for the PoC prompt."""
    details = {}
    # Example: "Create a React button component named 'Button' with props 'label' and 'onClick', styled with Tailwind classes 'bg-blue-500', 'text-white'."
    try:
        name_match = re.search(r"named '([^']+)'", prompt)
        props_match = re.search(r"props '([^']+)'", prompt)
        classes_match = re.search(r"classes '([^']+)'", prompt)
        element_match = re.search(r"(\w+) component", prompt) # e.g., "button component"

        if not name_match or not element_match:
            print("Error: Could not parse component name or type from prompt.")
            return None

        details["component_name"] = name_match.group(1)
        details["element_type"] = element_match.group(1).lower() # e.g., 'button'
        # Handle props parsing more robustly
        if props_match:
             # Split by "' and '" or just comma if only one prop
             props_list = props_match.group(1).split("' and '")
             # Further split by comma in case of single quotes with multiple items
             flat_props = []
             for item in props_list:
                 flat_props.extend([p.strip() for p in item.split(',')])
             details["props"] = [p for p in flat_props if p] # Remove empty strings
        else:
             details["props"] = []

        details["css_classes"] = classes_match.group(1).split("', '") if classes_match else []

        # Infer text content for simple elements like buttons
        if details["element_type"] == "button" and "label" in details["props"]:
            details["text_content"] = "{label}" # Use the prop variable

        return details
    except Exception as e:
        print(f"Error during prompt parsing: {e}")
        traceback.print_exc()
        return None


# --- Orchestrator Logic ---
def run_orchestrator_v1(prompt: str):
    """
    Executes the monolithic orchestration sequence for Phase 1 PoC.
    """
    print(f"🚀 Starting Orchestrator V1 for prompt: \"{prompt}\"")

    # 1. Parse Input
    parsed_details = parse_simple_prompt(prompt)
    if not parsed_details:
        print("❌ Orchestration failed: Could not parse prompt.")
        return

    component_name = parsed_details["component_name"]
    file_path_str = f"src/components/{component_name}.jsx" # Example path
    print(f"   📝 Parsed Details: {json.dumps(parsed_details, indent=2)}")

    # --- Worker Agent Execution Sequence ---
    code_parts = {} # To store intermediate results
    project_root = Path('.') # Define project root for consistency

    try:
        # 2. Call ComponentSignatureWriter
        print("\n   [Step 1/4] Generating component signature...")
        sig_task = {
            "component_name": component_name,
            "props": parsed_details.get("props", [])
        }
        sig_result = write_component_signature_agent(sig_task)
        if not sig_result.get("success"):
            print(f"❌ Orchestration failed at SignatureWriter: {sig_result.get('message')}")
            return
        code_parts["signature"] = sig_result["code_snippet"]
        print(f"   ✅ Signature generated.")

        # 3. Call JSXRenderer
        print("\n   [Step 2/4] Rendering base JSX element...")
        jsx_task = {
            "element_type": parsed_details.get("element_type", "div"),
            "text_content": parsed_details.get("text_content"),
            # Add placeholder if no text AND it's not a known self-closing tag
            "add_children_placeholder": not parsed_details.get("text_content") and parsed_details.get("element_type", "div").lower() not in {"img", "input", "br", "hr", "meta"}
        }
        jsx_result = render_jsx_element_agent(jsx_task)
        if not jsx_result.get("success"):
            print(f"❌ Orchestration failed at JSXRenderer: {jsx_result.get('message')}")
            return
        base_jsx = jsx_result["code_snippet"]
        print(f"   ✅ Base JSX rendered: {base_jsx}")

        # 4. Call CSSApplier
        print("\n   [Step 3/4] Applying CSS classes...")
        css_task = {
            "jsx_snippet": base_jsx,
            "css_classes": parsed_details.get("css_classes", [])
        }
        css_result = apply_css_classes_agent(css_task)
        if not css_result.get("success"):
            print(f"❌ Orchestration failed at CSSApplier: {css_result.get('message')}")
            return
        styled_jsx = css_result["code_snippet"]
        code_parts["body"] = styled_jsx # Store the final styled element
        print(f"   ✅ CSS applied: {styled_jsx}")

        # 5. Assemble Final Code
        print("\n   [Step 4/4] Assembling final code...")
        # Basic assembly: signature, return statement, body, closing braces
        # Assumes simple functional component structure
        signature_lines = code_parts["signature"].splitlines()
        function_signature = signature_lines[0] # "function Button({ label, onClick }) {"
        # Ensure proper indentation for the body
        body_indent = "    " # 4 spaces
        styled_jsx_indented = body_indent + styled_jsx
        closing_brace = "\n}"

        final_code = f"import React from 'react';\n\n{function_signature}\n  return (\n{styled_jsx_indented}\n  );\n{closing_brace}\n\nexport default {component_name};\n"
        print(f"   ✅ Code assembled:\n```jsx\n{final_code}\n```")

        # 6. Create/Write File
        print(f"\n   Writing final code to {file_path_str}...")
        # Using create_file_agent just to ensure directory exists
        write_task = {"file_path": file_path_str}
        create_result = create_file_agent(write_task)
        if not create_result.get("success"):
            print(f"❌ Orchestration failed during file directory creation: {create_result.get('message')}")
            return

        # Now write the content using pathlib
        target_path = project_root.resolve() / file_path_str
        target_path.write_text(final_code, encoding='utf-8')
        print(f"   ✅ Successfully wrote component to {target_path.relative_to(project_root.resolve())}")

    except Exception as e:
        print(f"❌ An unexpected error occurred during orchestration: {e}")
        traceback.print_exc()
        return # Stop execution on error

    print("\n🏁 Orchestrator V1 finished.")


# --- Run the PoC ---
if __name__ == "__main__":
    # --- ADDED: Argument Parsing ---
    parser = argparse.ArgumentParser(description="Miso Swarm Orchestrator V1 - PoC")
    parser.add_argument("prompt", type=str, help="The prompt describing the component to create.")
    args = parser.parse_args()
    # --- END ADDED ---

    # Ensure OPENAI_API_KEY is set if any agent uses an LLM
    # if not os.environ.get("OPENAI_API_KEY"):
    #     print("Warning: OPENAI_API_KEY environment variable not set. LLM agents may fail.")

    run_orchestrator_v1(args.prompt) # <-- MODIFIED: Use parsed prompt

    # Optional: Clean up can remain commented out or be removed
    # print("\n--- Cleaning up generated files ---")
    # try:
    #     cleanup_path = Path("src/components/Button.jsx") # Needs dynamic path based on prompt
    #     # ... cleanup logic ...
    # except Exception as e:
    #     print(f"   🧹 (Cleanup error: {e})")
    #     pass
