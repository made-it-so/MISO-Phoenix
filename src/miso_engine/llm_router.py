import logging
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

# --- The Model Catalog ---
# We now have two pools: standard text models and specialized JSON-only models.
MODELS = {
    # Standard Models
    "opus": ChatAnthropic(model_name="claude-3-opus-20240229"),
    "sonnet": ChatAnthropic(model_name="claude-3-sonnet-20240229"),
    "haiku": ChatAnthropic(model_name="claude-3-haiku-20240307"),
    "gpt-4-turbo": ChatOpenAI(model_name="gpt-4-turbo", temperature=0),
    "gpt-3.5-turbo": ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0),
    "gemini-pro": ChatGoogleGenerativeAI(model="gemini-pro"),

    # JSON-Specific Models
    "gpt-4-turbo-json": ChatOpenAI(model_name="gpt-4-turbo", temperature=0, model_kwargs={"response_format": {"type": "json_object"}}),
    "gpt-3.5-turbo-json": ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, model_kwargs={"response_format": {"type": "json_object"}}),
}

class LLMRouter:
    """Analyzes a task and routes it to the most appropriate LLM from the correct pool."""
    def __init__(self, primary_strategist="gpt-4-turbo-json", primary_tactician="gpt-3.5-turbo-json", primary_summarizer="gpt-3.5-turbo", failover="gemini-pro"):
        self.primary_strategist = primary_strategist
        self.primary_tactician = primary_tactician
        self.primary_summarizer = primary_summarizer
        self.failover = failover
        logging.info(f"LLM Router initialized with multiple model pools.")

    def get_llm(self, task_type: str):
        """
        Returns the appropriate LLM client based on the task type.
        Task types: 'strategist', 'tactician', 'summarizer', 'synthesizer'
        """
        if task_type == "strategist":
            model_name = self.primary_strategist
        elif task_type == "tactician":
            model_name = self.primary_tactician
        elif task_type == "summarizer":
            model_name = self.primary_summarizer
        else: # Default for synthesis or other complex text tasks
            model_name = "gpt-4-turbo"

        try:
            llm_client = MODELS[model_name]
            logging.info(f"Routing task of type '{task_type}' to model: {model_name}")
            return llm_client
        except Exception as e:
            logging.warning(f"Could not access primary model '{model_name}'. Error: {e}. Switching to failover model.")
            return MODELS[self.failover]
