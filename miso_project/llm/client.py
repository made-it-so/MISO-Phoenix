import json
import os

print("--- LLM CLIENT (PATCHED V8 - ATOMIC HUMAN) ---") # <-- NEW CANARY

# This is a placeholder for your real LLM client.
# We are using a simulator here for demonstration.
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
    
    This function now accepts a 'persona' object to define
    its role and output schema.
    
    *** THIS IS A SIMULATOR ***
    Replace this with your actual Gemini/Ollama/OpenAI client.
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
            # We parse the full JSON context
            prompt_data = json.loads(prompt[prompt.find("{"):prompt.rfind("}")+1])
            isolated_error = prompt_data.get("isolated_error", prompt_data.get("error_output", ""))
            history_str = json.dumps(prompt_data.get("failed_plan_history", []))
        except:
            isolated_error = prompt # Fallback
            history_str = ""

        if persona['role'] == "Senior TDD Programmer":
            
            # (Primate's 'add' logic)
            if 'has no attribute "add"' in isolated_error:
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
            # (Primate's 'import' logic)
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
            
            # (THE FIX: This is the ATOMIC plan)
            # This simulates the Human brain seeing that the *current* error
            # is [arg-type], which was revealed by a Primate failure.
            if "incompatible type" in isolated_error.lower() or "argument 1" in isolated_error.lower():
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
            raise ValueError("LLM did not return a list (plan).")
        return plan
    
    except json.JSONDecodeError as e:
        print(f"🚨 {persona['role']}: LLM returned invalid JSON. Escalating. Error: {e}")
        return []
    except Exception as e:
        print(f"🚨 {persona['role']}: LLM call failed. Escalating. Error: {e}")
        return []
