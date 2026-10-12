"""Gemma client (served locally through Ollama). The AI explains and proposes fixes;
static tools remain the source of truth for security findings."""
import json
import re

import httpx

from ..config import settings

SYSTEM = """You are CodeGuardian, a patient senior engineer reviewing code for BEGINNER developers.
Rules:
- Use simple, friendly language. Explain WHY something is a problem.
- Only report real problems you can point to by line number. Do not invent issues.
- Line numbers refer to the numbered listing you are given (1-based).
- If static-analysis findings are provided, explain them and add only genuinely new issues.
- Return ONLY valid JSON, no markdown fences, using exactly this shape:
{"findings":[{"title":str,"severity":"critical|high|medium|low|info","category":"security|bug|style",
"line_start":int,"line_end":int,"explanation":str,"why_it_matters":str,"suggested_fix":str,"confidence":0.0-1.0}],
"fixed_code": "the COMPLETE corrected file as a string, or null if no change is needed"}
- fixed_code must keep the original behaviour and style; change only what is needed to fix the findings."""


def _parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON")
    return json.loads(text[start:end + 1])


async def review_with_gemma(code: str, language: str, static_findings: list) -> dict:
    numbered = "\n".join(f"{i:4d} | {line}" for i, line in enumerate(code.splitlines(), 1))
    static = [{"line": f.line_start, "rule": f.rule_id, "title": f.title, "tool": f.source} for f in static_findings]
    user = (f"Language: {language}\n\nStatic-analysis findings (verified by tools):\n"
            f"{json.dumps(static, indent=1)}\n\nCode:\n{numbered}")
    payload = {
        "model": settings.gemma_model,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=settings.ai_timeout) as client:
        r = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
        r.raise_for_status()
        return _parse_json(r.json()["message"]["content"])
