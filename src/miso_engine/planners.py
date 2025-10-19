from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class StrategistAgent:
    """Decomposes a goal into milestones using advice from the Persona Council."""
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a master AI strategist. Synthesize the user's goal with the council's advice to create a final, robust project plan.

            **User Goal:**
            {goal}

            **Council's Strategic Advice:**
            {advice}

            **Your Task:**
            Create a JSON object containing a 'plan', which is a list of human-readable strings, each representing a distinct phase of the project.
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def create_strategic_plan(self, goal: str, advice: dict) -> list:
        advice_str = json.dumps(advice, indent=2)
        response_str = self.chain.invoke({"goal": goal, "advice": advice_str})
        plan_data = json.loads(response_str)
        return plan_data['plan']

class TacticianAgent:
    """Determines the single next tool call to make progress on a specific milestone."""
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a methodical AI tactician. Decide the next single best action to achieve the current milestone, working backward from its goal.

            **!! SURGICAL PROTOCOL !!**
            To modify a file, you MUST `read_file` in the step immediately before you `patch_code` or `write_file`.

            **Current Milestone:** {milestone}
            **Overall Goal:** {goal}
            **Project File Structure:**
            ```
            {project_layout}
            ```
            **History:** {history}
            **Available Tools:** {tool_signatures}
            
            **Output Format:**
            Respond with a valid JSON object: `{{"thought": "...", "action": {{"tool_name": "...", "parameters": {{...}} }} }}`
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def get_next_action(self, goal: str, milestone: str, history: list, project_layout: str, tool_signatures: str) -> dict:
        history_str = "\n".join(history) if history else "No steps taken yet."
        response_str = self.chain.invoke({
            "goal": goal, "milestone": milestone, "history": history_str,
            "tool_signatures": tool_signatures, "project_layout": project_layout
        })
        return json.loads(response_str)
