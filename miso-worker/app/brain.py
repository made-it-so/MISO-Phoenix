import os
import logging
import google.generativeai as genai
from openai import OpenAI
from anthropic import Anthropic

logger = logging.getLogger('Brain')
logger.setLevel(logging.INFO)

class UniversalBrain:
    def __init__(self):
        self.provider = None
        self.client = None
        self.model_name = None
        self._connect()

    def _connect(self):
        # PRIORITY 1: ANTHROPIC (Best Coder)
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                self.client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
                self.provider = "ANTHROPIC"
                self.model_name = "claude-3-5-sonnet-20240620"
                logger.info(f"🧠 Brain Linked: {self.provider} ({self.model_name})")
                return
            except: pass

        # PRIORITY 2: OPENAI (Best Reasoner)
        if os.environ.get("OPENAI_API_KEY"):
            try:
                self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
                self.provider = "OPENAI"
                self.model_name = "gpt-4o"
                logger.info(f"🧠 Brain Linked: {self.provider} ({self.model_name})")
                return
            except: pass

        # PRIORITY 3: GEMINI (Best Context/Price)
        if os.environ.get("GEMINI_API_KEY"):
            try:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                self.provider = "GOOGLE"
                self.model_name = "gemini-1.5-pro"
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"🧠 Brain Linked: {self.provider} ({self.model_name})")
                return
            except: pass
            
        logger.critical("💀 NO VALID BRAIN FOUND.")

    def think(self, prompt, system_instruction="You are a helpful AI."):
        if not self.provider: return None

        try:
            if self.provider == "ANTHROPIC":
                message = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    system=system_instruction,
                    messages=[{"role": "user", "content": prompt}]
                )
                return message.content[0].text

            elif self.provider == "OPENAI":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content

            elif self.provider == "GOOGLE":
                # Gemini combines system prompt differently, keeping simple for adapter
                full_prompt = f"{system_instruction}\n\n{prompt}"
                response = self.client.generate_content(full_prompt)
                return response.text

        except Exception as e:
            logger.error(f"Cognitive Failure ({self.provider}): {e}")
            return None

if __name__ == "__main__":
    brain = UniversalBrain()
    print(brain.think("What is your name and what company made you?"))
