from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class Persona:
    """A specialist AI persona that provides advice from a specific viewpoint."""
    def __init__(self, persona_prompt: str, model_name="gpt-4-turbo-preview"):
        self.llm = ChatOpenAI(temperature=0.7, model_name=model_name)
        self.prompt = ChatPromptTemplate.from_template(
            persona_prompt + """

            **Current Mission Goal:**
            {goal}

            Based on your unique perspective, what is a novel strategy, a hidden risk, or a critical prerequisite for this mission? Provide a single, concise suggestion as a string.
            """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    def get_advice(self, goal: str) -> str:
        return self.chain.invoke({"goal": goal})

PERSONA_PROMPTS = {
    "Technologist": "You are a pragmatic CTO. Your focus is on robust, scalable, and maintainable technical solutions.",
    "Economist": "You are a CFO. Your focus is on efficiency and resource cost. You challenge any plan that seems wasteful.",
    "MBA": "You are a CEO. Your focus is on long-term strategy and ensuring the technical plan aligns with the true business intent of the goal.",
    "Improv_Artist": "You are a creative genius. Your goal is to generate 'what if' ideas that break conventional thinking."
}

def get_persona_council():
    """Initializes and returns a dictionary of all Persona objects."""
    council = {}
    for name, prompt in PERSONA_PROMPTS.items():
        council[name] = Persona(persona_prompt=prompt)
    return council
