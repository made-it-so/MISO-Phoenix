"""
Multimodal Ingest Agent

Accepts:
  - Code files / ZIP codebase -> analysis + World Model proposals + tasks + Agent Forge detection
  - Images (screenshots, dashboards) -> description + generate-ready spec

After code analysis the results flow automatically:
  1. Key facts proposed to World Model (pending human approval)
  2. Issues/improvements surfaced as tasks in the dashboard roadmap
  3. If code is a MISO-compatible agent, an Agent Forge install link is returned
"""
import asyncio
import base64
import io
import json
import os
import re
import time
import urllib.request as _ur
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter()

_MAX_CODE_BYTES  = 512 * 1024
_MAX_TOTAL_BYTES = 2 * 1024 * 1024
_MAX_IMAGE_BYTES = 4 * 1024 * 1024

_ALLOWED_CODE_EXTS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
    '.json', '.yaml', '.yml', '.md', '.txt', '.sql',
    '.sh', '.bash', '.dockerfile', '.go', '.rs', '.toml',
}
_IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}


# -- Static helpers -----------------------------------------------------------

def _ext_to_lang(ext: str) -> str:
    return {
        '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
        '.jsx': 'React JSX', '.tsx': 'React TSX', '.html': 'HTML',
        '.css': 'CSS', '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML',
        '.md': 'Markdown', '.sql': 'SQL', '.sh': 'Shell', '.bash': 'Bash',
        '.go': 'Go', '.rs': 'Rust', '.dockerfile': 'Dockerfile', '.toml': 'TOML',
    }.get(ext, 'plaintext')


def _quick_code_stats(content: str, filename: str) -> dict:
    lines = content.splitlines()
    non_blank = [l for l in lines if l.strip()]
    comment_chars = {'#', '//', '--', '/*', '*'}
    comment_lines = [l for l in non_blank if any(l.lstrip().startswith(c) for c in comment_chars)]
    return {
        "total_lines":     len(lines),
        "non_blank_lines": len(non_blank),
        "comment_lines":   len(comment_lines),
        "language":        _ext_to_lang(Path(filename).suffix.lower()),
        "size_bytes":      len(content.encode()),
    }


def _is_agent_compatible(code: str) -> bool:
    return bool(
        re.search(r'router\s*=\s*APIRouter\(\)', code)
        and re.search(r'@router\.(get|post)\s*\(\s*["\']/?health', code)
    )


# -- LLM prompts --------------------------------------------------------------

def _build_code_prompt(label: str, content: str, intent: Optional[str], is_codebase: bool = False) -> str:
    scope = "codebase" if is_codebase else "file"
    stats_lines = []
    if not is_codebase:
        stats = _quick_code_stats(content, label)
        stats_lines = [
            f"Language: {stats['language']}",
            f"Lines: {stats['total_lines']} ({stats['non_blank_lines']} non-blank)",
        ]
    snippet = content[:8000] + ("\n\n... [truncated]" if len(content) > 8000 else "")
    task = intent or f"Perform a thorough {scope} review."
    stats_block = "\n".join(stats_lines)

    return (
        f"You are reviewing uploaded code. Task: {task}\n\n"
        f"{scope.capitalize()}: {label}\n"
        f"{stats_block}\n\n"
        f"Code:\n```\n{snippet}\n```\n\n"
        'Return ONLY valid JSON:\n'
        '{\n'
        '  "summary": "2-4 sentence description",\n'
        '  "purpose": "single sentence: what problem this solves",\n'
        '  "tech_stack": ["languages, frameworks, key libraries"],\n'
        '  "issues": [{"severity": "high|medium|low", "description": "...", "suggestion": "..."}],\n'
        '  "improvements": ["concrete improvement suggestion"],\n'
        '  "notable_patterns": ["pattern or architectural decision"],\n'
        '  "is_agent": false,\n'
        '  "agent_name": null,\n'
        '  "world_model_facts": [{"attribute": "property", "value": "value", "confidence": 0.8}],\n'
        '  "tasks": [{"title": "short title", "description": "what and why", "priority": 5,\n'
        '    "vector": "resource_efficiency|autodidacticism|self_healing|macro_architecture|micro_quality"}],\n'
        '  "generate_prompt": "instruction to regenerate this as a MISO app"\n'
        '}\n\n'
        'Rules: world_model_facts=3-8 facts; tasks=real actionable issues only (high=8-10,mid=4-7,low=1-3);\n'
        'is_agent=true if FastAPI/Flask service that could run standalone.'
    )


