import sys
import os
import json
import re # Make sure re is imported
import traceback # Added for error reporting
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Import personas ---
try:
    from . import personas # type: ignore
except ImportError:
    # Handle if run as standalone script for testing, though main.py handles path
    import personas # type: ignore

# --- Helper Function for Brace Escaping ---
def _escape_braces(text: str) -> str:
    """Escapes single braces for LangChain templating."""
    return text.replace("{", "{{").replace("}", "}}")
class Agent:
    """Represents a MISO agent with a specific persona."""
    def __init__(self, persona_name: str):
        """Initializes an agent with a persona from personas.py."""
        
        # --- Load Persona Config ---
        if persona_name not in personas.MISO_PERSONAS:
            raise ValueError(f"Persona '{persona_name}' not found in personas.py.")
            
        cfg = personas.MISO_PERSONAS[persona_name]
        
        # Ensure the critical 'persona' key exists
        if 'persona' not in cfg:
             raise KeyError(f"Persona '{persona_name}' is missing the required 'persona' key in its definition.")

        # --- Prepare Persona/System Message ---
        base_persona_raw = cfg['persona']
        # Use 'system_message_template' if available, otherwise fallback to 'persona'
        system_message_content_raw = cfg.get('system_message_template', base_persona_raw)

        # --- Optimized Brace Escaping ---
        # Escape the base persona first
        base_persona_escaped = _escape_braces(base_persona_raw)
        # Only escape the system message if it's different from the base persona
        if system_message_content_raw == base_persona_raw:
            system_message_content_escaped = base_persona_escaped
        else:
            system_message_content_escaped = _escape_braces(system_message_content_raw)
        # --- End Optimization ---

        # --- Initialize LangChain Components ---
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
             # This specific error string is expected by the orchestrator
             raise ImportError("OpenAIError: The api_key client option must be set... environment variable.")

        self.llm = ChatOpenAI(
            model=cfg.get("model_name", "gpt-4o"),
            temperature=cfg.get("temperature", 0.0),
            api_key=api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_message_content_escaped),
            ("user", "{input}")
        ])
        
        self.output_parser = StrOutputParser()
        
        # --- Chain ---
        self.chain = self.prompt | self.llm | self.output_parser
        
        # print(f"✅ Agent '{persona_name}' initialized.") # Quieted
def run(self, input: str) -> str:
        """Runs the agent's chain with the given input."""
        try:
            # LangChain expects a dictionary for the input variables
            response = self.chain.invoke({"input": input})
            return response
        except Exception as e:
            print(f"❌ ERROR running agent: {e}")
            traceback.print_exc()
            return f"Agent execution failed: {e}"

# This allows main.py to use `agents.get("...")`
def get(agent_name: str) -> Agent | None:
    """Helper to retrieve an agent instance from the global dict (defined in main.py)."""
    try:
        from __main__ import agents as main_agents_dict
        return main_agents_dict.get(agent_name)
    except ImportError:
        # This might happen if file is imported outside of main.py context
        # print("⚠️ Warning: Could not import agents dict from main.py in agents.get")
        return None
    except Exception as e:
        print(f"⚠️ Warning: Error importing agents dict: {e}")
        return None