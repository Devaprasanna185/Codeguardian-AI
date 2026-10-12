"""Orchestrates: static analysis -> Gemma -> merge -> confidence -> diff."""
import ast
import difflib
from typing import Optional

from .ai.gemma import review_with_gemma
from .analyzers.static import analyze
from .schemas import DiffRow, Finding, ReviewResponse, Summary

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
SEV_WEIGHT = {"critical": 25, "high": 15, "medium": 7, "low": 3, "info": 1}
VALID_SEV = set(SEV_ORDER)


def make_diff(original: str, fixed: str) -> list[DiffRow]:
    a, b = original.splitlines(), fixed.splitlines()
    rows: list[DiffRow] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                rows.append(DiffRow(tag="equal", left_no=i1 + k + 1, right_no=j1 + k + 1, left=a[i1 + k], right=b[j1 + k]))
        else:
            n = max(i2 - i1, j2 - j1)
            for k in range(n):
                li, rj = i1 + k, j1 + k
                has_l, has_r = li < i2, rj < j2
                rows.append(DiffRow(
                    tag="replace" if has_l and has_r else ("delete" if has_l else "insert"),
                    left_no=li + 1 if has_l else None, right_no=rj + 1 if has_r else None,
                    left=a[li] if has_l else "", right=b[rj] if has_r else ""))
    return rows


def _valid_fix(original: str, fixed: Optional[str], language: str) -> Optional[str]:
    if not fixed or not isinstance(fixed, str) or fixed.strip() == original.strip():
        return None
    if language == "python":
        try:
            ast.parse(fixed)
        except SyntaxError:
            return None
    return fixed


def _merge_ai(findings: list[Finding], ai: dict, n_lines: int) -> None:
    matched = set()
    for a in ai.get("findings", []):
        try:
            ls = max(1, min(int(a.get("line_start", 1)), n_lines))
            le = max(ls, min(int(a.get("line_end", ls)), n_lines))
        except (TypeError, ValueError):
            continue
        sev = a.get("severity", "low")
        sev = sev if sev in VALID_SEV else "low"
        match = next((f for f in findings if id(f) not in matched and f.source != "gemma" and f.line_start == ls), None)
        if not match:
            match = next((f for f in findings if id(f) not in matched and f.source != "gemma" and abs(f.line_start - ls) <= 1), None)
        if match:  # AI enriches a tool-verified finding
            matched.add(id(match))
            match.explanation = a.get("explanation") or match.explanation
            match.why_it_matters = a.get("why_it_matters") or match.why_it_matters
            match.suggested_fix = a.get("suggested_fix") or match.suggested_fix
            match.confidence = min(1.0, match.confidence + 0.05)
        else:      # AI-only finding: unverified -> capped confidence
            try:
                conf = float(a.get("confidence", 0.5))
            except (TypeError, ValueError):
                conf = 0.5
            cat = a.get("category", "bug")
            findings.append(Finding(
                rule_id="AI", title=str(a.get("title", "Possible issue"))[:120], severity=sev,
                category=cat if cat in ("security", "bug", "style") else "bug",
                line_start=ls, line_end=le, source="gemma",
                explanation=str(a.get("explanation", "")), why_it_matters=str(a.get("why_it_matters", "")),
                suggested_fix=str(a.get("suggested_fix", "")),
                confidence=round(max(0.2, min(conf, 0.7)), 2), verified_by_static=False))


def summarize(findings: list[Finding]) -> Summary:
    counts = {s: 0 for s in SEV_ORDER}
    for f in findings:
        counts[f.severity] += 1
    score = max(0, 100 - sum(SEV_WEIGHT[f.severity] for f in findings))
    return Summary(total=len(findings), counts=counts, score=score)


async def review_code(code: str, language: str, filename: str = "snippet", use_ai: bool = True) -> ReviewResponse:
    findings, warnings = analyze(code, language)
    fixed, ai_used, ai_error = None, False, None
    if use_ai:
        try:
            ai = await review_with_gemma(code, language, findings)
            _merge_ai(findings, ai, max(1, len(code.splitlines())))
            fixed = _valid_fix(code, ai.get("fixed_code"), language)
            if ai.get("fixed_code") and not fixed and ai.get("fixed_code").strip() != code.strip():
                warnings.append("Gemma's suggested patch didn't parse, so it was discarded.")
            ai_used = True
        except Exception as e:  # network, JSON, model missing...
            ai_error = f"{type(e).__name__}: {e}"
            warnings.append("AI review unavailable; showing static-analysis results only.")
    findings.sort(key=lambda f: (SEV_ORDER[f.severity], f.line_start))
    for i, f in enumerate(findings, 1):
        f.id = f"F{i}"
    return ReviewResponse(
        language=language, filename=filename, findings=findings, summary=summarize(findings),
        fixed_code=fixed, diff_rows=make_diff(code, fixed) if fixed else [],
        ai_used=ai_used, ai_error=ai_error, warnings=warnings)