def _build_image_prompt(intent: Optional[str]) -> str:
    task = intent or "Describe this UI/dashboard. Extract all visible components, layout, and data being shown."
    return (
        f"You are analyzing an uploaded image. Task: {task}\n\n"
        "Respond with valid JSON only:\n"
        "{\n"
        '  "type": "dashboard|form|chart|diagram|screenshot|photo|other",\n'
        '  "description": "2-3 sentence description of what you see",\n'
        '  "components": ["component 1"],\n'
        '  "data_shown": ["data element 1"],\n'
        '  "layout": "brief layout description",\n'
        '  "color_scheme": "colors used",\n'
        '  "generate_prompt": "specific MISO instruction to recreate this as a dark-theme React app"\n'
        "}"
    )


# -- LLM caller ---------------------------------------------------------------

async def _run_llm(prompt: str, image_b64: Optional[str] = None, mime: Optional[str] = None) -> dict:
    from engine.manifold_engine import ComputeManifold

    manifold = ComputeManifold()

    if image_b64:
        import anthropic
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise HTTPException(503, "ANTHROPIC_API_KEY not set - vision requires Anthropic Claude")
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime or "image/png", "data": image_b64}},
                {"type": "text", "text": prompt},
            ]}],
        )
        raw = msg.content[0].text
        cost = (msg.usage.input_tokens * 0.00025 + msg.usage.output_tokens * 0.00125) / 1000
        provider = "anthropic"
    else:
        result = await manifold.execute_with_escalation(
            prompt=prompt, mode="structured_extract",
        )
        if not result.get("success"):
            raise HTTPException(503, result.get("errors", ["LLM unavailable"])[0])
        raw = result["payload"]
        cost = result.get("cost_usd", 0)
        provider = result.get("provider", "")

    parsed = None
    try:
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            parsed = json.loads(m.group())
    except Exception:
        pass

    return {"raw": raw, "parsed": parsed, "cost_usd": cost, "provider": provider}


# -- Chunked parallel analysis ------------------------------------------------

_FILE_CHUNK_PROMPT = (
    "Analyse this single file briefly. Return ONLY valid JSON:\n"
    '{{\n'
    '  "purpose": "one sentence: what this file does",\n'
    '  "tech": ["languages, frameworks, key libs"],\n'
    '  "issues": [{{"severity": "high|medium|low", "description": "issue", "suggestion": "fix"}}],\n'
    '  "notable": ["key pattern or architectural decision"]\n'
    '}}\n\n'
    "File: {fname}\n```\n{snippet}\n```"
)


async def _analyze_file_chunk(fname: str, content: str) -> dict:
    """Analyze one file in isolation. Never raises."""
    snippet = content[:8000] + ("\n... [truncated]" if len(content) > 8000 else "")
    prompt = _FILE_CHUNK_PROMPT.format(fname=fname, snippet=snippet)
    try:
        llm = await _run_llm(prompt)
        return {"fname": fname, "result": llm.get("parsed") or {}, "cost": llm.get("cost_usd", 0), "provider": llm.get("provider", "")}
    except Exception as e:
        return {"fname": fname, "result": {}, "error": str(e), "cost": 0}


