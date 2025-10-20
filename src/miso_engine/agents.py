from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from . import personas
class Agent:
    def __init__(self, persona_name: str):
        if persona_name not in personas.MISO_PERSONAS:
            raise ValueError(f"Persona '{persona_name}' not found.")
        cfg = personas.MISO_PERSONAS[persona_name]
        self.persona = cfg['persona']
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages([("system", self.persona), ("user", "{input}")])
    def run(self, **kwargs) -> str:
        prompt = self.prompt.invoke(kwargs)
        response = self.llm.invoke(prompt)
        return response.content
