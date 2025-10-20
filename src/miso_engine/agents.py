from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from . import personas
import json

class Agent:
    def __init__(self, persona_name: str, tool_kb: dict | None = None):
        if persona_name not in personas.MISO_PERSONAS:
            raise ValueError(f"Persona '{persona_name}' not found.")
        
        cfg = personas.MISO_PERSONAS[persona_name]
        
        # --- V31.2 KNOWLEDGE-AWARE UPGRADE ---
        
        # --- CRITICAL FIX: Escape braces in the base persona for LangChain templater ---
        base_persona_raw = cfg['persona']
        base_persona_escaped = base_persona_raw.replace("{", "{{").replace("}", "}}")
        
        if tool_kb:
            tool_manual_raw = json.dumps(tool_kb, indent=2)
            
            # --- CRITICAL FIX: Escape braces in the tool manual for LangChain templater ---
            tool_manual_escaped = tool_manual_raw.replace("{", "{{").replace("}", "}}")
            
            final_persona = f"""{base_persona_escaped}

--- TOOL MANUAL ---
You have access to the following tools. You MUST use the exact syntax specified in this manual.
{tool_manual_escaped}
"""
            self.persona = final_persona
        else:
            self.persona = base_persona_escaped # Assign the escaped version
        # --- END V31.2 UPGRADE ---

        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([("system", self.persona), ("user", "{input}")])

    def run(self, **kwargs) -> str:
        prompt = self.prompt.invoke(kwargs)
        response = self.llm.invoke(prompt)
        return response.content
