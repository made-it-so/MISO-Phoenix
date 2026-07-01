"""
MISO Swarm Orchestrator — 4-tier compute gradient router.

Tiers (in order of escalation):
  0  Machine code   — deterministic algorithms, regex, no LLM tokens consumed.
                      Callers handle Tier 0 themselves; this module starts at Tier 1.
  1  Local LLM      — Ollama. Code tasks try the code model first, then the reason
                      model. Zero cost per token. Most tasks should resolve here.
  2  Commercial LLM — Cheapest available commercial API (e.g. claude-haiku,
                      gemini-flash, gpt-3.5-turbo). Only fires if Tier 1 fails or
                      the caller explicitly requires it.
  3  Frontier LLM   — Most capable commercial API (e.g. claude-opus, gpt-4o,
                      gemini-ultra). Reserved for edge cases. Never the default.

Design rules (encoded in the MISO PRD):
  - No hardcoded model names. Every model reference comes from env vars.
  - Paid tokens are reserved for tasks local models cannot handle.
  - Over time, the Ollama tier should absorb tasks currently sent to commercial.
  - Code tasks: local code model → local reason model → commercial → frontier.
  - max_tier caps escalation. Default is Tier 1 (local only).
  - Callers must explicitly pass max_tier >= 2 to allow commercial API use.

Environment variables:
  OLLAMA_URL              Ollama base URL (default: http://localhost:11434)
  MISO_CODE_MODEL         Tier 1 code model  (default: qwen2.5-coder:3b)
  MISO_REASON_MODEL       Tier 1 reason model (default: llama3.1)
  MISO_FAST_MODEL         Tier 1 fast/triage model (default: same as reason)
  MISO_COMMERCIAL_MODEL   Tier 2 model ID recognised by the commercial provider
  MISO_COMMERCIAL_PROVIDER  "anthropic" | "openai" | "google" (default: anthropic)
  MISO_FRONTIER_MODEL     Tier 3 model ID
  MISO_FRONTIER_PROVIDER  "anthropic" | "openai" | "google" (default: anthropic)
  ANTHROPIC_API_KEY       Required for Anthropic tiers
  OPENAI_API_KEY          Required for OpenAI tiers
  GOOGLE_API_KEY          Required for Google tiers
"""
import os
import re
import requests
from miso_config import OLLAMA_URL, DEFAULT_MODEL

# ── Tier 1 model names from env (no hardcoded fallbacks beyond generic defaults) ──

_CODE_MODEL    = os.environ.get("MISO_CODE_MODEL",    "qwen2.5-coder:3b")
_REASON_MODEL  = os.environ.get("MISO_REASON_MODEL",  DEFAULT_MODEL)
_FAST_MODEL    = os.environ.get("MISO_FAST_MODEL",    DEFAULT_MODEL)

# ── Tier 2 / 3 — entirely from env; empty string = not configured ──

_COMMERCIAL_MODEL    = os.environ.get("MISO_COMMERCIAL_MODEL",    "").strip()
_COMMERCIAL_PROVIDER = os.environ.get("MISO_COMMERCIAL_PROVIDER", "anthropic").lower()
_FRONTIER_MODEL      = os.environ.get("MISO_FRONTIER_MODEL",      "").strip()
_FRONTIER_PROVIDER   = os.environ.get("MISO_FRONTIER_PROVIDER",   "anthropic").lower()

_available_models: set[str] | None = None  # lazy-cached Ollama model list


# ── Tier 1: Local Ollama ───────────────────────────────────────────────────────

def _get_available_models() -> set[str]:
    global _available_models
    if _available_models is not None:
        return _available_models
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        _available_models = {m["name"] for m in r.json().get("models", [])}
    except Exception:
        _available_models = {DEFAULT_MODEL}
    return _available_models


def _local_model_for(task_type: str, prompt: str) -> list[str]:
    """
    Return ordered list of Ollama models to try for this task.
    Code tasks: code model first, then reason model as fallback.
    """
    available = _get_available_models()

    def _pick(preferred: str) -> str | None:
        return preferred if preferred in available else None

    if task_type == "code":
        candidates = [_CODE_MODEL, _REASON_MODEL, DEFAULT_MODEL]
    elif task_type == "fast":
        candidates = [_FAST_MODEL, DEFAULT_MODEL]
    elif task_type == "dynamic":
        code_signals = {"write", "generate", "implement", "code", "function",
                        "class", "import", "def ", "python", "javascript", "refactor"}
        if any(s in prompt.lower() for s in code_signals):
            candidates = [_CODE_MODEL, _REASON_MODEL, DEFAULT_MODEL]
        else:
            candidates = [_REASON_MODEL, DEFAULT_MODEL]
    else:  # "reason" and anything else
        candidates = [_REASON_MODEL, DEFAULT_MODEL]

    # Deduplicate while preserving order; keep only models actually installed
    seen, ordered = set(), []
    for m in candidates:
        if m and m not in seen:
            seen.add(m)
            if _pick(m):
                ordered.append(m)
    return ordered or [DEFAULT_MODEL]


