# MISO "Phoenix" - ALL BRAINS DE-SIMULATED
# PHASE 3: ADDING THE "TIER 0 CRITIC"
# Tiers: 0 (Critic), 2 (Lizard), 5 (Human), 6 (Einstein)

import time
import json
import os
import re
import asyncio
import ollama
from ollama import AsyncClient
import google.generativeai as genai
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()
try:
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=GOOGLE_API_KEY)
except KeyError:
    print("CRITICAL: 'GOOGLE_API_KEY' not found in .env file.")
except Exception as e:
    print(f"Error configuring Google AI: {e}")

# --- TIER 0: THE CRITIC (Difficulty Assessor) ---
class CriticBrain:
    """
    DE-SIMULATED (ASYNC): The "Tier 0" brain.
    Uses a fast, local model to assess bug difficulty.
    """
    def __init__(self):
        self.name = "Critic (Tier 0)"
        self.cost_per_assessment = 0.0001 # Even cheaper than Lizard
        self.model = "gemma:2b" # Proven local model
        self.client = AsyncClient()

    async def assess_difficulty(self, error_log: str) -> str:
        """
        Analyzes an error log and returns the Tier best suited to fix it.
        Returns a simple string: "Tier 2", "Tier 5", or "Tier 6".
        """
        print(f"   [CRITIC_BRAIN_API]: Assessing difficulty of error... '{error_log.splitlines()[0]}...'")
        
        system_prompt = (
        "You are a 'Human' brain, an expert senior software engineer. "
        "You are given a file with a complex bug and a pytest error log. "
        "Your job is to fix the bug. "
        "You must ONLY return the complete, corrected Python code block. "
        "Do not add any explanation, preamble, or markdown formatting. "
        "DO NOT use ```python or ``` markdown tags. "
        "Your response must be ONLY the raw, valid, runnable Python code."
    )
        )
        user_prompt = (f"Here is the buggy code:\n```python\n{code_content}\n```\n\n"
               f"Here is the pytest error:\n{error_log}\n\n"
               "Please provide the fixed code.")
        
        try:
            response = await self.client.chat(
                model=self.model,
                messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                stream=False
            )
            assessment = response['message']['content'].strip().replace("'", "").replace("\"", "")
            
            # Basic validation
            if "Tier 2" in assessment:
                print(f"   [CRITIC_BRAIN_API]: Assessment: Tier 2 (Lizard)")
                return "Tier 2"
            elif "Tier 6" in assessment:
                print(f"   [CRITIC_BRAIN_API]: Assessment: Tier 6 (Einstein)")
                return "Tier 6"
            else:
                print(f"   [CRITIC_BRAIN_API]: Assessment: Tier 5 (Human)")
                return "Tier 5"

        except Exception as e:
            print(f"   [CRITIC_BRAIN_API]: CRITICAL FAILURE. Ollama API call failed: {e}")
            return "Tier 5" # Default to Human on failure

# --- TIER 2: LIZARD (Worker) ---
class LizardBrain:
    def __init__(self):
        self.name = "Lizard (Cheap)"
        self.cost_per_fix = 0.001
        self.model = "gemma:2b"
        self.client = AsyncClient()

    async def fix(self, code_content, error_log):
        system_prompt = (
            "You are an expert Python linter. You will be given a block of Python code "
            "and a mypy error message. Your job is to fix the code to resolve the mypy error. "
            "You must ONLY return the complete, corrected Python code block. "
            "Do not add any explanation, preamble, or markdown formatting."
        )
        user_prompt = (f"Code:\n```python\n{code_content}\n```\n\nError:\n{error_log}\n\nFixed code:")
        try:
            response = await self.client.chat(
                model=self.model,
                messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}],
                stream=False
            )
            content = response['message']['content']
            fixed_code = content.replace("```python", "").replace("```", "").strip()
            print("   [LIZARD_BRAIN_API]: Fix generated successfully.")
            return fixed_code, self.cost_per_fix
        except Exception as e:
            print(f"   [LIZARD_BRAIN_API]: CRITICAL FAILURE. Ollama API call failed: {e}")
            return None, 0

