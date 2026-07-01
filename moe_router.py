"""
MISO MoE Router — Critic → Consultant → Actor PRD generation pipeline.

Extracted from miso_architecture.md and wired to miso_prd_store + miso_config.
Mount in main.py: app.include_router(router, prefix="/api/v3/moe")
"""
import io
import base64
from PIL import Image
import os
import sys
import json
import re
import tempfile
import shutil
import asyncio
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pypdf import PdfReader
import email
from email import policy

from miso_swarm_orchestrator import call_model
from miso_prd_store import create_bounty, get_bounty, get_bounty_log_path
from miso_config import BOUNTY_DB_PATH

router = APIRouter()


def extract_code(text, lang="json"):
    bt = chr(96) * 3
    pattern = f"{bt}(?:{lang})?\\s*(.*?){bt}"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else text.strip()


class ACCProtocol:
    def __init__(self):
        self.traces = []

    def log(self, role: str, msg: str):
        print(f"[{role}] {msg}")
        self.traces.append({"role": role.upper(), "msg": msg})


async def sanitize_and_process_uploads(files: Optional[List[UploadFile]], acc: ACCProtocol):
    if not files:
        return [], "", []
    uris = []
    warnings = []
    temp_dir = tempfile.mkdtemp(prefix="miso_uploads_")

    for file in files:
        if not file.filename:
            continue
        content = await file.read()
        filename = file.filename.lower()
        try:
            if filename.endswith(".pdf"):
                reader = PdfReader(io.BytesIO(content))
                text = "".join(page.extract_text() for page in reader.pages)
                out_path = os.path.join(temp_dir, file.filename + ".txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
                uris.append(out_path)
            elif filename.endswith(".eml"):
                msg = email.message_from_bytes(content, policy=policy.default)
                text = msg.get_body(preferencelist=("plain", "html")).get_content()
                out_path = os.path.join(temp_dir, file.filename + ".txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
                uris.append(out_path)
            elif filename.endswith((".txt", ".md", ".py", ".js", ".jsx", ".json", ".sh", ".html", ".css", ".csv")):
                text = content.decode("utf-8", errors="ignore")
                out_path = os.path.join(temp_dir, file.filename + ".txt")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(text)
                uris.append(out_path)
                acc.log("LIBRARIAN", f"Ingested raw source/text file: {filename}")
            elif filename.endswith((".doc", ".docx", ".xls", ".xlsx")):
                warnings.append(f"Proprietary binary detected ({filename}). Please convert to PDF or TXT.")
            elif filename.endswith((".png", ".jpg", ".jpeg", ".gif")):
                if len([u for u in uris if u.endswith(".jpg")]) >= 3:
                    warnings.append(f"Vision limit reached. Dropped {filename}.")
                    continue
                try:
                    image = Image.open(io.BytesIO(content))
                    if image.mode in ("RGBA", "P"):
                        image = image.convert("RGB")
                    image.thumbnail((800, 800))
                    out_path = os.path.join(temp_dir, f"vision_{len(uris)}.jpg")
                    image.save(out_path, "JPEG", quality=85)
                    uris.append(out_path)
                    acc.log("OPTIC NERVE", f"Compressed {filename} to 800x800 JPEG (Q85).")
                except Exception as img_err:
                    warnings.append(f"Failed to compress {filename}: {img_err}")
            else:
                out_path = os.path.join(temp_dir, file.filename)
                with open(out_path, "wb") as f:
                    f.write(content)
                uris.append(out_path)
        except Exception as e:
            acc.log("SYSTEM FAULT", f"Failed to sanitize {filename}: {e}")
            warnings.append(f"Failed to parse file: {filename}")

    if len(uris) > 5:
        warnings.append(f"Cognitive load high. Truncated {len(uris) - 5} files.")
        uris = uris[:5]

    return uris, "", warnings


def build_native_prompt(system_directive: str, user_input: str, uris: List[str], vision_text: str = "") -> str:
    prompt = f"{system_directive}\n\nINPUT:\n{user_input}"
    if vision_text:
        prompt += f"\n\n{vision_text}"
    if uris:
        prompt += "\n\n[ATTACHED SENSORY PAYLOAD URIS]:\n" + "\n".join(uris)
    return prompt


@router.post("/analyze-context")
async def analyze_context(intent: str = Form(...), files: Optional[List[UploadFile]] = File(None)):
    async def event_stream():
        acc = ACCProtocol()
        yield f":{' ' * 2048}\n\n"
        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'SYSTEM', 'msg': 'Sanitizing context vault and extracting text...'})}\n\n"

        uris, vision_text, warnings = await sanitize_and_process_uploads(files, acc)
        for w in warnings:
            yield f"data: {json.dumps({'status': 'warning', 'msg': w})}\n\n"

        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'CRITIC', 'msg': 'Auditing intent and identifying gaps...'})}\n\n"
        critic_sys = "You are the Sovereign Critic. Audit the intent for risks, missing architecture, and optimal paths. Provide a short bulleted response that includes warnings and suggestions for optimal, industry-standard approaches."
        critic_prompt = build_native_prompt(critic_sys, intent, uris, vision_text)

        task = asyncio.create_task(asyncio.to_thread(call_model, "dynamic", critic_prompt, 2))
        while not task.done():
            yield f"data: {json.dumps({'status': 'ping', 'msg': 'Critic is reasoning...'})}\n\n"
            await asyncio.sleep(4)
        critique = task.result()

        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'CONSULTANT', 'msg': 'Formulating scoping parameters...'})}\n\n"
        consult_sys = """You are a Sovereign OS Consultant. Engage the user. Generate exactly 2 clarifying questions based on the Critic's warnings and optimizations. Provide optimal suggestions as options.
        Add "allowMultiple": true if the options are composable (e.g., features, integrations). Add "allowMultiple": false if options are mutually exclusive (e.g., choosing a primary database).
        OUTPUT STRICTLY VALID JSON:
        {
          "intentType": "frontend",
          "questions": [
            {
              "question": "To optimize this, which integrations should we include? (Select all that apply)",
              "allowMultiple": true,
              "options": [{"label": "Auth0 (Recommended)"}, {"label": "Stripe"}]
            }
          ]
        }"""
        consult_input = f"USER INTENT: {intent}\n\nCRITIC FEEDBACK:\n{critique}"
        consult_prompt = build_native_prompt(consult_sys, consult_input, uris, vision_text)

        task = asyncio.create_task(asyncio.to_thread(call_model, "dynamic", consult_prompt, 2))
        while not task.done():
            yield f"data: {json.dumps({'status': 'ping', 'msg': 'Consultant finalizing parameters...'})}\n\n"
            await asyncio.sleep(4)
        raw_response = task.result()

        json_str = extract_code(raw_response, "json")
        try:
            final_dict = json.loads(json_str)
        except Exception:
            final_dict = {"intentType": "backend", "questions": [{"question": "Fallback Trigger?", "options": [{"label": "Manual"}, {"label": "Cron"}]}]}

        final_dict["acc_traces"] = acc.traces
        final_dict["warnings"] = warnings
        if uris:
            shutil.rmtree(os.path.dirname(uris[0]), ignore_errors=True)

        yield f"data: {json.dumps({'status': 'complete', 'payload': final_dict})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"})


