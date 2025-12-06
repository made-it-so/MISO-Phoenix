from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .schemas import Plan
from pydantic import ValidationError
import json

class Specialist:
    """A specialist AI agent that validates its own output against a Pydantic schema."""
    def __init__(self, system_prompt: str, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            system_prompt + """

            **Your Current Task:**
            {task}

            **Relevant History & Context:**
            {history}

            **Your Available Tools (You MUST use these exact signatures):**
            {tool_signatures}

            **Your Task:**
            Based on your specific role and the task given, define the single, correct action to take.

            **Output Format:**
            Respond with a valid JSON object that strictly follows this schema: 
            `{{"thought": "...", "action": {{ "tool_name": "...", "parameters": {{...}} }} }}`
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def execute_task(self, task: str, history: list, tool_signatures: str) -> Plan:
        history_str = "\n".join(map(str, history))
        response_str = self.chain.invoke({
            "task": task,
            "history": history_str,
            "tool_signatures": tool_signatures
        })
        
        # --- VALIDATION STEP ---
        # This will raise a ValidationError if the JSON is malformed.
        try:
            validated_plan = Plan.model_validate_json(response_str)
            return validated_plan
        except ValidationError as e:
            # Re-raise with a more informative error for the Executive to handle.
            raise ValueError(f"Specialist produced invalid JSON output. Raw response: '{response_str}'. Error: {e}")


# --- Specialist Prompts & Toolsets (unchanged) ---
PROMPT_CATALOG = {
    "CoderAgent": "You are an expert Python developer. Your only goal is to write or modify code to satisfy the given requirements.",
    "TestWriterAgent": "You are an expert QA engineer specializing in Test-Driven Development. Your only goal is to write a robust `pytest` test.",
    "DebuggerAgent": "You are a debugging expert. You are given a file and a test error. Your only goal is to find the bug and propose the patch."
}

TOOLSET_CATALOG = {
    "CoderAgent": ["write_file", "patch_code", "read_file"],
    "TestWriterAgent": ["write_file", "read_file"],
    "DebuggerAgent": ["read_file"]
}
