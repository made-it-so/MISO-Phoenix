from llm.client import call_gemini_pro_programmer, HUMAN_PERSONA
import json

def run_human_brain(isolated_error: str, file_context: dict, failure_history: list) -> list:
    print("--- TIER 4/5 (Human 👨‍🔬) ACTIVATED ---")
    
    prompt_context = {
        "description": "All lower-tier brains (Lizard, Mammal, Primate) have failed. You are the final escalation. Analyze the failure pattern and provide a strategic JSON plan.",
        "test_command": "mypy workspace/",
        "isolated_error": isolated_error,
        "filesystem_context": file_context,
        "failed_plan_history": failure_history
    }
    
    prompt = f"""
    Here is the complete failure context.
    {json.dumps(prompt_context, indent=2)}
    
    Provide a strategic JSON plan to resolve this complex failure.
    """
    
    plan = call_gemini_pro_programmer(prompt, HUMAN_PERSONA)
    
    if not plan:
        print("👨‍🔬 Human: Brain generated an empty plan. This is a hard failure.")
        return []
        
    print("👨‍🔬 Human: Brain generated a strategic plan. Submitting for verification.")
    return plan