def _call_ollama(model: str, prompt: str, timeout: int) -> str | None:
    """
    Call a single Ollama model. Returns response text or None on failure.
    """
    try:
        r = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        r.raise_for_status()
        return r.json().get("response", "") or None
    except Exception:
        return None


def _try_tier1(task_type: str, prompt: str, timeout: int) -> str | None:
    """
    Try all applicable local models in order. Returns first successful response.
    """
    for model in _local_model_for(task_type, prompt):
        result = _call_ollama(model, prompt, timeout)
        if result:
            return result
    return None


# ── Tier 2 / 3: Commercial and Frontier APIs ──────────────────────────────────

def _call_api(model: str, provider: str, prompt: str, timeout: int,
              max_tokens: int = 1024) -> str | None:
    """
    Call a commercial or frontier API. Provider and model come entirely from env.
    Returns response text or None on failure.
    """
    if not model:
        return None  # not configured — skip this tier silently

    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            return None
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json={"model": model, "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"] or None
        except Exception:
            return None

    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            return None
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json={"model": model, "max_tokens": max_tokens,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"] or None
        except Exception:
            return None

    elif provider == "google":
        key = os.environ.get("GOOGLE_API_KEY", "").strip()
        if not key:
            return None
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=timeout,
            )
            r.raise_for_status()
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"] or None
        except Exception:
            return None

    return None


# ── Public interface ───────────────────────────────────────────────────────────

def call_model(task_type: str, prompt: str, priority: int = 1,
               timeout: int = 120, max_tier: int = 1,
               max_tokens: int = 1024) -> str:
    """
    Call the compute gradient. Tries tiers in order up to max_tier.

    Args:
        task_type:  "code" | "reason" | "fast" | "dynamic"
        prompt:     Full prompt string.
        priority:   1 = standard, 2 = low (doubles timeout tolerance).
        timeout:    Per-tier timeout in seconds (base; multiplied by priority).
        max_tier:   Maximum tier to attempt. Default 1 (local only).
                    Pass max_tier=2 to allow commercial API fallback.
                    Pass max_tier=3 to allow frontier API fallback.
        max_tokens: Token budget for commercial/frontier calls.

    Returns:
        Response text, or "ERROR: ..." string if all tiers exhausted.

    Tier escalation:
        Tier 1 (local)      — always attempted first
        Tier 2 (commercial) — only if Tier 1 fails AND max_tier >= 2
        Tier 3 (frontier)   — only if Tier 2 fails AND max_tier >= 3
    """
    t = timeout * max(priority, 1)

    # Tier 1 — local Ollama
    result = _try_tier1(task_type, prompt, t)
    if result:
        return result

    # Tier 2 — commercial (cheapest)
    if max_tier >= 2:
        result = _call_api(_COMMERCIAL_MODEL, _COMMERCIAL_PROVIDER,
                           prompt, t, max_tokens)
        if result:
            return result

    # Tier 3 — frontier (edge cases only)
    if max_tier >= 3:
        result = _call_api(_FRONTIER_MODEL, _FRONTIER_PROVIDER,
                           prompt, t, max_tokens)
        if result:
            return result

    # All tiers exhausted
    tiers_tried = ["Tier1(local)"]
    if max_tier >= 2:
        tiers_tried.append(f"Tier2({_COMMERCIAL_PROVIDER}/{_COMMERCIAL_MODEL or 'not configured'})")
    if max_tier >= 3:
        tiers_tried.append(f"Tier3({_FRONTIER_PROVIDER}/{_FRONTIER_MODEL or 'not configured'})")
    return f"ERROR: All tiers exhausted ({', '.join(tiers_tried)}). No response."


def call_code_then_escalate(prompt: str, cleanup_prompt: str | None = None,
                             timeout: int = 120) -> str:
    """
    The "Ollama codes, commercial cleans up" pattern.

    1. Local code model generates the initial implementation (Tier 1).
    2. If a cleanup_prompt is provided and Tier 1 succeeded, pass the output
       to the commercial tier for review/cleanup (Tier 2).
    3. Falls back gracefully if commercial tier is not configured.

    Args:
        prompt:         Code generation prompt for local model.
        cleanup_prompt: Optional cleanup/review prompt. If None, skips Tier 2.
                        Use "{code}" placeholder to inject Tier 1 output.
        timeout:        Per-tier timeout.

    Returns:
        Final response text (Tier 1 output if cleanup not configured/needed).
    """
    # Step 1: local code generation
    local_result = _try_tier1("code", prompt, timeout)
    if not local_result:
        # Local failed — escalate the original prompt directly to commercial
        return call_model("code", prompt, timeout=timeout, max_tier=2)

    # Step 2: optional commercial cleanup
    if cleanup_prompt and _COMMERCIAL_MODEL:
        review = cleanup_prompt.replace("{code}", local_result)
        cleaned = _call_api(_COMMERCIAL_MODEL, _COMMERCIAL_PROVIDER,
                            review, timeout)
        if cleaned:
            return cleaned

    return local_result


def invalidate_model_cache():
    """Call when Ollama models are added or removed at runtime."""
    global _available_models
    _available_models = None
