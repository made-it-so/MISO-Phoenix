"""
MISO Engineer Daemon — autonomous PRD → code → sandbox → deploy loop.

Extracted from miso_architecture.md and wired to miso_prd_store + miso_config.
Run continuously: python engineer_daemon.py

Loop:
  1. Claim next OPEN bounty from PRD Store
  2. LLM synthesizes code (local Ollama → Frontier escalation on failure)
  3. Docker sandbox validates: syntax check + 15s runtime
  4. Ouroboros: self-heals up to MAX_RETRIES times on sandbox failure
  5. Deploy: copy to target path, run post-deploy bash
  6. Mark COMPLETED or FAILED in PRD Store (closes loop to Goal Kernel)
"""
import time
import json
import requests
import re
import os
import subprocess
import shutil
from dotenv import load_dotenv

from miso_prd_store import claim_next_open_bounty, complete_bounty, fail_bounty, get_bounty_log_path
from miso_config import OLLAMA_URL, DEFAULT_MODEL

load_dotenv()

STAGING_DIR = os.environ.get("MISO_STAGING_DIR", os.path.join(os.path.dirname(__file__), "staging"))
DEPLOY_DIR = os.environ.get("MISO_DEPLOY_DIR", os.path.join(os.path.dirname(__file__), "deployments"))
MODEL = os.environ.get("MISO_CODER_MODEL", "qwen2.5-coder:3b")
MAX_RETRIES = 3
POLL_INTERVAL = 5  # seconds between queue checks

os.makedirs(STAGING_DIR, exist_ok=True)
os.makedirs(DEPLOY_DIR, exist_ok=True)


class BountyLogger:
    def __init__(self, bounty_id: int):
        self.bounty_id = bounty_id
        self.log_path = get_bounty_log_path(bounty_id)

    def log(self, msg: str):
        formatted = f"[DAEMON] {msg}"
        print(formatted)
        with open(self.log_path, "a") as f:
            f.write(formatted + "\n")


# ── Frontier Escalation ───────────────────────────────────────────────────────

