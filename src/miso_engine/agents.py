import json
import os
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from .util import MisoLLM, logger, extract_json

# --- 🚀 DYNAMIC PERSONA LOADER ---

def load_persona_registry(persona_dir: Path) -> Dict[str, Dict[str, Any]]:
    """Dynamically loads all .json personas from the persona directory."""
    registry = {}
    if not persona_dir.exists():
        logger.error(f"Persona directory not found: {persona_dir}")
        return {}
        
    for f in persona_dir.glob("*.json"):
        try:
            with open(f, 'r', encoding='utf-8') as pf:
                persona_data = json.load(pf)
                name = persona_data.get("name")
                if name:
                    registry[name] = persona_data
                    logger.info(f"Loading persona: {name}")
                else:
                    logger.warning(f"Persona file {f.name} is missing 'name' key.")
        except Exception as e:
            logger.error(f"Failed to load persona {f.name}: {e}")
    return registry

# Get the persona directory relative to this file
PERSONA_DIR = Path(__file__).parent / "personas"
MISO_PERSONAS = load_persona_registry(PERSONA_DIR)

# --- END DYNAMIC LOADER ---

class Agent:
    _llm_client = None # Shared LLM client

    def __init__(self, persona_name: str):
        if persona_name not in MISO_PERSONAS:
            logger.error(f"Persona '{persona_name}' not found in MISO_PERSONAS registry.")
            raise ValueError(f"Persona '{persona_name}' not found.")
        
        persona = MISO_PERSONAS[persona_name]
        self.name = persona["name"]
        self.model = persona["model"]
        self.system_prompt = persona["system_prompt"]
        
        # Initialize shared client if it doesn't exist
        if Agent._llm_client is None:
            Agent._llm_client = MisoLLM()
        self.llm = Agent._llm_client
        
        # No need to log here, load_persona_registry already did
        # logger.info(f"Agent '{self.name}' initialized with persona '{persona_name}'. Model: {self.model}")

    def _build_messages(self, input_text: str) -> List[Dict[str, str]]:
        """Builds the message list for the LLM call."""
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": input_text})
        return messages

    def run(self, input: str) -> str:
        """Runs the agent with the given input."""
        # --- 🚀 F-STRING FIX ---
        prompt_snippet = input[:100].replace('\n', ' ')
        logger.info(f"Agent '{self.name}' received prompt: {prompt_snippet}...")
        # ---------------------
        
        messages = self._build_messages(input)
        
        try:
            logger.info(f"Agent '{self.name}' running in text-only mode (no tools).")
            response = self.llm.chat(model=self.model, messages=messages)
            
            # Handle the different response objects from MisoLLM
            if hasattr(response, 'content'): # MisoLLM.LLMResponse
                final_content = response.content
            elif hasattr(response, 'text'): # Gemini raw
                final_content = response.text
            elif isinstance(response, str): # Raw string
                final_content = response
            elif hasattr(response, 'message') and hasattr(response.message, 'content'): # OpenAI/Ollama
                final_content = response.message.content
            else:
                logger.error(f"Unknown response type from llm.chat: {type(response)}")
                final_content = f"Error: Unknown response type {type(response)}"
            
            # --- 🚀 F-STRING FIX ---
            response_snippet = final_content[:100].replace('\n', ' ')
            logger.info(f"Agent '{self.name}' (no tools used) response: {response_snippet}...")
            # ---------------------
            return final_content

        except Exception as e:
            logger.error(f"An error occurred in Agent.run: {e}")
            # Log the full traceback for debugging
            logger.error(traceback.format_exc())
            return f"Error: {e}"
