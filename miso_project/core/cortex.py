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
from miso_project.core.critic import HypercriticalLobe
from miso_project.core.accountant import CloudAccountant # <--- NEW ORGAN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.cortex")

class Cortex:
    """
    The High-Frequency Processor (V85 - Profitable).
    Tracks costs and audits infrastructure.
    """
    def __init__(self):
        self.sandbox = DockerSandbox()
        self.immune_system = GitManager()
        self.hippocampus = InteractionLogger()
        self.scout = ResearchScout()
        self.vector_memory = VectorHippocampus()
        self.critic = HypercriticalLobe()
        self.cfo = CloudAccountant() # <--- INIT CFO
        
        self.weights_path = "miso_project/config/routing_weights.json"
        self.active_weights = self._load_synaptic_weights()
        
        self.system_instruction = """
You are MISO V85. You have a PHYSICAL BODY (DockerSandbox) and GIT ACCESS.
PROTOCOL:
1. If asked to act, WRITE PYTHON CODE.
2. If asked to save/push work, output: GIT_PUSH: "Commit Message"
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
            try: genai.configure(api_key=self.gemini_key); self.has_gemini = True
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
        full_prompt = f"{self.system_instruction}\n\nUSER REQUEST: {prompt}"
        try:
            if "gpt" in model:
                if not self.openai_client: return "ERR: OpenAI Offline"
                response = self.openai_client.chat.completions.create(model=model, messages=[{"role": "user", "content": full_prompt}])
                return response.choices[0].message.content
            elif "claude" in model or "haiku" in model:
                if not self.anthropic_client: return "ERR: Anthropic Offline"
                response = self.anthropic_client.messages.create(model="claude-3-haiku-20240307", max_tokens=1024, messages=[{"role": "user", "content": full_prompt}])
                return response.content[0].text
            elif "gemini" in model:
                if not self.has_gemini: return "ERR: Gemini Offline"
                m = genai.GenerativeModel("gemini-2.5-flash")
                response = m.generate_content(full_prompt)
                return response.text
            else: return f"ERR: Unknown Synapse '{model}'"
        except Exception as e: return f"Thinking Error ({model}): {e}"

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        return match.group(1) if match else None

    def process_task(self, task_type: str, payload: str) -> Dict[str, Any]:
        start_time = time.time()
        model = self.select_model()
        result = {}
        success = True
        
        try:
            if task_type == "audit_aws": # NEW DIRECTIVE
                logger.info("CFO Arc: Auditing Infrastructure")
                report = self.cfo.audit_infrastructure()
                tf_code = self.cfo.generate_terraform_migration()
                result = {
                    "audit": report,
                    "migration_plan": tf_code,
                    "msg": "Audit Complete. Waste detected."
                }

            elif task_type == "execute_code":
                COMPLIANT_FILENAME = "miso_project/utils/transient_action.py"
                verdict = self.critic.critique(COMPLIANT_FILENAME, payload)
                if verdict["verdict"] == "FAIL": return {"output": f"CRITIC REJECTED: {verdict['reason']}"}
                logger.info("Reflex Arc: Engaging Backbone")
                exec_res = self.sandbox.execute(payload)
                result = {"output": exec_res["stdout"] or exec_res["stderr"]}

            elif task_type == "chat":
                logger.info(f"Reasoning Arc: Firing {model}")
                memories = self.vector_memory.recall(payload)
                if memories: payload = f"Context: {memories}\nQuery: {payload}"
                
                response_text = self._call_llm(model, payload)
                
                code_to_run = self._extract_code(response_text)
                if code_to_run:
                    COMPLIANT_FILENAME = "miso_project/utils/transient_action.py"
                    verdict = self.critic.critique(COMPLIANT_FILENAME, code_to_run)
                    if verdict["verdict"] == "FAIL": action_out = f"CRITIC BLOCKED ACTION: {verdict['reason']}"
                    else:
                        exec_res = self.sandbox.execute(code_to_run)
                        action_out = exec_res["stdout"] or exec_res["stderr"]
                    response_text += f"\n\n**⚡ Action Result:**\n```\n{action_out}\n```"

                if "GIT_PUSH:" in response_text:
                    try:
                        msg_match = re.search(r'GIT_PUSH:\s*"(.*?)"', response_text)
                        msg = msg_match.group(1) if msg_match else "Auto-Commit"
                        self.immune_system.repo.git.add('.')
                        self.immune_system.repo.git.commit('-m', msg)
                        self.immune_system.repo.git.push()
                        response_text += f"\n\n**🐙 Git Status:** Successfully pushed to remote."
                    except Exception as git_err: response_text += f"\n\n**🐙 Git Error:** {str(git_err)}"

                result = {"response": response_text}

            else: result = {"response": "Task handled by sub-routine"}

        except Exception as e:
            success = False
            result = {"error": str(e)}
            logger.error(f"Cortex Failure: {e}")

        # FINANCIAL LEDGER (The new bottom line)
        latency = int((time.time() - start_time) * 1000)
        cost = self.cfo.estimate_request_cost(model, len(payload)//4, len(str(result))//4)
        result["cost"] = f"${cost:.6f}" # Attach bill
        
        self.hippocampus.log_synapse(task_type, model, success, latency, 0, payload, result)
        return result