@router.post("/synthesize-blueprint")
async def synthesize_blueprint(intent: str = Form(...), answers: str = Form(...),
                                files: Optional[List[UploadFile]] = File(None),
                                goal_id: Optional[str] = Form(None)):
    async def event_stream():
        acc = ACCProtocol()
        yield f":{' ' * 2048}\n\n"
        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'SYSTEM', 'msg': 'Initializing SSE Stream & Sanitizing Binaries...'})}\n\n"

        uris, vision_text, warnings = await sanitize_and_process_uploads(files, acc)
        for w in warnings:
            yield f"data: {json.dumps({'status': 'warning', 'msg': w})}\n\n"

        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'ACTOR', 'msg': 'Drafting initial JSON blueprint via Swarm Orchestrator...'})}\n\n"
        actor_sys = """You are a Sovereign OS System Architect. Generate a full technical Product Requirements Document. OUTPUT STRICTLY VALID JSON: {"architectureNodes": [{"id": 1, "type": "Agent", "title": "Node Name", "desc": "Desc", "status": "to_build"}], "narrative": "A cohesive executive summary.", "mechanics": ["1. Feature A", "2. Feature B"], "dependencies": [], "uiPrefs": {"theme": "light", "color": "slate", "radius": "rounded-none", "layout": "sidebar"}}"""
        actor_input = f"USER INTENT: {intent}\nUSER SCOPING ANSWERS: {answers}"

        task = asyncio.create_task(asyncio.to_thread(call_model, "dynamic", build_native_prompt(actor_sys, actor_input, uris, vision_text), 2))
        while not task.done():
            yield f"data: {json.dumps({'status': 'ping', 'msg': 'Actor is drafting PRD...'})}\n\n"
            await asyncio.sleep(4)
        draft_raw = task.result()
        draft_json = extract_code(draft_raw, "json")

        yield f"data: {json.dumps({'status': 'acc_log', 'role': 'CRITIC', 'msg': 'Auditing draft architecture...'})}\n\n"
        critic_sys = "You are the Sovereign Critic. Do NOT rewrite the code. 1. Verify JSON syntax. 2. Verify PRD formatting. If the 'mechanics' field is a lazy comma-separated string instead of a strictly enumerated list with newlines (\\n), YOU MUST FLAG IT AS A FATAL FORMATTING ERROR. Provide a bulleted list of flaws."

        task = asyncio.create_task(asyncio.to_thread(call_model, "dynamic", build_native_prompt(critic_sys, f"USER INTENT: {intent}\nDRAFT:\n{draft_json}", uris, vision_text), 2))
        while not task.done():
            yield f"data: {json.dumps({'status': 'ping', 'msg': 'Critic is verifying JSON...'})}\n\n"
            await asyncio.sleep(4)
        critique = task.result()

        verified_json = ""
        final_dict = {}
        bt = chr(96) * 3

        for attempt in range(1, 4):
            yield f"data: {json.dumps({'status': 'acc_log', 'role': 'CONSULTANT', 'msg': f'Applying architectural fixes (Synthesis Attempt {attempt}/3)...'})}\n\n"
            consult_sys = f"You are the Sovereign Consultant. Fix ALL flaws identified by the Critic. You must rewrite lazy strings into strictly numbered, newline-separated lists if requested. Enforce strict JSON syntax. OUTPUT ONLY JSON inside a {bt}json block."
            consult_input = f"USER INTENT: {intent}\nCRITIC FLAWS:\n{critique}\nDRAFT:\n{draft_json}"

            task = asyncio.create_task(asyncio.to_thread(call_model, "dynamic", build_native_prompt(consult_sys, consult_input, [], ""), 2))
            while not task.done():
                yield f"data: {json.dumps({'status': 'ping', 'msg': 'Consultant is correcting formatting...'})}\n\n"
                await asyncio.sleep(4)
            verified_raw = task.result()
            verified_json = extract_code(verified_raw, "json")

            try:
                final_dict = json.loads(verified_json)
                yield f"data: {json.dumps({'status': 'acc_log', 'role': 'SYSTEM', 'msg': 'JSON verified. Protocol complete.'})}\n\n"
                break
            except Exception as e:
                yield f"data: {json.dumps({'status': 'acc_log', 'role': 'CRITIC', 'msg': f'FATAL JSON ERROR: {str(e)}. Triggering Ouroboros loop...'})}\n\n"
                critique += f"\n\nFATAL JSON FORMATTING ERROR IN YOUR LAST ATTEMPT:\n{str(e)}\nYou MUST output valid JSON."

        if not final_dict:
            final_dict = {"error": "Failed to parse JSON after 3 Ouroboros attempts."}

        yield f"data: {json.dumps({'status': 'complete', 'payload': final_dict})}\n\n"
        if uris:
            shutil.rmtree(os.path.dirname(uris[0]), ignore_errors=True)

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"})


