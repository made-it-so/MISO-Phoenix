import json
import os
import logging
import random
import time
import re
import base64
import io
from typing import Dict, Any
from PIL import Image

import openai
from anthropic import Anthropic
import google.generativeai as genai

# ORGANS
from miso_project.utils.sandbox import DockerSandbox
from miso_project.core.ouroboros import GitManager
from miso_project.core.logger import InteractionLogger
from miso_project.core.research import ResearchScout
from miso_project.core.vector import VectorHippocampus
from miso_project.core.critic import HypercriticalLobe
from miso_project.core.accountant import CloudAccountant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("miso.core.cortex")

class Cortex:
    """
    The High-Frequency Processor (V91 - Restored).
    Integrates Vision, Voice, Criticism, and Tactile Execution.
    """
    def __init__(self):
        self.sandbox = DockerSandbox()
        self.immune_system = GitManager()
        self.hippocampus = InteractionLogger()
        self.scout = ResearchScout()
        self.vector_memory = VectorHippocampus()
        self.critic = HypercriticalLobe()
        self.cfo = CloudAccountant()
        
        self.weights_path = "miso_project/config/routing_weights.json"
        self.active_weights = self._load_synaptic_weights()
        self.system_instruction = "You are MISO V91. Concise Enterprise Intelligence."
        
        # Clients
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
        return {"gemini-2.5-flash": 1.0}

    def select_model(self) -> str:
        return "gemini-2.5-flash"

    # --- SENSORY METHODS ---
    def _transcribe_audio(self, audio_bytes: bytes) -> str:
        if not self.openai_client: return "ERR: Auditory Lobe Offline"
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "command.wav"
            return self.openai_client.audio.transcriptions.create(model="whisper-1", file=audio_file, language="en").text
        except Exception as e: return f"Hearing Loss: {e}"

    def _generate_speech(self, text: str) -> str:
        if not self.openai_client: return None
        try:
            res = self.openai_client.audio.speech.create(model="tts-1", voice="alloy", input=text[:4096])
            return base64.b64encode(res.content).decode('utf-8')
        except: return None

    def _call_vision(self, prompt: str, image_b64: str) -> str:
        if not self.has_gemini: return "ERR: Vision requires Gemini."
        try:
            m = genai.GenerativeModel('gemini-2.5-flash')
            img = Image.open(io.BytesIO(base64.b64decode(image_b64)))
            return m.generate_content([prompt, img]).text
        except Exception as e: return f"Vision Failure: {e}"

    def _call_llm(self, model: str, prompt: str) -> str:
        try:
            if "gemini" in model and self.has_gemini:
                return genai.GenerativeModel("gemini-2.5-flash").generate_content(prompt).text
            if self.openai_client:
                return self.openai_client.chat.completions.create(model="gpt-4o", messages=[{"role":"user","content":prompt}]).choices[0].message.content
            return "ERR: No Cognitive Function"
        except Exception as e: return str(e)

    def _extract_code(self, text: str) -> str:
        match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
        return match.group(1) if match else None

    # --- MAIN LOOP ---
    def process_task(self, task_type: str, payload: str, image_data: str = None, audio_data: str = None) -> Dict[str, Any]:
        start_time = time.time()
        model = self.select_model()
        result = {}
        success = True
        
        try:
            # 1. AUDIO SENSE
            if audio_data:
                logger.info("Processing Audio...")
                transcription = self._transcribe_audio(base64.b64decode(audio_data))
                if not transcription or len(transcription) < 2:
                    return {"response": "Audio unclear.", "transcription": "(Silence)"}
                payload = transcription
                task_type = "chat"

            # 2. ROUTING
            if task_type == "audit_aws":
                result = {"audit": self.cfo.audit_infrastructure(), "msg": "Audit Complete"}

            elif task_type == "execute_code":
                # RESTORED: CRITIC + OUTPUT CAPTURE
                COMPLIANT_FILENAME = "miso_project/utils/transient_action.py"
                
                # A. Critique
                verdict = self.critic.critique(COMPLIANT_FILENAME, payload)
                if verdict["verdict"] == "FAIL":
                    return {"output": f"CRITIC REJECTED: {verdict['reason']}"}
                
                # B. Execute
                logger.info("Reflex Arc: Engaging Backbone")
                exec_res = self.sandbox.execute(payload, trusted=True)
                
                # C. Return Actual Output
                result = {"output": exec_res["stdout"] or exec_res["stderr"] or "No Output"}
                success = (exec_res["status"] == "success")

            elif task_type == "research":
                # RESTORED: RESEARCH HANDLER
                papers = self.scout.search_papers(payload)
                prompt = f"Summarize:\n{json.dumps(papers)}"
                insight = self._call_llm(model, prompt)
                self.vector_memory.store_insight(insight, metadata={"topic": payload})
                result = {"papers": papers, "insight": insight}

            elif task_type == "chat":
                logger.info(f"Reasoning Arc: Firing {model}")
                
                if image_data:
                    response_text = self._call_vision(payload, image_data)
                else:
                    if not audio_data:
                        memories = self.vector_memory.recall(payload)
                        if memories: payload = f"Context: {memories}\nQuery: {payload}"
                    response_text = self._call_llm(model, payload)
                
                # Action Reflex
                code_to_run = self._extract_code(response_text)
                if code_to_run:
                    COMPLIANT_FILENAME = "miso_project/utils/transient_action.py"
                    verdict = self.critic.critique(COMPLIANT_FILENAME, code_to_run)
                    if verdict["verdict"] == "FAIL":
                        action_out = f"CRITIC BLOCKED: {verdict['reason']}"
                    else:
                        exec_res = self.sandbox.execute(code_to_run, trusted=True)
                        action_out = exec_res["stdout"] or exec_res["stderr"]
                    response_text += f"\n\n**⚡ Action Result:**\n```\n{action_out}\n```"

                # Git Reflex
                if "GIT_PUSH:" in response_text:
                    try:
                        msg = re.search(r'GIT_PUSH:\s*"(.*?)"', response_text).group(1)
                        self.immune_system.repo.git.add('.')
                        self.immune_system.repo.git.commit('-m', msg)
                        self.immune_system.repo.git.push()
                        response_text += "\n\n**🐙 Git Status:** Pushed."
                    except Exception as e: response_text += f"\n\n**🐙 Git Error:** {e}"

                # Voice Reply
                audio_reply = self._generate_speech(response_text) if audio_data else None
                result = {"response": response_text, "audio_reply": audio_reply, "transcription": payload if audio_data else None}

        except Exception as e:
            success = False
            result = {"error": str(e)}
            logger.error(f"Cortex Failure: {e}")

        # Ledger
        latency = int((time.time() - start_time) * 1000)
        cost = self.cfo.estimate_request_cost(model, len(payload)//4, len(str(result))//4)
        result["cost"] = f"${cost:.6f}"
        self.hippocampus.log_synapse(task_type, model, success, latency, 0, payload, result)
        
        return result
