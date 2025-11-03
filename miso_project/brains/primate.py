from llm.client import call_gemini_pro_programmer, PRIMATE_PERSONA
import json
def run_primate_brain(isolated_error: str, file_context: dict) -> list:
    print("--- TIER 3 (Primate 🐒) ACTIVATED ---")
    prompt_context = {
        "description": "The current TDD failure state. Please generate an atomic JSON plan to fix it.",
        "test_command": "mypy workspace/ + pytest workspace/",
        "error_output": isolated_error,
        "filesystem_context": file_context
    }
    prompt = f"TDD Context:\n{json.dumps(prompt_context, indent=2)}\n\nGenerate the JSON plan."
    plan = call_gemini_pro_programmer(prompt, PRIMATE_PERSONA)
    if not plan:
        print("🐒 Primate: Brain generated an empty plan. Escalating.")
        return []
    print("🐒 Primate: Brain generated a new plan. Submitting for verification.")
    return plan