@router.post("/refine-idea")
async def refine_idea(text: str = Form(...), field_type: str = Form(...)):
    acc = ACCProtocol()
    critic_sys = "You are the Sovereign Critic. Identify vagueness, missing business logic. Do NOT rewrite it. Output a harsh critique."
    critic_input = f"The user has written a draft for a system's {field_type}.\nDRAFT:\n{text}"
    critique = await asyncio.to_thread(call_model, "dynamic", build_native_prompt(critic_sys, critic_input, [], ""), 2)

    consult_sys = f"You are the Sovereign Consultant. Rewrite the {field_type} to address all of the Critic's concerns. OUTPUT ONLY THE REFINED TEXT."
    consult_input = f"DRAFT {field_type.upper()}:\n{text}\nCRITIC FLAWS:\n{critique}"
    refined_text = await asyncio.to_thread(call_model, "dynamic", build_native_prompt(consult_sys, consult_input, [], ""), 2)

    return {"refined_text": refined_text.strip(), "critique": critique, "acc_traces": acc.traces}


@router.post("/deploy")
async def deploy_project(title: str = Form(...), narrative: str = Form(...),
                          blueprint: str = Form(...), goal_id: Optional[str] = Form(None)):
    """
    Queue a PRD as an OPEN bounty for the engineer daemon to pick up.
    goal_id links the bounty to an active Goal Kernel goal.
    """
    try:
        blueprint_dict = json.loads(blueprint) if isinstance(blueprint, str) else blueprint
    except Exception:
        blueprint_dict = {"raw": blueprint}

    bounty_id = create_bounty(
        title=title,
        description=narrative,
        prd_blueprint=blueprint_dict,
        goal_id=goal_id,
    )

    log_path = get_bounty_log_path(bounty_id)
    with open(log_path, "w") as f:
        f.write(f"[SYSTEM] Bounty #{bounty_id} queued. Awaiting Engineer Daemon...\n")

    return {"status": "success", "bounty_id": bounty_id}


@router.get("/stream-bounty/{bounty_id}")
async def stream_bounty_logs(bounty_id: int):
    async def log_generator():
        log_path = get_bounty_log_path(bounty_id)
        last_pos = 0
        yield f":{' ' * 2048}\n\n"

        while True:
            bounty = get_bounty(bounty_id)
            status = bounty["status"] if bounty else "OPEN"

            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    f.seek(last_pos)
                    lines = f.readlines()
                    last_pos = f.tell()
                    if lines:
                        for line in lines:
                            yield f"data: {json.dumps({'log': line.strip(), 'status': status})}\n\n"
                    else:
                        yield f"data: {json.dumps({'log': '', 'status': status, 'ping': True})}\n\n"
            else:
                yield f"data: {json.dumps({'log': '', 'status': status, 'ping': True})}\n\n"

            if status in ("COMPLETED", "FAILED"):
                yield f"data: {json.dumps({'log': '[SYSTEM] Handoff stream terminated.', 'status': status})}\n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(log_generator(), media_type="text/event-stream",
                             headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache", "Connection": "keep-alive"})
