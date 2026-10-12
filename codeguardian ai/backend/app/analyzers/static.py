"""Static analysis: Bandit + Ruff for Python, regex rules for JavaScript.
User code is only ever *read* (parsed/scanned), never executed.
"""
import ast
import json
import os
import subprocess
import sys
import tempfile

from ..schemas import Finding
from .explanations import EXPLANATIONS
from .js_rules import COMPILED

BANDIT_SEV = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}
BANDIT_CONF = {"HIGH": 0.95, "MEDIUM": 0.85, "LOW": 0.65}
RUFF_IGNORE = "E501"


def _run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _enrich(f: Finding) -> Finding:
    if f.rule_id in EXPLANATIONS:
        f.explanation, f.why_it_matters, f.suggested_fix = EXPLANATIONS[f.rule_id]
    return f


def run_bandit(code: str) -> list[Finding]:
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "target.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        r = _run([sys.executable, "-m", "bandit", "-f", "json", "-q", path])
        if not r or not r.stdout.strip():
            return []
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            return []
    out = []
    for i in data.get("results", []):
        cwe = i.get("issue_cwe", {}).get("id")
        lr = i.get("line_range") or [i["line_number"]]
        out.append(_enrich(Finding(
            rule_id=i["test_id"], title=i["issue_text"].rstrip("."),
            severity=BANDIT_SEV.get(i["issue_severity"], "low"), category="security",
            line_start=min(lr), line_end=max(lr), source="bandit",
            explanation=i["issue_text"], confidence=BANDIT_CONF.get(i["issue_confidence"], 0.6),
            verified_by_static=True, cwe=f"CWE-{cwe}" if cwe else None)))
    return out


def run_ruff(code: str) -> list[Finding]:
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "target.py")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(code)
        r = _run([sys.executable, "-m", "ruff", "check", "--isolated", "--select", "E,F,B",
                  "--ignore", RUFF_IGNORE, "--output-format", "json", path])
        if not r or not r.stdout.strip():
            return []
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            return []
    out = []
    for i in data:
        code_ = i.get("code") or ""
        sev = "medium" if code_.startswith(("F8", "E9", "B0")) else "low"
        cat = "bug" if sev == "medium" else "style"
        out.append(_enrich(Finding(
            rule_id=code_, title=i["message"], severity=sev, category=cat,
            line_start=i["location"]["row"], line_end=i.get("end_location", i["location"])["row"],
            source="ruff", explanation=i["message"], confidence=0.85, verified_by_static=True)))
    return out


def python_syntax(code: str) -> list[Finding]:
    try:
        ast.parse(code)
        return []
    except SyntaxError as e:
        return [Finding(rule_id="SYNTAX", title=f"Syntax error: {e.msg}", severity="high", category="bug",
                        line_start=e.lineno or 1, line_end=e.lineno or 1, source="syntax",
                        explanation=f"Python can't read this line: {e.msg}.",
                        why_it_matters="The file will not run at all until this is fixed.",
                        suggested_fix="Check brackets, quotes and colons near this line.",
                        confidence=1.0, verified_by_static=True)]


def run_js_rules(code: str) -> list[Finding]:
    out = []
    for n, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(("//", "*", "/*")):
            continue
        for rid, rx, sev, cat, title, expl, why, fix, cwe in COMPILED:
            if rx.search(line):
                out.append(Finding(rule_id=rid, title=title, severity=sev, category=cat, line_start=n, line_end=n,
                                   source="pattern", explanation=expl, why_it_matters=why, suggested_fix=fix,
                                   confidence=0.75 if cat == "security" else 0.7,
                                   verified_by_static=True, cwe=cwe))
    return out


def analyze(code: str, language: str) -> tuple[list[Finding], list[str]]:
    warnings = []
    if language == "python":
        syn = python_syntax(code)
        if syn:
            return syn, warnings  # Bandit/Ruff can't help with unparsable code
        b, r = run_bandit(code), run_ruff(code)
        if not b and not r:
            # distinguish "clean" from "tool missing" cheaply
            if _run([sys.executable, "-m", "bandit", "--version"]) is None:
                warnings.append("Bandit is not installed; security checks are limited.")
        findings = b + r
    else:
        findings = run_js_rules(code)
    # de-duplicate identical rule+line
    seen, unique = set(), []
    for f in findings:
        k = (f.rule_id, f.line_start)
        if k not in seen:
            seen.add(k)
            unique.append(f)
    return unique, warnings