def _build_synthesis_prompt(label: str, chunk_results: list, intent: Optional[str], is_codebase: bool) -> str:
    parts = []
    for cr in chunk_results:
        r = cr.get("result", {})
        parts.append(
            f"- {cr['fname']}: {r.get('purpose', '?')} | "
            f"tech: {r.get('tech', [])} | issues: {len(r.get('issues', []))}"
        )
    files_summary = "\n".join(parts)

    all_issues = []
    for cr in chunk_results:
        for issue in cr.get("result", {}).get("issues", []):
            all_issues.append({**issue, "file": cr["fname"]})

    scope = "codebase" if is_codebase else "upload"
    task = intent or f"Thorough {scope} review."

    return (
        f'Synthesize per-file analyses for "{label}" into a unified assessment.\n'
        f"Task: {task}\n\n"
        f"Per-file summaries:\n{files_summary}\n\n"
        f"All detected issues ({len(all_issues)} total):\n"
        f"{json.dumps(all_issues[:20], indent=2)}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "summary": "2-4 sentence overall description",\n'
        '  "purpose": "one sentence: what problem this solves",\n'
        '  "tech_stack": ["all tech detected across files"],\n'
        '  "issues": [{"severity": "high|medium|low", "description": "...", "suggestion": "...", "file": "filename"}],\n'
        '  "improvements": ["improvement suggestion"],\n'
        '  "notable_patterns": ["architectural pattern or decision"],\n'
        '  "is_agent": false,\n'
        '  "agent_name": null,\n'
        '  "world_model_facts": [{"attribute": "property", "value": "value", "confidence": 0.8}],\n'
        '  "tasks": [{"title": "short title", "description": "what and why", "priority": 5,\n'
        '    "vector": "resource_efficiency|autodidacticism|self_healing|macro_architecture|micro_quality"}],\n'
        '  "generate_prompt": "instruction to regenerate this as a MISO app"\n'
        "}"
    )


def _build_drop_synthesis_prompt(label: str, chunk_results: list, intent: Optional[str]) -> str:
    parts = [f"- {cr['fname']}: {cr.get('result', {}).get('purpose', '?')}" for cr in chunk_results]
    files_summary = "\n".join(parts)
    task = intent or "general understanding"

    return (
        f'Synthesize these file analyses for "{label}" into a friendly, jargon-free summary.\n'
        f"Task: {task}\n\n"
        f"Files analyzed:\n{files_summary}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "plain_summary": "2-3 friendly sentences suitable for someone non-technical",\n'
        '  "what_it_does": "one sentence: the core purpose",\n'
        '  "interesting_things": ["up to 4 interesting observations a non-expert would care about"],\n'
        '  "tech_stack": ["technologies detected"],\n'
        '  "world_model_facts": [{"entity": "name", "attribute": "key", "value": "val", "evidence_level": "D"}],\n'
        '  "suggested_next_steps": ["1-3 concrete things the user could do next"],\n'
        '  "is_agent": false,\n'
        '  "agent_name": null\n'
        "}"
    )


# -- Post-analysis pipeline ---------------------------------------------------

def _propose_world_model_facts(facts: list, entity_name: str, source: str) -> list:
    results = []
    for fact in facts[:10]:
        attr  = str(fact.get("attribute", ""))[:80]
        value = str(fact.get("value", ""))[:200]
        conf  = float(fact.get("confidence", 0.7))
        if not attr or not value:
            continue
        try:
            payload = json.dumps({
                "entity_name": entity_name[:80], "attribute": attr, "value": value,
                "source": source, "confidence": round(min(max(conf, 0.0), 1.0), 2),
                "proposed_by": "multimodal_ingest",
            }).encode()
            req = _ur.Request(
                "http://localhost:8000/apps/world_model_agent/facts/propose",
                data=payload, headers={"Content-Type": "application/json"}, method="POST"
            )
            with _ur.urlopen(req, timeout=5) as r:
                resp = json.loads(r.read())
                results.append({"attribute": attr, "value": value, "id": resp.get("id"),
                                 "contradictions": len(resp.get("contradictions", []))})
        except Exception as e:
            results.append({"attribute": attr, "value": value, "error": str(e)})
    return results


