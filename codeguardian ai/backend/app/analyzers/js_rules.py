"""Lightweight JavaScript pattern rules. One tuple = one rule.
(rule_id, regex, severity, category, title, explanation, why, fix, cwe)
"""
import re

JS_RULES = [
    ("JS001", r"\beval\s*\(", "high", "security", "Use of eval()",
     "`eval()` executes a string as code.", "If any part of the string comes from a user, they can run their own code (XSS / RCE).",
     "Use `JSON.parse` for data or a lookup table of allowed functions.", "CWE-95"),
    ("JS002", r"\.innerHTML\s*=", "high", "security", "Assigning to innerHTML",
     "`innerHTML` parses a string as HTML.", "Untrusted text can inject <script> or event handlers (cross-site scripting).",
     "Use `element.textContent = value`, or sanitise with DOMPurify.", "CWE-79"),
    ("JS003", r"document\.write\s*\(", "medium", "security", "Use of document.write()",
     "`document.write` injects raw HTML into the page.", "It is an XSS risk and breaks page loading.", "Create elements with `createElement` and `textContent`.", "CWE-79"),
    ("JS004", r"(?i)(password|passwd|secret|api[_-]?key|token)\s*[:=]\s*['\"][^'\"]{4,}['\"]", "high", "security", "Hard-coded secret",
     "A credential seems to be written directly in the source.", "Anyone who can read the repo (or its history) can use it.",
     "Read it from `process.env.MY_SECRET` and keep it out of git.", "CWE-798"),
    ("JS005", r"child_process|\bexec(Sync)?\s*\(\s*[`'\"].*(\$\{|\+)", "high", "security", "Possible command injection",
     "A shell command is built from variables.", "Special characters can add extra commands.", "Use `execFile('cmd', [args])` instead of building a string.", "CWE-78"),
    ("JS006", r"(?i)(SELECT|INSERT|UPDATE|DELETE)\b[^;\n]*(\+\s*\w+|\$\{)", "high", "security", "SQL built with string concatenation",
     "A query is assembled from variables.", "Attackers can alter the query (SQL injection).", "Use placeholders: `db.query('... WHERE id = ?', [id])`.", "CWE-89"),
    ("JS007", r"Math\.random\s*\(\s*\)", "low", "security", "Math.random() is not secure",
     "`Math.random` is predictable.", "Don't use it for tokens, passwords or IDs that must be unguessable.", "Use `crypto.getRandomValues()` or `crypto.randomUUID()`.", "CWE-338"),
    ("JS008", r"[^=!<>]==[^=]|!=[^=]", "low", "bug", "Loose equality (== / !=)",
     "`==` converts types before comparing (`0 == '0'` is true).", "Can cause surprising bugs.", "Use `===` and `!==`.", None),
    ("JS009", r"\bvar\s+\w+", "info", "style", "`var` declaration",
     "`var` is function-scoped and hoisted, which surprises beginners.", "Can leak variables and cause hard-to-find bugs.", "Use `const` (default) or `let`.", None),
    ("JS010", r"catch\s*\(\s*\w*\s*\)\s*\{\s*\}", "medium", "bug", "Empty catch block",
     "The error is swallowed silently.", "Failures go unnoticed and are hard to debug.", "Log or handle the error: `console.error(err)`.", None),
    ("JS011", r"(?i)fetch\([^)]*http://", "low", "security", "Insecure http:// request",
     "Traffic is not encrypted.", "Data can be read or changed in transit.", "Use https://.", "CWE-319"),
]

COMPILED = [(r[0], re.compile(r[1]), *r[2:]) for r in JS_RULES]
