from app.analyzers.static import analyze

PY_BAD = '''import os, subprocess
password = "hunter2hunter2"
def run(cmd):
    subprocess.call(cmd, shell=True)
def f(x=[]):
    return eval(x)
'''


def rules(code, lang):
    findings, _ = analyze(code, lang)
    return {f.rule_id for f in findings}


def test_python_security_detected():
    r = rules(PY_BAD, "python")
    assert "B602" in r      # shell=True
    assert "B307" in r      # eval
    assert "B105" in r      # hardcoded password


def test_python_lint_detected():
    assert "B006" in rules(PY_BAD, "python")  # mutable default


def test_syntax_error_reported():
    findings, _ = analyze("def broken(:\n  pass", "python")
    assert findings and findings[0].rule_id == "SYNTAX"


def test_clean_python_has_no_findings():
    assert rules("def add(a, b):\n    return a + b\n", "python") == set()


def test_js_rules():
    code = "var a = 1;\nel.innerHTML = user;\nif (a == 2) { eval(x) }\n"
    r = rules(code, "javascript")
    assert {"JS001", "JS002", "JS008", "JS009"} <= r


def test_js_comments_ignored():
    assert rules("// eval(x)\n", "javascript") == set()
