from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json

class Auditor:
    """
    The Strategic Auditor. It critiques plans and suggests meta-level improvement goals.
    """
    def __init__(self, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0.1, model_name=model_name, model_kwargs={"response_format": {"type": "json_object"}})
        self.prompt = ChatPromptTemplate.from_template(
            """
            You are a meticulous, principal-level AI QA architect. Your job is to audit a plan and the overall process.

            **Core Mandates:**
            1.  **Critique the Plan:** Is the proposed plan a logical and efficient step toward the User's Goal?
            2.  **Identify Systemic Inefficiency:** Are you seeing a pattern of failure or inefficiency in the history? Is the agent struggling with a problem that a better tool or prompt could solve permanently?

            **User's High-Level Goal:**
            {goal}

            **History of All Steps Taken:**
            {history}
            
            **The Proposed Plan:**
            {plan}

            **Your Task:**
            Review the plan in the context of the history and the user's goal.

            **Output Format:**
            You MUST respond with a JSON object with two keys:
            1.  `approved`: A boolean (true or false).
            2.  `feedback`: If the plan is good, provide a concise approval. If the plan is flawed, provide actionable advice.
            3.  `new_goal_suggestion`: (Optional) If you identify a systemic inefficiency, provide a new, high-level goal for the AI to improve itself (e.g., "Upgrade the `patch_code` tool to handle multi-line replacements."). Otherwise, this should be null.
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def audit_plan(self, goal: str, plan: dict, history: list[str]) -> dict:
        """Audits the given plan and returns the verdict and any new goal."""
        plan_str = json.dumps(plan, indent=2)
        history_str = "\n".join(history) if history else "No steps taken yet."
        response_str = self.chain.invoke({
            "goal": goal,
            "plan": plan_str,
            "history": history_str
        })
        return json.loads(response_str)
