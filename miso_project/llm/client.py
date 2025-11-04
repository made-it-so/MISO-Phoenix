import json
import os
import re
import google.generativeai as genai

print("--- LLM CLIENT (LIVE V-FINAL - gemini-pro-latest) ---")

# --- Configure the Live Client ---
try:
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=API_KEY)
    
    generation_config = {"temperature": 0.0, "top_p": 1, "top_k": 1, "max_output_tokens": 8192}
    safety_settings = [
      {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
      {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
      {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
      {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    LLM_CLIENT = genai.GenerativeModel(model_name="gemini-pro-latest",
                                      generation_config=generation_config,
                                      safety_settings=safety_settings)
    print("Gemini Pro (latest) client configured successfully.")
except Exception as e:
    print(f"🚨 FATAL ERROR: Could not configure Gemini client: {e}")
    LLM_CLIENT = None
# ---

# --- (THE FIX: Load personas from correct path) ---
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'personas', 'primate_persona.json'), 'r') as f:
        PRIMATE_PERSONA = json.load(f)
    with open(os.path.join(os.path.dirname(__file__), '..', 'personas', 'human_persona.json'), 'r') as f:
        HUMAN_PERSONA = json.load(f)
except FileNotFoundError:
    print("WARNING: Personas not found. Using stub personas.")
    PRIMATE_PERSONA = {"role": "Primate", "principles": [], "output_schema": {}}
    HUMAN_PERSONA = {"role": "Human", "principles": [], "output_schema": {}}


def call_gemini_pro_programmer(prompt: str, persona: dict) -> dict:
    if not LLM_CLIENT:
        print(f"🚨 {persona['role']}: LLM client is not configured. Escalating.")
        return []

    system_prompt = f"""
You are an autonomous "Code-First" TDD agent.
You are the '{persona['role']}'.
Your *only* goal is to solve the user's TDD error.
You *must* respond with a valid JSON array matching this schema:
{json.dumps(persona['output_schema'])}
CRITICAL RULE 1: You must *only* output the JSON array.
Do *not* include any other text, markdown, or explanation.
CRITICAL RULE 2: All 'path' values in your plan MUST be relative to the
workspace root (e.g., 'math_utils.py'). NEVER include 'workspace/'.
"""
    full_prompt = [{"role": "user", "parts": [system_prompt, "\n\n", prompt]}]

    print(f"🧠 {persona['role']}: (LIVE) Calling model gemini-pro-latest...")
    try:
        response = LLM_CLIENT.generate_content(full_prompt)
        llm_output_text = response.text
        print(f"🧠 {persona['role']}: (LIVE) Model response received:\n{llm_output_text}")
        
        json_match = re.search(r'```(json)?\s*(\[.*\])\s*```', llm_output_text, re.DOTALL)
        if json_match:
            plan_str = json_match.group(2)
        else:
            json_start = llm_output_text.find('[')
            json_end = llm_output_text.rfind(']') + 1
            if json_start == -1 or json_end == -1:
                 raise ValueError("LLM did not return a JSON array.")
            plan_str = llm_output_text[json_start:json_end]
        
        plan = json.loads(plan_str)
        if not isinstance(plan, list):
            raise ValueError("LLM did not return a JSON list (plan).")
        return plan
    
    except json.JSONDecodeError as e:
        print(f"🚨 {persona['role']}: LLM returned invalid JSON. Escalating. Error: {e}")
        return []
    except Exception as e:
        print(f"🚨 {persona['role']}: LLM call failed. Escalating. Error: {e}")
        return []
