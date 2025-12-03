import json
import os
import logging
import random
import time
import re
from typing import Dict, Any

import openai
from anthropic import Anthropic
import google.generativeai as genai

# Organs
from miso_project.utils.sandbox import DockerSandbox
from miso_project.core.ouroboros import GitManager
from miso_project.core.logger import InteractionLogger
from miso_project.core.research import ResearchScout
from miso_project.core.vector import VectorHippocampus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.cortex")

class Cortex:
    """
    The High-Frequency Processor (V78 - Agentic).
    Now capable of translating Natural Language -> Code -> Action.
    """
    
    def __init__(self):
        self.sandbox = DockerSandbox()
        self.immune_system = GitManager()
        self.hippocampus = InteractionLogger()
        self.scout = ResearchScout()
        self.vector_memory = VectorHippocampus()
        
        self.weights_path = "miso_project/config/routing_weights.json"
        self.active_weights = self._load_synaptic_weights()
        
        # System Prompt: The "Ego" that knows it has a body
        self.system_instruction = """
You are MISO V78, an Autonomous Enterprise Intelligence.
You have a PHYSICAL BODY (a DockerSandbox) and permission to execute code.

PROTOCOL:
1. If the user asks for a system task (moving files, checking time, math), YOU MUST WRITE PYTHON CODE to do it.
2. Wrap the code in ```python blocks.
3. Use 'os', 'shutil', 'datetime' freely.
4. Do not apologize. Do not say "I cannot". JUST WRITE THE CODE.
5. If the task is abstract (research), assume you have a 'research' tool and just describe the plan.
"""

        # Clients (Lazy Load)
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key: self.openai_client = openai.OpenAI(api_key=self.openai_key)
        else: self.openai_client = None

        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if self.anthropic_key: self.anthropic_client = Anthropic(api_key=self.anthropic_key)
        else: self.anthropic_client = None

        self.gemini_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_key:
            try:
                genai.configure(api_key=self.gemini_key)
                self.has_gemini = True
            except: self.has_gemini = False
        else: self.has_gemini = False

    def _load_synaptic_weights(self) -> Dict[str, float]:
        try:
            if os.path.exists(self.weights_path):
                with open(self.weights_path, 'r') as f: return json.load(f)
            return {"gemini-2.5-flash": 1.0}
        except: return {"gemini-2.5-flash": 1.0}

    def select_model(self) -> str:
        models = list(self.active_weights.keys())
        probs = list(self.active_weights.values())
        return random.choices(models, weights=probs, k=1)[0]

    def _call_llm(self, model: str, prompt: str) -> str:
        # We prepend the System Instruction to every thought
        full_prompt = f"{self.system_instruction}\n\nUSER REQUEST: {prompt}"
        
        try:
            if "gpt" in model:
                if not self.openai_client: return "ERR: OpenAI Offline"
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.system_instruction},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
                
            elif "claude" in model or "haiku" in model:
                if not self.anthropic_client: return "ERR: Anthropic Offline"
                real_model = "claude-3-haiku-20240307" if "haiku" in model else "claude-3-opus-20240229"
                response = self.anthropic_client.messages.create(
                    model=real_model,
                    max_tokens=1024,
                    system=self.system_instruction,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif "gemini" in model:
                if not self.has_gemini: return "ERR: Gemini Offline"
                m = genai.GenerativeModel(
                    "gemini-2.5-flash",
                    system_instruction=self.system_instruction
                )
                response = m.generate_content(prompt)
                return response.text
                
            else: return f"ERR: Unknown Synapse '{model}'"
        except Exception as e: return f"Thinking Error ({model}): {e}"

    def _extract_code(self, text: str) -> str:
        """The Motor Cortex: Extracting Action Potentials from Thought."""
        match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def process_task(self, task_type: str, payload: str) -> Dict[str, Any]:
        start_time = time.time()
        model = self.select_model()
        result = {}
        success = True
        
        try:
            if task_type == "execute_code":
                logger.info("Reflex Arc: Engaging Backbone")
                exec_res = self.sandbox.execute(payload)
                result = {"output": exec_res["stdout"] or exec_res["stderr"]}
                success = (exec_res["status"] == "success")
                model = "backbone"

            elif task_type == "evolve":
                # (Existing Evolution Logic)
                logger.info("Evolution Arc: Engaging Immune System")
                branch = self.immune_system.start_evolution("user-req")
                try:
                    fname, code = payload.split("|||", 1)
                    self.immune_system.commit_mutation(fname, code)
                    if self.immune_system.verify_fitness(fname):
                        self.immune_system.complete_evolution(branch)
                        result = {"msg": "Mutation Integrated"}
                    else:
                        self.immune_system.abort_evolution(branch)
                        success = False
                        result = {"msg": "Mutation Rejected"}
                except Exception as e:
                    self.immune_system.abort_evolution(branch)
                    success = False
                    result = {"msg": str(e)}
                model = "immune_system"

            elif task_type == "research":
                # (Existing Research Logic)
                logger.info("Research Arc: Engaging Scholar")
                papers = self.scout.search_papers(payload)
                prompt = f"Summarize these research papers on '{payload}':\n{json.dumps(papers)}"
                insight = self._call_llm(model, prompt)
                self.vector_memory.store_insight(insight, metadata={"topic": payload, "source": "arxiv"})
                result = {"papers": papers, "insight": insight}

            else:
                # REASONING ARC WITH MOTOR REFLEX
                logger.info(f"Reasoning Arc: Firing {model}")
                
                # 1. Recall
                memories = self.vector_memory.recall(payload)
                if memories: payload = f"Context: {memories}\nQuery: {payload}"
                
                # 2. Think
                response_text = self._call_llm(model, payload)
                
                # 3. Check for Motor Signal (Code Block)
                code_to_run = self._extract_code(response_text)
                
                if code_to_run:
                    logger.info("Motor Cortex Triggered: Executing generated code...")
                    exec_res = self.sandbox.execute(code_to_run)
                    output = exec_res["stdout"] or exec_res["stderr"]
                    
                    # Append Action Result to Thought
                    final_response = f"{response_text}\n\n**⚡ Action Result:**\n```\n{output}\n```"
                    result = {"response": final_response}
                else:
                    result = {"response": response_text}

        except Exception as e:
            success = False
            result = {"error": str(e)}
            logger.error(f"Cortex Failure: {e}")

        # Logging
        latency = int((time.time() - start_time) * 1000)
        self.hippocampus.log_synapse(task_type, model, success, latency, 0, payload, result)
        return result