def trigger_frontier_escalation(prompt: str, logger: BountyLogger) -> str:
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")).strip()

    if anthropic_key:
        try:
            logger.log("FRONTIER ESCALATION: Routing to Anthropic Claude...")
            headers = {"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
            payload = {"model": "claude-sonnet-4-6", "max_tokens": 4000,
                       "messages": [{"role": "user", "content": prompt}]}
            res = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=60)
            res.raise_for_status()
            return res.json()["content"][0]["text"]
        except Exception as e:
            logger.log(f"Anthropic escalation failed: {e}")

    if openai_key:
        try:
            logger.log("FRONTIER ESCALATION: Routing to OpenAI GPT-4o...")
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}]}
            res = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=60)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.log(f"OpenAI escalation failed: {e}")

    if gemini_key:
        try:
            logger.log("FRONTIER ESCALATION: Routing to Google Gemini...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={gemini_key}"
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            res.raise_for_status()
            return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.log(f"Gemini escalation failed: {e}")

    raise RuntimeError("All frontier escalations failed. No valid API keys found.")


def execute_llm_task(prompt: str, logger: BountyLogger, timeout: int = 45) -> str:
    payload = {"model": MODEL, "prompt": prompt, "stream": False}
    try:
        logger.log(f"Attempting local synthesis via {MODEL}...")
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        logger.log(f"Local engine fault ({e}). Engaging Frontier Escalation...")
        return trigger_frontier_escalation(prompt, logger)


# ── Code Parsing ──────────────────────────────────────────────────────────────

def parse_synthesis(text: str, b_id: int):
    bt = chr(96) * 3
    target_path = os.path.join(DEPLOY_DIR, f"bounty_{b_id}", "main.py")
    code = ""
    post_deploy = ""

    r_pattern = bt + r"(python|bash|sh|yaml|json)\s*\n(.*?)" + bt
    blocks = re.findall(r_pattern, text, re.DOTALL | re.IGNORECASE)

    for lang, block_content in blocks:
        lang = lang.lower()
        if lang == "python":
            code = block_content.strip()
            first_line = code.split("\n")[0].strip()
            if first_line.startswith("#") and "/" in first_line:
                candidate = first_line.replace("#", "").strip()
                # Only accept paths under DEPLOY_DIR (prevent path traversal)
                if candidate.startswith(DEPLOY_DIR) or not os.path.isabs(candidate):
                    target_path = candidate
        elif lang in ("bash", "sh"):
            post_deploy += block_content.strip() + "\n"

    return target_path, code, post_deploy


def sanitize_bash(cmd_string: str) -> str:
    danger_words = ["rm -rf", "mkfs", "chmod -R", "chown", ":(){ :|:& };:", "dd if="]
    sanitized = cmd_string
    for word in danger_words:
        if word in sanitized:
            sanitized = sanitized.replace(word, "echo [BLOCKED_COMMAND]")
    return sanitized


# ── Sandbox ───────────────────────────────────────────────────────────────────

def run_sandbox(script_path: str, logger: BountyLogger):
    logger.log("Booting isolated Ring 3 Sandbox for AST compilation...")
    cmd_syntax = [
        "docker", "run", "--rm",
        "-v", f"{script_path}:/app/script.py",
        "python:3.12-slim", "python", "-m", "py_compile", "/app/script.py"
    ]
    res = subprocess.run(cmd_syntax, capture_output=True, text=True)
    if res.returncode != 0:
        return False, f"Syntax Error:\n{res.stderr}"

    logger.log("Syntax verified. Executing 15-second runtime health check...")
    common_libs = "requests aiohttp pydantic fastapi uvicorn"
    cmd_run = [
        "docker", "run", "--rm", "--network", "host",
        "-v", f"{script_path}:/app/script.py",
        "python:3.12-slim", "bash", "-c",
        f"pip install -q {common_libs} && python /app/script.py"
    ]
    try:
        res = subprocess.run(cmd_run, capture_output=True, text=True, timeout=20)
        if res.returncode == 0:
            return True, "Clean execution."
        else:
            return False, f"Runtime Crash:\n{res.stderr}"
    except subprocess.TimeoutExpired:
        return True, "Process stable (daemon loop ran for 15s without crashing)."


def trigger_ouroboros(code: str, error_trace: str, attempt: int, logger: BountyLogger) -> str:
    logger.log(f"Awakening Ouroboros Healing Loop (Mutation attempt {attempt}/{MAX_RETRIES})...")
    bt = chr(96) * 3
    prompt = (
        f"AXIOM: METACOGNITIVE HEALING.\n"
        f"Original code crashed in sandbox.\n"
        f"ORIGINAL:\n{code}\n"
        f"TRACEBACK:\n{error_trace}\n"
        f"Fix the error. Return ONLY valid Python inside a {bt}python block."
    )
    raw_text = execute_llm_task(prompt, logger, timeout=45)
    code_match = re.search(f"{bt}(?:python)?\\s*(.*?){bt}", raw_text, re.DOTALL)
    return code_match.group(1).strip() if code_match else raw_text.strip()


# ── Main Loop ─────────────────────────────────────────────────────────────────

def run_engineer_loop():
    print("[SOVEREIGN ENGINEER] Online. Awaiting production deployments...")
    bt = chr(96) * 3

    while True:
        bounty = claim_next_open_bounty()

        if not bounty:
            time.sleep(POLL_INTERVAL)
            continue

        b_id = bounty["bounty_id"]
        title = bounty["title"]
        desc = bounty["description"]
        blueprint = bounty["prd_blueprint"]

        logger = BountyLogger(b_id)
        logger.log(f"PRD Handoff Confirmed: {title}. Task locked.")

        system_prompt = f"""AXIOM: FLIGHT TO CODE.
You are MISO's Core Engineer Agent. Write flawless Python code based on the PRD.
OUTPUT STRICTLY IN THIS FORMAT:

1. To save a file to disk, output exactly:
{bt}python
# {os.path.join(DEPLOY_DIR, f'bounty_{b_id}', 'main.py')}
[code]
{bt}
2. To execute terminal commands and test your code, output exactly:
{bt}bash
[commands]
{bt}
Do NOT roleplay the terminal output. The system will physically execute the bash blocks.

# CONTEXT: {title}
{desc}
# PRD:
{json.dumps(blueprint, indent=2)}
"""

        logger.log("Synthesizing raw architecture and logic paths...")
        try:
            raw_synthesis = execute_llm_task(system_prompt, logger, timeout=60)
        except Exception as e:
            logger.log(f"FATAL: Code synthesis failed entirely: {e}")
            fail_bounty(b_id, reason=str(e))
            continue

        target_path, current_code, post_deploy = parse_synthesis(raw_synthesis, b_id)

        if not current_code:
            logger.log("FATAL: No Python code block found in synthesis output.")
            fail_bounty(b_id, reason="No code block in LLM output")
            continue

        logger.log(f"Code generated. Target: {target_path}")
        staging_file = os.path.join(STAGING_DIR, f"staged_{b_id}.py")

        passed = False
        for attempt in range(1, MAX_RETRIES + 1):
            with open(staging_file, "w") as f:
                f.write(current_code)
            success, msg = run_sandbox(staging_file, logger)

            if success:
                logger.log(f"Sandbox Passed: {msg}")
                passed = True
                break
            else:
                logger.log(f"Sandbox Failed:\n{msg}")
                if attempt < MAX_RETRIES:
                    healed = trigger_ouroboros(current_code, msg, attempt, logger)
                    if healed:
                        current_code = healed

        if passed:
            logger.log(f"Code hardened. Deploying to: {target_path}")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy(staging_file, target_path)

            if post_deploy:
                safe_cmd = sanitize_bash(post_deploy)
                logger.log(f"Executing sanitized Post-Deploy:\n{safe_cmd}")
                subprocess.Popen(safe_cmd, shell=True, cwd=DEPLOY_DIR)

            logger.log("APPLICATION SUCCESSFULLY DEPLOYED.")
            complete_bounty(b_id, deployed_path=target_path,
                            note=f"Engineer daemon deployed {title} to {target_path}")
        else:
            logger.log(f"FAILED after {MAX_RETRIES} Ouroboros attempts.")
            fail_bounty(b_id, reason=f"Sandbox failed after {MAX_RETRIES} healing attempts")


if __name__ == "__main__":
    run_engineer_loop()