# --- TIER 5: HUMAN (Worker) ---
class HumanBrain:
    def __init__(self):
        self.name = "Human (Expensive)"
        self.cost_per_fix = 1.50
        self.model = genai.GenerativeModel('models/gemini-pro-latest') # Our proven model

    def fix(self, code_content, error_log):
        print(f"   [HUMAN_BRAIN_API]: Engaging Google Gemini API to analyze... '{error_log.splitlines()[0]}...'")
        system_prompt = (
            "You are 'Human', an expert senior software engineer. "
            "You are given a file with a complex bug and a pytest error log. "
            "Your job is to fix the bug. "
            "You must ONLY return the complete, corrected Python code block. "
            "Do not add any explanation, preamble, or markdown formatting."
        )
        user_prompt = (f"Here is the buggy code:\n```python\n{code_content}\n```\n\n"
                       f"Here is the pytest error:\n{error_log}\n\n"
                       "Please provide the fixed code.")
        try:
            response = self.model.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.types.GenerationConfig(temperature=0.1)
            )
            content = response.text
            match = re.search(r"```python\n(.*?)\n```", content, re.DOTALL)
            fixed_code = match.group(1) if match else content.strip()
            print("   [HUMAN_BRAIN_API]: Fix generated successfully.")
            return fixed_code, self.cost_per_fix
        except Exception as e:
            print(f"   [HUMAN_BRAIN_API]: CRITICAL FAILURE. Gemini API call failed: {e}")
            return None, 0

# --- TIER 6: EINSTEIN (Worker) ---
class EinsteinBrain:
    def __init__(self):
        self.name = "Einstein (Tier 6)"
        self.cost_per_fix = 5.00
        self.persona = self._load_persona()
        self.model = genai.GenerativeModel('models/gemini-pro-latest') # Our proven model

    def _load_persona(self):
        persona_path = "miso_project/personas/einstein_persona.json"
        try:
            with open(persona_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"   [EINSTEIN_BRAIN_API]: CRITICAL ERROR - Could not load persona from {persona_path}")
            return None

    def fix(self, code_content, error_log):
        if not self.persona: return None, 0
        print(f"   [EINSTEIN_BRAIN_API]: Engaging Google Gemini API for Tier-6 Feature Generation...")
        print(f"   [EINSTEIN_BRAIN_API]: Persona '{self.persona.get('persona_name')}' loaded.")
        system_prompt = self.persona.get('system_prompt', "You are a helpful assistant.")
        user_prompt = (f"Here is the code file to modify (it may be empty):\n```python\n{code_content}\n```\n\n"
                       f"Here is the pytest TDD error (ImportError or AttributeError):\n{error_log}\n\n"
                       "Please provide the new, complete code for the file, including the new feature.")
        try:
            response = self.model.generate_content(
                [system_prompt, user_prompt],
                generation_config=genai.types.GenerationConfig(temperature=0.2)
            )
            content = response.text
            try:
                json_match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
                if json_match:
                    parsed_json = json.loads(json_match.group(1))
                    fixed_code = parsed_json[0]['code']
                else:
                    py_match = re.search(r"```python\n(.*?)\n```", content, re.DOTALL)
                    fixed_code = py_match.group(1) if py_match else content.strip()
            except Exception as json_e:
                print(f"   [EINSTEIN_BRAIN_API]: JSON response parsing failed: {json_e}")
                py_match = re.search(r"```python\n(.*?)\n```", content, re.DOTALL)
                fixed_code = py_match.group(1) if py_match else content.strip()
            print("   [EINSTEIN_BRAIN_API]: New feature generated successfully.")
            return fixed_code, self.cost_per_fix
        except Exception as e:
            print(f"   [EINSTEIN_BRAIN_API]: CRITICAL FAILURE. Gemini API call failed: {e}")
            return None, 0