def _create_tasks(tasks: list, source_label: str) -> list:
    _VALID_VECTORS = {"resource_efficiency", "autodidacticism", "self_healing", "macro_architecture", "micro_quality"}
    results = []
    for t in tasks[:8]:
        title    = str(t.get("title", ""))[:100].strip()
        desc     = str(t.get("description", ""))[:1000].strip()
        priority = max(1, min(10, int(t.get("priority", 5))))
        vector   = t.get("vector", "micro_quality")
        if not title or len(title) < 3:
            continue
        if len(desc) < 10:
            desc = f"From analysis of {source_label}: {title}"
        if vector not in _VALID_VECTORS:
            vector = "micro_quality"
        try:
            payload = json.dumps({
                "title": f"[{source_label}] {title}"[:100],
                "description": desc, "priority": priority, "vector": vector,
            }).encode()
            req = _ur.Request(
                "http://localhost:8000/api/tasks",
                data=payload, headers={"Content-Type": "application/json"}, method="POST"
            )
            with _ur.urlopen(req, timeout=5) as r:
                resp = json.loads(r.read())
                results.append({"title": title, "priority": priority, "vector": vector, "task_id": resp.get("task_id")})
        except Exception as e:
            results.append({"title": title, "error": str(e)})
    return results


def _forge_candidate(analysis: dict, all_files: dict) -> Optional[dict]:
    if not analysis.get("is_agent"):
        return None
    agent_name = analysis.get("agent_name") or "external_agent"
    main_code  = all_files.get("main.py", next(iter(all_files.values()), ""))
    already_ok = _is_agent_compatible(main_code)
    return {
        "detected": True, "suggested_name": agent_name, "already_compatible": already_ok,
        "install_hint": (
            "Code has router = APIRouter() + /health - can be installed directly with auto_approve=true"
            if already_ok else
            "MISO will generate a FastAPI adapter - review before approving"
        ),
        "forge_register_url": "http://localhost:8000/apps/agent_forge/register",
    }


def _build_downstream_payload(analysis: dict, entity_name: str, source_label: str, all_files: dict) -> dict:
    return {
        "world_model_proposals": _propose_world_model_facts(analysis.get("world_model_facts", []), entity_name, source_label),
        "tasks_created":         _create_tasks(analysis.get("tasks", []), source_label),
        "agent_candidate":       _forge_candidate(analysis, all_files),
    }


# -- Cross-agent notification -------------------------------------------------

