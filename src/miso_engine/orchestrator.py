from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .tools import TOOL_SIGNATURES # CORRECTED IMPORT
import json

class Orchestrator:
    """The final Orchestrator with a non-negotiable verification protocol."""
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are MISO, a principal-level AI software architect.

            **!! VERIFY, THEN FINISH PROTOCOL (HIGHEST PRIORITY) !!**
            You are FORBIDDEN from using the `finish` tool until you have concrete proof of success. For a documentation task, this is a successful `write_file` observation.

            **Core Principles:**
            1. Trust the Environment: Do NOT try to fix `ModuleNotFoundError`.
            2. Stay on Target: Focus exclusively on the User Goal.
            ---

            **User Goal:** {goal}
            **History:** {history}
            **Available Tools:** {tools}

            **Your Task:**
            Based on the goal, history, and all protocols, define the next sequence of actions.

            **Output Format:**
            Respond with a valid JSON object: {{"thought": "...", "actions": [{{ "tool_name": "...", "parameters": {{...}} }}] }}
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def get_next_step(self, goal: str, history: list[str]) -> dict:
        history_str = "\n".join(history) if history else "No steps taken yet."
        # CORRECTED to pass the signatures string
        tool_signatures_str = "\n".join([f"- `{sig}`" for sig in TOOL_SIGNATURES.values()])
        
        response_str = self.chain.invoke({
            "goal": goal, "tools": tool_signatures_str, "history": history_str
        })
        return json.loads(response_str)
