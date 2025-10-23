# src/miso_swarm/management/strategist.py

import json
import os
import traceback # Added for error reporting
from typing import List, Dict, Any

# Placeholder for LLM setup (replace with your actual LLM client)
# Make sure OPENAI_API_KEY is set in your environment if using OpenAI
# from langchain_openai import ChatOpenAI
# llm = ChatOpenAI(model="gpt-4o", temperature=0.0)

# Define known worker agents and their expected inputs (for prompting the LLM)
KNOWN_WORKER_AGENTS = """
- create_file_agent: Creates a file. Requires: {"file_path": "path/to/file.ext"}
- write_component_signature_agent: Writes React component signature. Requires: {"component_name": "CompName", "props": ["prop1", "prop2"]}
- render_jsx_element_agent: Renders basic JSX. Requires: {"element_type": "div", "text_content": "Hello", "add_children_placeholder": false}
- apply_css_classes_agent: Adds CSS classes to JSX. Requires: {"jsx_snippet": "<tag>...</tag>", "css_classes": ["class1", "class2"]}
"""

class StrategistAgent:
    def __init__(self):
        # Initialize LLM client here if needed
        # Ensure API key is available via environment variable
        # if not os.environ.get("OPENAI_API_KEY"):
        #     print("Warning: OPENAI_API_KEY not set. Strategist LLM calls may fail.")
        # self.llm = ChatOpenAI(...)
        pass

    def generate_plan(self, user_prompt: str) -> List[Dict[str, Any]] | None:
        """
        Analyzes the user prompt and generates a high-level plan (list of tasks).
        """
        print(f"🧠 Strategist received prompt: \"{user_prompt}\"")
        print("   Generating high-level plan...")

        # --- LLM Integration ---
        prompt_template = f"""
You are an expert software development planner. Your goal is to break down a user request into a sequence of atomic tasks that can be executed by specialized worker agents.

User Request: "{user_prompt}"

Available Worker Agents and their required inputs:
{KNOWN_WORKER_AGENTS}

Based on the user request, generate a JSON list of tasks to be executed in sequence. Each task object in the list must contain:
1.  "agent": The name of the worker agent function to call (e.g., "write_component_signature_agent").
2.  "task_details": A dictionary containing the exact inputs required by that agent, derived from the user request.

Example for "Create a simple div component named 'Box'":
[
  {{"agent": "write_component_signature_agent", "task_details": {{"component_name": "Box", "props": []}}}},
  {{"agent": "render_jsx_element_agent", "task_details": {{"element_type": "div", "add_children_placeholder": true}}}},
  {{"agent": "apply_css_classes_agent", "task_details": {{"jsx_snippet": "PLACEHOLDER", "css_classes": []}}}}
]
Note: For 'apply_css_classes_agent', use "PLACEHOLDER" for 'jsx_snippet'. The orchestrator will fill this dynamically.

Respond ONLY with the valid JSON list of tasks. Ensure the JSON is well-formed.
"""
        plan_json_str = None
        try:
            # Replace with actual LLM call
            # response = self.llm.invoke(prompt_template)
            # plan_json_str = response.content # Adapt based on your LLM client library

            # --- Placeholder for now ---
            print("   (LLM Call Placeholder - Using hardcoded plan for PoC)")
            # Crude check for button example
            if "button component named 'Button'" in user_prompt:
                 plan_json_str = json.dumps([
                     {"agent": "write_component_signature_agent", "task_details": {"component_name": "Button", "props": ["label", "onClick"]}},
                     {"agent": "render_jsx_element_agent", "task_details": {"element_type": "button", "text_content": "{label}"}},
                     {"agent": "apply_css_classes_agent", "task_details": {"jsx_snippet": "PLACEHOLDER", "css_classes": ["bg-blue-500", "text-white"]}}
                 ])
            elif "card component named 'InfoCard'" in user_prompt: # Added case from user test
                 plan_json_str = json.dumps([
                     {"agent": "write_component_signature_agent", "task_details": {"component_name": "InfoCard", "props": ["title", "children"]}},
                     {"agent": "render_jsx_element_agent", "task_details": {"element_type": "div", "add_children_placeholder": True}}, # Card -> div
                     {"agent": "apply_css_classes_agent", "task_details": {"jsx_snippet": "PLACEHOLDER", "css_classes": ["p-4", "border", "rounded-lg"]}}
                 ])
            else:
                 print("   Warning: Prompt not recognized by placeholder logic. Returning empty plan.")
                 plan_json_str = "[]" # Default empty plan
            # --- End Placeholder ---

            # Attempt to parse the JSON plan
            plan = json.loads(plan_json_str)
            print(f"   ✅ Plan generated: {json.dumps(plan, indent=2)}")
            return plan

        except json.JSONDecodeError:
            print(f"❌ Strategist Error: Failed to parse LLM response into JSON.\nRaw response: {plan_json_str}")
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"❌ Strategist Error: An unexpected error occurred during plan generation: {e}")
            traceback.print_exc()
            return None

# --- Example Usage ---
if __name__ == "__main__":
    strategist = StrategistAgent()
    # test_prompt = "Create a React button component named 'Button' with props 'label' and 'onClick', styled with Tailwind classes 'bg-blue-500', 'text-white'."
    test_prompt_card = "Create a React card component named 'InfoCard' with props 'title' and 'children', styled with Tailwind classes 'p-4', 'border', 'rounded-lg'."
    generated_plan = strategist.generate_plan(test_prompt_card)

    if generated_plan:
        print("\n--- Generated Plan ---")
        # In a real system, this plan would be passed to the Task Dispatcher
    else:
        print("\n--- Failed to generate plan ---")