def _notify_consigliere(alert: dict):
    """Fire-and-forget: POST alert into the Consigliere SSE stream."""
    try:
        payload = json.dumps(alert).encode()
        req = _ur.Request(
            "http://localhost:8000/apps/consigliere_agent/push",
            data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        with _ur.urlopen(req, timeout=5) as _r:
            pass
    except Exception:
        pass


# -- Background analysis tasks ------------------------------------------------

async def _run_codebase_bg(job_id: str, all_files: dict, ordered: list,
                            label: str, entity_name: str, intent: Optional[str]):
    """Analyze codebase in background, push SSE notification when done."""
    try:
        chunk_results = await asyncio.gather(*[
            _analyze_file_chunk(fname, all_files[fname]) for fname in ordered[:20]
        ])
        chunk_cost = sum(cr.get("cost", 0) for cr in chunk_results)
        synth_llm  = await _run_llm(_build_synthesis_prompt(label, list(chunk_results), intent, is_codebase=True))
        analysis   = synth_llm.get("parsed") or {}
        downstream = _build_downstream_payload(analysis, entity_name, label, all_files)
        issues      = analysis.get("issues", [])
        high_issues = [i for i in issues if i.get("severity") == "high"]
        tech        = ", ".join(analysis.get("tech_stack", [])[:6])
        tasks_made  = len(downstream.get("tasks_created", []))
        summary_parts = []
        if analysis.get("purpose"):   summary_parts.append(analysis["purpose"])
        if tech:                       summary_parts.append(f"Stack: {tech}.")
        if high_issues:                summary_parts.append(f"{len(high_issues)} high-severity issue(s) found.")
        if tasks_made:                 summary_parts.append(f"{tasks_made} task(s) added to roadmap.")
        _notify_consigliere({
            "type":            "ingest_complete",
            "title":           f'Analysis complete: "{label}"',
            "body":            " ".join(summary_parts) or "Codebase analyzed.",
            "job_id":          job_id,
            "generate_prompt": analysis.get("generate_prompt", ""),
            "label":           label,
            "file_count":      len(all_files),
        })
    except Exception as exc:
        _notify_consigliere({
            "type":   "ingest_error",
            "title":  f'Analysis failed: "{label}"',
            "body":   str(exc)[:200],
            "job_id": job_id,
        })


async def _run_drop_bg(job_id: str, text_files: dict, image_files: list,
                       label: str, intent: Optional[str]):
    """Analyze drop upload in background, push SSE notification when done."""
    try:
        analysis_result: dict = {}

        if text_files:
            ordered = sorted(text_files.keys(), key=lambda f: (f not in ("README.md", "readme.txt", "main.py"), f))
            chunk_results = await asyncio.gather(*[
                _analyze_file_chunk(fname, text_files[fname]) for fname in ordered[:20]
            ])
            synth_llm       = await _run_llm(_build_drop_synthesis_prompt(label, list(chunk_results), intent))
            analysis_result = synth_llm.get("parsed") or {}
            entity_name = re.sub(r'[^a-z0-9_]', '_', label.lower())[:40] or "upload"
            _propose_world_model_facts(analysis_result.get("world_model_facts", []), entity_name, f"drop/{label}")
            _create_tasks(
                [{"title": s, "vector": "macro_architecture", "priority": 5}
                 for s in analysis_result.get("suggested_next_steps", [])],
                f"drop/{label}",
            )

        if image_files:
            async def _analyze_image_bg(img: dict) -> str:
                try:
                    llm = await _run_llm(
                        f"Describe this image in 2-3 plain sentences. Goal: {intent or 'understand what this shows'}",
                        image_b64=img["b64"], mime=img["mime"]
                    )
                    return f"{img['name']}: {llm.get('raw', '')[:300]}"
                except Exception:
                    return f"{img['name']}: (analysis failed)"
            await asyncio.gather(*[_analyze_image_bg(img) for img in image_files[:3]])

        steps = analysis_result.get("suggested_next_steps", [])
        _notify_consigliere({
            "type":            "ingest_complete",
            "title":           f'Analysis complete: "{label}"',
            "body":            analysis_result.get("plain_summary") or analysis_result.get("what_it_does") or "Files analyzed.",
            "job_id":          job_id,
            "generate_prompt": steps[0] if steps else "",
            "label":           label,
        })
    except Exception as exc:
        _notify_consigliere({
            "type":   "ingest_error",
            "title":  f'Analysis failed: "{label}"',
            "body":   str(exc)[:200],
            "job_id": job_id,
        })


# -- Endpoints ----------------------------------------------------------------

@router.post("/code")
async def ingest_code(
    file:   UploadFile = File(...),
    intent: Optional[str] = Form(None),
):
    """Upload a single code file for analysis."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_CODE_EXTS:
        raise HTTPException(400, f"Unsupported type '{ext}'. Allowed: {sorted(_ALLOWED_CODE_EXTS)}")
    raw_bytes = await file.read()
    if len(raw_bytes) > _MAX_CODE_BYTES:
        raise HTTPException(413, f"File too large ({len(raw_bytes)//1024} KB). Max: {_MAX_CODE_BYTES//1024} KB")

    content = raw_bytes.decode("utf-8", errors="replace")
    stats   = _quick_code_stats(content, file.filename)
    llm     = await _run_llm(_build_code_prompt(file.filename, content, intent))
    analysis   = llm["parsed"] or {}
    downstream = _build_downstream_payload(analysis, Path(file.filename).stem, file.filename, {file.filename: content})

    return {
        "id": str(uuid.uuid4())[:8], "type": "code", "filename": file.filename,
        "stats": stats, "analysis": analysis,
        "raw_llm": llm["raw"][:500] if not analysis else None,
        "cost_usd": llm["cost_usd"], "provider": llm["provider"],
        "timestamp": time.time(), **downstream,
    }


@router.post("/codebase")
async def ingest_codebase(
    files:  list[UploadFile] = File(...),
    name:   Optional[str]    = Form(None),
    intent: Optional[str]    = Form(None),
):
    """
    Upload a full codebase as multiple files or a single .zip.
    Each file is analyzed in parallel; a synthesis pass produces the unified assessment.
    """
    all_files: dict[str, str] = {}
    total_bytes = 0

    for upload in files:
        raw = await upload.read()
        total_bytes += len(raw)
        if total_bytes > _MAX_TOTAL_BYTES:
            raise HTTPException(413, f"Total upload exceeds {_MAX_TOTAL_BYTES//1024} KB")
        fname = upload.filename or "unknown"
        if fname.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                for member in zf.namelist():
                    ext = Path(member).suffix.lower()
                    if ext in _ALLOWED_CODE_EXTS and not Path(member).name.startswith("."):
                        try:
                            all_files[member] = zf.read(member).decode("utf-8", errors="replace")
                        except Exception:
                            pass
        else:
            ext = Path(fname).suffix.lower()
            if ext in _ALLOWED_CODE_EXTS:
                all_files[fname] = raw.decode("utf-8", errors="replace")

    if not all_files:
        raise HTTPException(400, "No supported code files found in upload")

    ordered     = sorted(all_files.keys(), key=lambda f: (f not in ("main.py", "app.py"), f))
    label       = name or (Path(ordered[0]).parent.name or Path(ordered[0]).stem)
    entity_name = re.sub(r'[^a-z0-9_]', '_', label.lower())[:40] or "codebase"
    total_lines = sum(len(c.splitlines()) for c in all_files.values())
    languages   = list({_ext_to_lang(Path(f).suffix.lower()) for f in all_files})

    job_id = str(uuid.uuid4())[:8]
    asyncio.create_task(_run_codebase_bg(job_id, all_files, ordered, label, entity_name, intent))

    return JSONResponse({
        "id": job_id, "status": "processing", "type": "codebase",
        "name": label, "file_count": len(all_files),
        "files": list(all_files.keys())[:10],
        "total_lines": total_lines, "languages": languages,
        "message": "Analysis running in background. You will be notified when complete.",
        "timestamp": time.time(),
    })


@router.post("/image")
async def ingest_image(
    file:   UploadFile = File(...),
    intent: Optional[str] = Form(None),
):
    """Upload a screenshot or dashboard image to extract a replication spec."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _IMAGE_EXTS:
        raise HTTPException(400, f"Unsupported image type '{ext}'. Allowed: {sorted(_IMAGE_EXTS)}")
    raw_bytes = await file.read()
    if len(raw_bytes) > _MAX_IMAGE_BYTES:
        raise HTTPException(413, f"Image too large ({len(raw_bytes)//1024} KB). Max: {_MAX_IMAGE_BYTES//1024} KB")

    mime = "image/png"
    if raw_bytes[:3] == b'\xff\xd8\xff':                         mime = "image/jpeg"
    elif raw_bytes[:4] == b'GIF8':                               mime = "image/gif"
    elif raw_bytes[:4] == b'RIFF' and raw_bytes[8:12] == b'WEBP': mime = "image/webp"

    b64 = base64.standard_b64encode(raw_bytes).decode()
    llm = await _run_llm(_build_image_prompt(intent), image_b64=b64, mime=mime)

    return {
        "id": str(uuid.uuid4())[:8], "type": "image", "filename": file.filename,
        "mime": mime, "size_kb": len(raw_bytes) // 1024,
        "analysis": llm["parsed"], "raw_llm": llm["raw"][:500] if not llm["parsed"] else None,
        "cost_usd": llm["cost_usd"], "provider": llm["provider"], "timestamp": time.time(),
    }


_MAX_DROP_BYTES = 25 * 1024 * 1024

_READABLE_EXTS = _ALLOWED_CODE_EXTS | {
    '.pdf', '.csv', '.tsv', '.log', '.cfg', '.ini', '.env',
    '.xml', '.svg', '.rst', '.tex', '.rtf',
}


@router.post("/drop")
async def drop_anything(
    files: list[UploadFile] = File(...),
    intent: Optional[str]   = Form(None),
    name:   Optional[str]   = Form(None),
):
    """
    General-purpose ingest for the dashboard import UI.
    ZIP archives, code/text files, and images up to 25 MB.
    Files analyzed in parallel; synthesis produces a plain-English summary.
    """
    text_files: dict[str, str] = {}
    image_files: list[dict]    = []
    skipped: list[str]         = []
    total_bytes = 0

    for upload in files:
        raw = await upload.read()
        total_bytes += len(raw)
        if total_bytes > _MAX_DROP_BYTES:
            raise HTTPException(413, f"Total upload exceeds {_MAX_DROP_BYTES // (1024*1024)} MB")
        fname = upload.filename or "upload"
        ext   = Path(fname).suffix.lower()

        if ext == ".zip":
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for member in zf.namelist():
                        if Path(member).name.startswith((".", "__")):
                            continue
                        member_ext = Path(member).suffix.lower()
                        if member_ext in _IMAGE_EXTS:
                            try:
                                b64 = base64.standard_b64encode(zf.read(member)).decode()
                                image_files.append({"name": member, "b64": b64, "mime": "image/png"})
                            except Exception:
                                pass
                        elif member_ext in _READABLE_EXTS or member_ext == "":
                            try:
                                content = zf.read(member).decode("utf-8", errors="replace")
                                if content.strip():
                                    text_files[member] = content[:8000]
                            except Exception:
                                pass
                        else:
                            skipped.append(member)
            except zipfile.BadZipFile:
                raise HTTPException(400, f"'{fname}' is not a valid ZIP file")
        elif ext in _IMAGE_EXTS:
            b64 = base64.standard_b64encode(raw).decode()
            image_files.append({"name": fname, "b64": b64, "mime": "image/png"})
        elif ext in _READABLE_EXTS or ext == "":
            try:
                text_files[fname] = raw.decode("utf-8", errors="replace")[:8000]
            except Exception:
                skipped.append(fname)
        else:
            skipped.append(fname)

    if not text_files and not image_files:
        raise HTTPException(400, "No readable files found. Supported: ZIP, code, text, CSV, images.")

    file_list = list(text_files.keys())
    label = name or (
        Path(file_list[0]).parent.name if file_list else
        (upload.filename or "upload").rsplit(".", 1)[0]
    )

    job_id = str(uuid.uuid4())[:8]
    asyncio.create_task(_run_drop_bg(job_id, text_files, image_files, label, intent))

    return JSONResponse({
        "id": job_id, "status": "processing", "type": "drop",
        "name": label,
        "file_count": len(text_files) + len(image_files),
        "text_files": len(text_files), "image_files": len(image_files),
        "skipped_files": len(skipped), "total_kb": total_bytes // 1024,
        "message": "Analysis running in background. You will be notified when complete.",
        "timestamp": time.time(),
    })


@router.get("/health")
def health():
    return {
        "status":       "healthy",
        "agent":        "multimodal_ingest",
        "capabilities": ["code_analysis", "codebase_analysis", "image_to_spec", "drop_anything"],
    }
