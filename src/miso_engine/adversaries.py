from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class Specialist:
    """A specialist AI agent that validates its own output against a schema."""
    def __init__(self, system_prompt: str, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0.1, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            system_prompt + """

            **Your Current Task:**
            {task}

            **Relevant Context (e.g., source code, failing tests):**
            {context}

            **Your Available Tools (You MUST use these exact signatures):**
            {tool_signatures}

            **Your Task:**
            Based on your specific role, define the single, correct action to take.

            **Output Format:**
            Respond with a valid JSON object: `{{"thought": "...", "action": {{ "tool_name": "...", "parameters": {{...}} }} }}`
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def generate_action(self, task: str, context: str, tool_signatures: str) -> dict:
        response_str = self.chain.invoke({
            "task": task, "context": context, "tool_signatures": tool_signatures
        })
        return json.loads(response_str)

# --- Specialist Personas ---
PERSONA_PROMPTS = {
    "BlueTeam": "You are an expert, security-conscious Python developer (the Blue Team). Your goal is to write robust, clean, and secure code that can withstand scrutiny and adversarial testing.",
    "RedTeam": "You are an expert QA and security engineer (the Red Team). Your goal is to break the Blue Team's code. You must think of creative edge cases, security vulnerabilities, and performance issues, and then write a `pytest` test that FAILS, proving the code is flawed."
}

# --- Specialist Toolsets ---
TOOLSET_CATALOG = {
    "BlueTeam": ["patch_code", "read_file"],
    "RedTeam": ["write_file", "read_file"]
}
