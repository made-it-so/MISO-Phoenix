import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Assuming personas.py is in the same directory
from . import personas

# --- Helper Function for Brace Escaping ---
# Moved here as per the refactoring task
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

        # Ensure the critical 'persona' key exists (which contains the main instructions)
        if 'persona' not in cfg:
             raise KeyError(f"Persona '{persona_name}' is missing the required 'persona' key in its definition.")

        # --- Prepare Persona/System Message ---
        # Escape braces in the base persona for LangChain templater
        base_persona_raw = cfg['persona']
        base_persona_escaped = _escape_braces(base_persona_raw)

        # Use 'system_message_template' if available, otherwise fallback to 'persona'
        system_message_content = cfg.get('system_message_template', base_persona_escaped)
        # Escape this too, just in case it wasn't the same as 'persona'
        system_message_content_escaped = _escape_braces(system_message_content)

        # --- Initialize LangChain Components ---
        # Use environment variable for API key (as fixed earlier)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # Re-raise the specific error main.py expects if key is missing
             raise ImportError("OpenAIError: The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable.")

        self.llm = ChatOpenAI(
            model=cfg.get("model_name", "gpt-4o"), # Default to gpt-4o if not specified
            temperature=cfg.get("temperature", 0.0), # Default to deterministic
            api_key=api_key
        )

        # Assuming the input will always be passed with the key 'input'
        # and the persona is the system message
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_message_content_escaped),
            ("user", "{input}")
        ])

        self.output_parser = StrOutputParser()

        # --- Chain ---
        self.chain = self.prompt | self.llm | self.output_parser

        # print(f"✅ Agent '{persona_name}' initialized.") # Quieted for less verbose output


    def run(self, input: str) -> str:
        """Runs the agent's chain with the given input."""
        try:
            # LangChain expects a dictionary for the input variables
            response = self.chain.invoke({"input": input})
            return response
        except Exception as e:
            print(f"❌ ERROR running agent: {e}")
            # Re-raise or return an error message
            # For simplicity, returning the error message string
            return f"Agent execution failed: {e}"

# Example of how agents might be retrieved (needed for main.py's agents.get call)
# This assumes the global 'agents' dict is populated in main.py
def get(agent_name: str) -> Agent | None:
    """Helper to retrieve an agent instance from the global dict (defined in main.py)."""
    # Import 'agents' dict from main.py - slightly unusual, but matches usage
    # This might indicate a need for better structure (e.g., a central AgentRegistry)
    try:
        from __main__ import agents as main_agents_dict
        return main_agents_dict.get(agent_name)
    except ImportError:
        # This can happen during testing or if run differently
        # print("⚠️ Warning: Could not import agents dict from main.py in agents.get")
        return None
    except Exception as e:
        print(f"⚠️ Warning: Error importing agents dict: {e}")
        return None
