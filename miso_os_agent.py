import subprocess
import tempfile
import logging
import urllib.request
import json
import argparse
import sys
import os
import ast
import venv
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

try:
    import chromadb
    import uuid
    HAS_MEMORY = True
except ImportError:
    HAS_MEMORY = False

logging.basicConfig(level=logging.INFO, format='[MISO OS] %(message)s')

# We generate backticks mathematically so PowerShell/Markdown parsers don't crash
TICKS = chr(96) * 3

class MemoryBank:
    """Persistent Vector Memory"""
    def __init__(self):
        self.enabled = HAS_MEMORY
        if self.enabled:
            self.client = chromadb.PersistentClient(path="./.miso_memory")
            self.collection = self.client.get_or_create_collection(name="miso_fixes")

    def memorize(self, objective: str, final_code: str):
        if self.enabled and objective.strip():
            self.collection.add(
                documents=[objective],
                metadatas=[{"code": final_code}],
                ids=[str(uuid.uuid4())]
            )

class ExecutionSandbox:
    """Phase 3 Sandbox: Executes Python inside VENV, or arbitrary Shell commands."""
    def __init__(self, timeout_seconds: int = 15):
        self.timeout = timeout_seconds
        self.venv_dir = Path(os.getcwd()) / ".miso_venv"
        self._ensure_venv()

    def _ensure_venv(self):
        if not self.venv_dir.exists():
            logging.info("Creating isolated virtual environment...")
            venv.create(self.venv_dir, with_pip=True)
        if os.name == 'nt':
            self.python_exe = str(self.venv_dir / "Scripts" / "python.exe")
            self.pip_exe = str(self.venv_dir / "Scripts" / "pip.exe")
        else:
            self.python_exe = str(self.venv_dir / "bin" / "python")
            self.pip_exe = str(self.venv_dir / "bin" / "pip")

    def _resolve_dependencies(self, source_code: str):
        try: tree = ast.parse(source_code)
        except SyntaxError: return
        imports = {n.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for n in node.names}
        imports.update({node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module})
        stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
        missing = [pkg for pkg in imports if pkg not in stdlib]
        if missing:
            subprocess.run([self.pip_exe, "install", "-q"] + missing, check=False)

    def execute_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        if language == "shell":
            try:
                result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=self.timeout)
                if result.returncode == 0:
                    return {"status": "success", "stdout": result.stdout}
                return {"status": "error", "error_type": "ShellError", "stderr": result.stderr}
            except subprocess.TimeoutExpired:
                return {"status": "error", "error_type": "TimeoutError", "stderr": "Shell command timed out."}
        else:
            self._resolve_dependencies(code)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_path = temp_file.name
            try:
                result = subprocess.run([self.python_exe, temp_path], capture_output=True, text=True, timeout=self.timeout)
                if result.returncode == 0:
                    return {"status": "success", "stdout": result.stdout}
                return {"status": "error", "error_type": "RuntimeError", "stderr": result.stderr}
            except subprocess.TimeoutExpired:
                return {"status": "error", "error_type": "TimeoutError", "stderr": "Python script timed out."}
            finally:
                Path(temp_path).unlink(missing_ok=True)

class ClaudeTeacher:
    """Escalation protocol for Phase 3."""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "[https://api.anthropic.com/v1/messages](https://api.anthropic.com/v1/messages)"
        self.model_name = "claude-3-7-sonnet-20250219" # Default fallback

    def ask_for_help(self, history: str) -> Optional[str]:
        logging.info(f"ESCALATION: Calling Teacher Model...")
        prompt = f"A local AI failed to solve this OS objective. Here is the log of its attempts:\n{history}\n\nSolve the objective. Return ONLY a valid JSON object matching this schema:\n{{\"thought\": \"...\", \"action\": \"python\", \"code\": \"...\", \"is_final\": true}}"
        
        payload = {"model": self.model_name, "max_tokens": 2048, "messages": [{"role": "user", "content": prompt}]}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(self.api_url, data=data, headers={'Content-Type': 'application/json', 'x-api-key': self.api_key, 'anthropic-version': '2023-06-01'})
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf-8'))
                raw_text = result.get('content', [{}])[0].get('text', '')
                cleaned = raw_text.strip()
                if cleaned.startswith(f"{TICKS}json"): cleaned = cleaned[7:]
                if cleaned.endswith(TICKS): cleaned = cleaned[:-3]
                return json.loads(cleaned)["code"].strip()
        except Exception as e:
            logging.error(f"Teacher API Error: {e}")
            return None

