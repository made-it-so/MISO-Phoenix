import os
import re
import json
import shlex
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
from openai import OpenAI
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold # 🚀 --- NEW IMPORT
import logging
import httpx # Import httpx for timeout handling with OpenAI client

# --- Logger Setup ---
logger = logging.getLogger("MisoEngine")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
# --- End Logger Setup ---

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extracts the first valid JSON object from a string,
    even if it's wrapped in markdown or has text before/after.
    """
    if not text:
        return None
    start_index = text.find('{')
    end_index = text.rfind('}')
    if start_index == -1 or end_index == -1 or end_index < start_index:
        logger.error(f"extract_json: Could not find valid JSON object brackets in text: {text[:200]}")
        return None
    json_str = text[start_index : end_index + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"extract_json: JSONDecodeError: {e} for string: {json_str[:200]}")
        try:
            # Attempt to fix common trailing comma issue
            json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
            return json.loads(json_str)
        except Exception as final_e:
            logger.error(f"extract_json: Final parsing attempt failed: {final_e}")
            return None

def run_shell(command: str, cwd: Path | str = ".") -> Tuple[bool, str, str]:
    """Runs a shell command and returns (success, stdout, stderr)."""
    try:
        env = os.environ.copy()
        if "MISO_ROOT" not in env:
            env["MISO_ROOT"] = str(Path(__file__).parent.parent.parent.resolve())

        process = subprocess.run(
            command, # PASS THE RAW COMMAND STRING
            cwd=cwd, 
            capture_output=True, 
            text=True, 
            timeout=60, 
            env=env,
            shell=True # ENABLE SHELL EXPANSION
        )
        
        success = process.returncode == 0
        return success, process.stdout.strip(), process.stderr.strip()
    except Exception as e:
        return False, "", f"Shell execution error: {e}"

def read_file(file_path: Path | str) -> str:
    """Reads a file and returns its content."""
    try:
        if isinstance(file_path, str): file_path = Path(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: File not found at {file_path}"
    except Exception as e:
        return f"ERROR: Could not read file: {e}"

def write_file(file_path: Path | str, content: str):
    """Writes content to a file."""
    try:
        if isinstance(file_path, str): file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"ERROR: Could not write file {file_path}: {e}")

def create_file(file_path: Path | str, content: str):
    """Creates a new file with content."""
    write_file(file_path, content)

def get_file_manifest(root_dir: Path) -> str:
    """Generates a JSON string of the file manifest, ignoring common junk."""
    ignore_dirs = {'.git', '__pycache__', 'venv', '.vscode', 'node_modules'}
    ignore_files = {'.gitignore', '.DS_Store'}
    manifest: List[str] = []
    for path in root_dir.rglob('*'):
        if path.is_file():
            if any(part in ignore_dirs for part in path.parts) or path.name in ignore_files:
                continue
            relative_path = path.relative_to(root_dir)
            manifest.append(str(relative_path.as_posix()))
    return json.dumps(manifest, indent=2)

MISO_ROOT_PATH = None
def get_project_root() -> Path:
    """Finds and returns the project root directory."""
    global MISO_ROOT_PATH
    if MISO_ROOT_PATH: return MISO_ROOT_PATH
    MISO_ROOT_PATH = Path(__file__).parent.parent.parent.resolve()
    logger.info(f"Project root set to: {MISO_ROOT_PATH}")
    return MISO_ROOT_PATH

def load_config() -> Dict[str, Any]:
    """Loads configuration. Stubbed for now."""
    logger.info("Loading config (stubbed)")
    return {"default_model": "models/gemini-pro-latest"}

# 🚀 --- MisoLLM Class (Thread-Safe Timeout + Safety Fix) --- 🚀
class MisoLLM:
    """
    LLM client supporting OpenAI, Google Gemini, and local OpenAI-compatible
    servers (like Ollama) for open-source models.
    """
    def __init__(self):
        # 1. OpenAI Client
        try:
            self.openai_client = OpenAI()
            logger.info("OpenAI client initialized successfully.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client (API key might be missing): {e}")
            self.openai_client = None

        # 2. Google Gemini Client
        try:
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            genai.configure(api_key=google_api_key)
            
            # 🚀 --- NEW: Define Safety Settings ---
            self.gemini_safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            # -------------------------------------
            
            logger.info("Google Gemini client configured successfully.")
            self._google_clients = {} # Cache Gemini models
        except Exception as e:
            logger.warning(f"Failed to configure Google Gemini client (API key might be missing or invalid): {e}")
            self._google_clients = None # Indicate Google client failed
            
        # 3. Local/Open-Source Client (Ollama, etc.)
        try:
            # We set a *connect* timeout, but the *read* timeout will be
            # set per-call in the chat() method.
            local_timeout = httpx.Timeout(60.0, connect=10.0)
            self.local_client = OpenAI(
                base_url=os.environ.get("OPENAI_API_BASE", "http://localhost:11434/v1"),
                api_key='ollama', # Required, but Ollama ignores it
                timeout=local_timeout,
            )
            logger.info(f"Local client initialized (Ollama/OpenAI-compatible) at {self.local_client.base_url}")
        except Exception as e:
            logger.warning(f"Failed to initialize Local client: {e}")
            self.local_client = None

    def _get_google_model(self, model_name: str):
        if self._google_clients is None: # Check if client failed init
            raise RuntimeError("Google Gemini client failed to initialize.")
        if model_name not in self._google_clients:
            logger.info(f"Initializing Google Gemini model: {model_name}")
            self._google_clients[model_name] = genai.GenerativeModel(model_name)
        return self._google_clients[model_name]

    def _convert_messages_to_gemini(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        gemini_messages = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "assistant":
                gemini_messages.append({'role': 'model', 'parts': [content]})
            elif role == "user":
                gemini_messages.append({'role': 'user', 'parts': [content]})
        return gemini_messages

    class LLMResponse:
        def __init__(self, content: Optional[str] = None, tool_calls: Optional[List[Any]] = None):
            self.content = content
            self.tool_calls = tool_calls

    def chat(self, model: str, messages: List[Dict[str, str]]) -> Any:
        """Performs a standard chat completion call using the specified model provider."""
        logger.debug(f"Chat request - Model: {model}, Messages Count: {len(messages)}")

        if "gemini" in model:
            if self._google_clients is None:
                return self.LLMResponse(content="Error: Google Gemini client not configured.")
            try:
                gemini_model = self._get_google_model(model)
                gemini_messages = self._convert_messages_to_gemini(messages)
                system_prompt = next((m.get("content") for m in messages if m.get("role") == "system"), "")
                if system_prompt:
                    if gemini_messages and gemini_messages[0]['role'] == 'user':
                        gemini_messages[0]['parts'].insert(0, system_prompt + "\n\n")
                    else:
                        gemini_messages.insert(0, {'role': 'user', 'parts': [system_prompt]})

                # 🚀 --- FIX: Pass safety_settings to the API call ---
                response = gemini_model.generate_content(
                    gemini_messages,
                    safety_settings=self.gemini_safety_settings
                )
                
                # Check for empty response *before* accessing .text
                if not response.candidates or not response.candidates[0].content.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                    logger.error(f"Error during Google Gemini 'chat': API returned no content. Finish Reason: {finish_reason}")
                    if "safety" in str(finish_reason).lower():
                         return self.LLMResponse(content="Error: Gemini API call blocked by safety settings.")
                    return self.LLMResponse(content=f"Error: Gemini API returned no content (Finish Reason: {finish_reason}).")

                response_content = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                return self.LLMResponse(content=response_content)
                # ----------------------------------------------------
            
            except ValueError as ve:
                # Catch the specific "Invalid operation" error
                logger.error(f"Error during Google Gemini 'chat': {ve}", exc_info=True)
                return self.LLMResponse(content=f"Error during Gemini API call: {ve}")
            except Exception as e:
                logger.error(f"Error during Google Gemini 'chat': {e}", exc_info=True)
                return self.LLMResponse(content=f"Error during Gemini API call: {e}")
        
        elif "ollama/" in model:
            if not self.local_client:
                return self.LLMResponse(content="Error: Local (Ollama) client not configured.")
            try:
                # --- ROBUST TIMEOUT FIX (Working) ---
                local_model_name = model.split('ollama/')[-1]
                response = self.local_client.chat.completions.create(
                    model=local_model_name,
                    messages=messages, 
                    timeout=90.0 # This is the thread-safe, 90-second timeout
                )
                return response.choices[0].message
            except Exception as e:
                if "Timeout" in str(e) or "timed out" in str(e).lower():
                    logger.error(f"Error in Local (Ollama) 'chat': TIMEOUT (90s)")
                    raise TimeoutError("Ollama local client timed out after 90 seconds")
                logger.error(f"Error in Local (Ollama) 'chat': {e}")
                return self.LLMResponse(content=f"Error during Local API call: {e}")
            # --- END FIX ---

        elif "gpt" in model:
            if not self.openai_client:
                return self.LLMResponse(content="Error: OpenAI client not configured.")
            try:
                valid_messages = [{"role": m["role"], "content": m["content"]} for m in messages if isinstance(m, dict) and "role" in m and "content" in m and m["role"] != "tool"]
                response = self.openai_client.chat.completions.create(
                    model=model, messages=valid_messages
                )
                return response.choices[0].message
            except Exception as e:
                logger.error(f"Error in OpenAI 'chat': {e}")
                return self.LLMResponse(content=f"Error during OpenAI API call: {e}")
        else:
            logger.error(f"Unsupported model specified: {model}")
            return self.LLMResponse(content=f"Error: Unsupported model type: {model}")

    def chat_with_tools(self, model: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]]) -> Tuple[Any, Optional[List[Any]]]:
        logger.warning(f"chat_with_tools called for {model}, but falling back to standard text chat.")
        resp = self.chat(model, messages) # Use our standard chat method
        return resp, None

# --- Archivist Query Stub ---
def query_development_logs(query_text: str) -> str:
    """Placeholder for RAG."""
    logger.info(f"Querying development logs for: '{query_text[:100]}...'")
    return "<HISTORICAL_CONTEXT>\nNo specific historical context found.\n</HISTORICAL_CONTEXT>"

# --- Mypy Output Parser ---
def parse_mypy_output(mypy_output: str) -> List[Dict[str, Any]] | str:
    errors: List[Dict[str, Any]] = []
    line_error_pattern = re.compile(
        r"^(?P<file_path>[^:]+):(?P<line>\d+): (?P<level>error|note): (?P<message>.*?)(?: \[(?P<code>[^\]]+)\])?$"
    )
    module_error_pattern = re.compile(
        r"^(?P<file_path>[^:]+): (?P<level>error|note): (?P<message>.*?)(?: \[(?P<code>[^\]]+)\])?$"
    )
    lines = mypy_output.strip().split('\n')
    if "Success: no issues found" in mypy_output: 
        return "SUCCESS"
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Fallback:") or line.startswith("REFINEMENT:"):
            continue 
        match = line_error_pattern.match(line)
        if match:
            error_dict = match.groupdict()
            error_dict['line'] = int(error_dict['line'])
            if error_dict.get('code') is None: error_dict.pop('code', None)
            errors.append(error_dict)
            continue
        match = module_error_pattern.match(line)
        if match:
            error_dict = match.groupdict()
            error_dict['line'] = 1 
            if error_dict.get('code') is None: error_dict.pop('code', None)
            errors.append(error_dict)
    if not errors and mypy_output and "Success: no issues found" not in mypy_output:
        logger.warning(f"Mypy output was non-empty but no errors were parsed: {mypy_output[:200]}")
        return [{"level": "error", "message": "Failed to parse mypy output structure.", "raw_output": mypy_output[:500]}]
    return errors

# --- Ruff Output Parser ---
def parse_ruff_output(ruff_output: str) -> List[Dict[str, Any]] | str:
    errors: List[Dict[str, Any]] = []
    error_pattern = re.compile(
        r"^(?P<file_path>[^:]+):(?P<line>\d+):(?P<col>\d+): (?P<code>[A-Z]+\d+) (?:\[\*\] )?(?P<message>.*)$"
    )
    lines = ruff_output.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line or line.startswith("Found ") or line.startswith("No errors found"):
            continue
        match = error_pattern.match(line)
        if match:
            error_dict = match.groupdict()
            error_dict['line'] = int(error_dict['line'])
            error_dict['col'] = int(error_dict['col'])
            errors.append(error_dict)
    if not errors and ruff_output and "No errors found" not in ruff_output:
        logger.warning(f"Ruff output was non-empty but no errors were parsed: {ruff_output[:200]}")
        return [{"level": "error", "message": "Failed to parse ruff output structure.", "raw_output": ruff_output[:500]}]
    if not errors:
        return "SUCCESS"
    return errors
