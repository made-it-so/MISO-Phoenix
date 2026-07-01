"""
MISO Swarm Orchestrator — model routing layer.

Routes LLM calls to the appropriate model based on task type and load.
Provides the `call_model(task_type, prompt, priority)` interface consumed
by moe_router.py and other agents.

Routing strategy:
  "code"     -> qwen2.5-coder (if available) else fallback
  "reason"   -> llama3 (default reasoning model)
  "dynamic"  -> picks based on prompt heuristics
  "fast"     -> smallest available model for low-latency tasks

Falls back to DEFAULT_MODEL if the preferred model is unavailable.
"""
import os
import re
import requests
from miso_config import OLLAMA_URL, DEFAULT_MODEL

# Model preferences per task type. Override via env vars.
MODEL_MAP = {
    "code": os.environ.get("MISO_CODE_MODEL", "qwen2.5-coder:3b"),
    "reason": os.environ.get("MISO_REASON_MODEL", DEFAULT_MODEL),
    "fast": os.environ.get("MISO_FAST_MODEL", DEFAULT_MODEL),
    "dynamic": None,  # resolved at runtime
}

_available_models: set[str] | None = None  # lazy-loaded cache


def _get_available_models() -> set[str]:
    global _available_models
    if _available_models is not None:
        return _available_models
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = {m["name"] for m in r.json().get("models", [])}
        _available_models = models
        return models
    except Exception:
        return {DEFAULT_MODEL}


def _resolve_model(task_type: str, prompt: str) -> str:
    available = _get_available_models()

    if task_type == "dynamic":
        # Heuristic: if prompt looks like code generation, use code model
        code_signals = ["write", "generate", "implement", "code", "function",
                        "class", "import", "def ", "python", "javascript"]
        prompt_lower = prompt.lower()
        if any(s in prompt_lower for s in code_signals):
            task_type = "code"
        else:
            task_type = "reason"

    preferred = MODEL_MAP.get(task_type, DEFAULT_MODEL)
    if preferred and preferred in available:
        return preferred

    # Fallback: use default model
    return DEFAULT_MODEL


def call_model(task_type: str, prompt: str, priority: int = 1, timeout: int = 120) -> str:
    """
    Call the appropriate LLM for the given task type.

    Args:
        task_type: "code" | "reason" | "fast" | "dynamic"
        prompt:    The full prompt string.
        priority:  1 = standard, 2 = low priority (longer timeout tolerance).
        timeout:   Request timeout in seconds.

    Returns:
        The model's response text, or an error string prefixed with "ERROR:".
    """
    model = _resolve_model(task_type, prompt)
    effective_timeout = timeout * priority  # Higher priority = allow more time

    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=effective_timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.exceptions.Timeout:
        return f"ERROR: Model {model} timed out after {effective_timeout}s."
    except requests.exceptions.RequestException as e:
        return f"ERROR: {type(e).__name__}: {e}"
    except (KeyError, ValueError) as e:
        return f"ERROR: Unexpected response shape: {e}"


def invalidate_model_cache():
    """Call this if models are added/removed from Ollama at runtime."""
    global _available_models
    _available_models = None
