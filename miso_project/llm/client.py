import json
import os

print("--- LLM CLIENT (PATCHED V10 - FINAL) ---") # <-- CANARY

# This is a placeholder for your real LLM client.
# from ollama import Client 
# LLM_CLIENT = Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))

# --- Load the Personas ---
try:
    with open('personas/primate_persona.json', 'r') as f:
        PRIMATE_PERSONA = json.load(f)
    with open('personas/human_persona.json', 'r') as f:
        HUMAN_PERSONA = json.load(f)
except FileNotFoundError:
    print("WARNING: Personas not found. Using stub personas.")
    PRIMATE_PERSONA = {"role": "Primate", "principles": [], "output_schema": {}}
    HUMAN_PERSONA = {"role": "Human", "principles": [], "output_schema": {}}


def call_gemini_pro_programmer(prompt: str, persona: dict) -> dict:
    """
    Calls the "ProgrammerAgent-Pro" LLM (e.g., gemini-pro).
    
    *** THIS IS A SIMULATOR ***
    """
    
    messages = [
        {
            "role": "system",
            "content": f"""
            You are a '{persona['role']}'.
            Your principles are: {json.dumps(persona['principles'])}
            Your output MUST be a JSON array matching this schema:
            {json.dumps(persona['output_schema'])}
            """
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        # --- Placeholder Simulation ---
        llm_output_text = "[]" # Default to empty plan
        
        try:
            prompt_data = json.loads(prompt[prompt.find("{"):prompt.rfind("}")+1])
            isolated_error = prompt_data.get("isolated_error", prompt_data.get("error_output", ""))
            history_str = json.dumps(prompt_data.get("failed_plan_history", []))
        except:
            isolated_error = prompt # Fallback
            history_str = ""

        if persona['role'] == "Senior TDD Programmer":
            
            # (PATCH: Handles 'divide' error)
            if 'has no attribute "divide"' in isolated_error:
                print("🐒 Primate: (Simulating LLM) Generating multi-file 'divide' fix...")
                llm_output_text = """
                [
                  {
                    "op": "create_file",
                    "path": "utils.py",
                    "content": "def safe_division_helper(a: int, b: int) -> int:\\n    if b == 0:\\n        return 0\\n    return a // b\\n"
                  },
                  {
                    "op": "modify_file",
                    "path": "calculator.py",
                    "content": "from utils import safe_division_helper\\n\\ndef add(a: int, b: int) -> int:\\n    \\"\\"\\"Adds two integers.\\"\\"\\"\\n    return a + b\\n\\ndef subtract(a: int, b: int) -> int:\\n    \\"\\"\\"Subtracts two integers.\\"\\"\\"\\n    return a - b\\n\\ndef divide(a: int, b: int) -> int:\\n    return safe_division_helper(a, b)\\n"
                  }
                ]
                """
            
            elif 'has no attribute "add"' in isolated_error:
                print("🐒 Primate: (Simulating LLM) Generating 'add' AND 'subtract' functions...")
                llm_output_text = """
                [
                  {
                    "op": "modify_file",
                    "path": "calculator.py",
                    "content": "def add(a: int, b: int) -> int:\\n    \\"\\"\\"Adds two integers.\\"\\"\\"\\n    return a + b\\n\\ndef subtract(a: int, b: int) -> int:\\n    \\"\\"\\"Subtracts two integers.\\"\\"\\"\\n    return a - b\\n"
                  }
                ]
                """
            elif "Cannot find implementation or library stub" in isolated_error or "Cannot find module named 'calculator'" in isolated_error:
                print("🐒 Primate: (Simulating LLM) Generating 'add' AND 'subtract' functions...")
                llm_output_text = """
                [
                  {
                    "op": "create_file",
                    "path": "calculator.py",
                    "content": "def add(a: int, b: int) -> int:\\n    \\"\\"\\"Adds two integers.\\"\\"\\"\\n    return a + b\\n\\ndef subtract(a: int, b: int) -> int:\\n    \\"\\"\\"Subtracts two integers.\\"\\"\\"\\n    return a - b\\n"
                  }
                ]
                """
            else:
                print(f"🐒 Primate: (Simulating LLM) Failed to find a solution for: {isolated_error}")
                llm_output_text = "[]"

        elif persona['role'] == "Lead Architect and Diagnostician":
            
            # (Human's 'flawed test' logic)
            if "incompatible type" in isolated_error.lower() or "argument 1" in isolated_error.lower():
                print("👨‍🔬 Human: (Simulating LLM) Meta-analysis complete. The TDD test is flawed.")
                llm_output_text = """
                [
                  {
                    "op": "analysis",
                    "analysis": "The Primate brain's code is correct. The TDD test at 'test_calculator.py' is flawed, as it is passing strings to a function expecting integers. The plan will correct the test file."
                  },
                  {
                    "op": "modify_file",
                    "path": "test_calculator.py",
                    "content": "from calculator import add, subtract\\n\\nassert add(2, 2) == 4\\nassert subtract(5, 2) == 3\\n"
                  }
                ]
                """
            # (Human's 'atomic fix' logic)
            elif ("incompatible type" in history_str or "argument 1" in history_str) and "import-not-found" in isolated_error:
                print("👨‍🔬 Human: (Simulating LLM) Meta-analysis complete. Primate and Test are *both* flawed. Generating atomic fix.")
                llm_output_text = """
                [
                  {
                    "op": "analysis",
                    "analysis": "The Primate's plan to create 'calculator.py' was correct, but it revealed a flawed test. The test is *also* flawed. This plan fixes BOTH issues at once: it creates the correct 'calculator.py' AND fixes the flawed 'test_calculator.py'."
                  },
                  {
                    "op": "create_file",
                    "path": "calculator.py",
                    "content": "def add(a: int, b: int) -> int:\\n    \\"\\"\\"Adds two integers.\\"\\"\\"\\n    return a + b\\n\\ndef subtract(a: int, b: int) -> int:\\n    \\"\\"\\"Subtracts two integers.\\"\\"\\"\\n    return a - b\\n"
                  },
                  {
                    "op": "modify_file",
                    "path": "test_calculator.py",
                    "content": "from calculator import add, subtract\\n\\nassert add(2, 2) == 4\\nassert subtract(5, 2) == 3\\n"
                  }
                ]
                """
            else:
                print(f"👨‍🔬 Human: (Simulating LLM) Failed to find a strategic solution for: {isolated_error}")
                llm_output_text = "[]"
        # --- End Placeholder ---
        
        plan = json.loads(llm_output_text)
        if not isinstance(plan, list):
            raise ValueError("LLM did_not return a list (plan).")
        return plan
    
    except json.JSONDecodeError as e:
        print(f"🚨 {persona['role']}: LLM returned invalid JSON. Escalating. Error: {e}")
        return []
    except Exception as e:
        print(f"🚨 {persona['role']}: LLM call failed. Escalating. Error: {e}")
        return []