class MisoAgent:
    def __init__(self, model_name: str = "miso-coder:latest", api_url: str = "http://localhost:11434/api/chat"):
        self.model_name = model_name
        self.api_url = api_url

    def generate_system_prompt(self) -> str:
        return """You are Miso, an autonomous Operating System agent.
You achieve goals by running commands, exploring the filesystem, and observing outputs.
Output ONLY a valid JSON object with exactly four keys:
"thought": "Your internal reasoning for the next step."
"action": Must be exactly "python" or "shell". Use shell for directory exploration or sys checks.
"code": "The raw python code or shell command to execute."
"is_final": true/false. Set to false to observe the output of your command. Set to true ONLY when the objective is completely solved and 'code' contains the final deliverable."""

    def parse_response(self, raw_llm_text: str) -> Optional[Tuple[str, str, str, bool]]:
        try:
            cleaned = raw_llm_text.strip()
            if cleaned.startswith(f"{TICKS}json"): cleaned = cleaned[7:]
            if cleaned.endswith(TICKS): cleaned = cleaned[:-3]
            data = json.loads(cleaned)
            print(f"\n🧠 [MISO THOUGHT]: {data.get('thought', '...')}")
            print(f"⚡ [MISO ACTION]: Executing {data.get('action', 'python').upper()}...")
            return data["thought"], data["action"], data["code"], data["is_final"]
        except json.JSONDecodeError:
            return None

    def query_model(self, history: str) -> str:
        schema = {
            "type": "object",
            "properties": {
                "thought": {"type": "string"},
                "action": {"type": "string", "enum": ["python", "shell"]},
                "code": {"type": "string"},
                "is_final": {"type": "boolean"}
            },
            "required": ["thought", "action", "code", "is_final"]
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": self.generate_system_prompt()},
                {"role": "user", "content": history}
            ],
            "format": schema,
            "stream": False,
            "options": {"temperature": 0.1}
        }
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(self.api_url, data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=300) as response:
                return json.loads(response.read().decode('utf-8')).get('message', {}).get('content', '')
        except Exception as e:
            logging.error(f"Ollama API Error: {e}")
            return ""

def run_agentic_loop(agent, sandbox, memory, objective: str, max_steps: int = 10, claude_key=None) -> Tuple[bool, str]:
    history = f"[OBJECTIVE]\n{objective}\n\nExecute actions to achieve this objective. Observe outputs carefully."
    last_code = ""

    for step in range(max_steps):
        logging.info(f"--- ReAct Step {step + 1}/{max_steps} ---")
        raw_response = agent.query_model(history)
        parsed = agent.parse_response(raw_response)

        if not parsed:
            history += "\n[SYSTEM ERROR]: Invalid JSON returned. Follow the schema exactly.\n"
            continue

        thought, action, code, is_final = parsed
        last_code = code

        result = sandbox.execute_code(code, language=action)
        output = result.get("stdout", "") if result["status"] == "success" else result.get("stderr", "")
        
        # Prevent context explosion
        if len(output) > 2000:
            output = output[:2000] + "\n...[OUTPUT TRUNCATED]..."

        if is_final:
            if result["status"] == "success":
                logging.info("✅ Objective achieved successfully!")
                memory.memorize(objective, code)
                return True, code
            else:
                logging.warning("⚠️ Agent declared final, but the code crashed. Forcing continuation.")
                history += f"\n[SYSTEM OVERRIDE - YOU CANNOT DECLARE IS_FINAL=TRUE YET]\nYour final code crashed with:\n{output}\nFix the error and try again.\n"
                continue

        # Append to history for the next loop (The "Observation")
        history += f"\n[YOUR LAST ACTION: {action.upper()}]\n{code}\n\n[OBSERVATION FROM OS]:\n{output}\n"

    logging.error("Agent exhausted max reasoning steps. Escaping loop.")
    
    if claude_key:
        teacher = ClaudeTeacher(claude_key)
        teacher_code = teacher.ask_for_help(history)
        if teacher_code:
            logging.info("🌟 Claude successfully provided a final solution!")
            memory.memorize(objective, teacher_code)
            return True, teacher_code

    return False, last_code

def main():
    parser = argparse.ArgumentParser(description="Miso OS Phase 3: The ReAct Singularity")
    parser.add_argument("target", nargs='?', help="File to fix OR objective to accomplish if --goal is used")
    parser.add_argument("--goal", action="store_true", help="Treat the target as a natural language objective, not a file.")
    parser.add_argument("--model", default="miso-coder:latest")
    parser.add_argument("--claude-key", default=os.environ.get("ANTHROPIC_API_KEY"))
    args = parser.parse_args()

    agent = MisoAgent(model_name=args.model)
    sandbox = ExecutionSandbox()
    memory = MemoryBank()

    if args.goal:
        if not args.target:
            logging.error("You must provide an objective text when using --goal")
            sys.exit(1)
        logging.info(f"Starting OS Agent with Goal: {args.target}")
        success, final_code = run_agentic_loop(agent, sandbox, memory, args.target, claude_key=args.claude_key)
        if success:
            logging.info(f"\n--- FINAL DELIVERABLE ---\n{final_code}\n-------------------------")
    else:
        if not args.target:
            logging.error("Provide a target file or use --goal")
            sys.exit(1)
        target_path = Path(args.target)
        if not target_path.exists():
            logging.error(f"File not found: {args.target}")
            sys.exit(1)
            
        with open(target_path, "r", encoding="utf-8") as f:
            broken_code = f.read()
            
        objective = f"The following Python script is failing. Use the shell to inspect any missing requirements, then fix the script.\n\n{TICKS}python\n{broken_code}\n{TICKS}"
        success, final_code = run_agentic_loop(agent, sandbox, memory, objective, claude_key=args.claude_key)
        if success:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(final_code)
            logging.info(f"Healed and overwritten: {args.target}")

if __name__ == "__main__":
    main()
