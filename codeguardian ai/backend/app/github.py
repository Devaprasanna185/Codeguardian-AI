"""GitHub pull-request review (advanced feature)."""
import re

import httpx

from .config import settings
from .review import review_code

PR_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)")
EXT = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript"}
MAX_FILES = 10


def parse_pr_url(url: str):
    m = PR_RE.search(url)
    if not m:
        raise ValueError("Use a URL like https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))


def _lang(name: str):
    for ext, lang in EXT.items():
        if name.endswith(ext):
            return lang
    return None


def _changed_lines(patch: str) -> set[int]:
    """New-file line numbers touched by a unified-diff patch."""
    lines, cur = set(), 0
    for row in (patch or "").splitlines():
        if row.startswith("@@"):
            m = re.search(r"\+(\d+)", row)
            cur = int(m.group(1)) - 1 if m else 0
        elif row.startswith("+") and not row.startswith("+++"):
            cur += 1
            lines.add(cur)
        elif not row.startswith("-"):
            cur += 1
    return lines


def to_markdown(results: list[dict]) -> str:
    out = ["## 🛡️ CodeGuardian AI review\n"]
    total = sum(len(r["findings"]) for r in results)
    out.append(f"Checked **{len(results)}** file(s), found **{total}** issue(s) on changed lines.\n")
    for r in results:
        if not r["findings"]:
            continue
        out.append(f"### `{r['filename']}`")
        for f in r["findings"]:
            out.append(f"- **{f['severity'].upper()}** line {f['line_start']}: {f['title']} "
                       f"(confidence {int(f['confidence'] * 100)}%)\n  {f['suggested_fix']}")
    out.append("\n<sub>Security findings are verified by Bandit / pattern rules; AI explanations may be imperfect.</sub>")
    return "\n".join(out)


async def review_pull_request(pr_url: str, token: str | None, use_ai: bool, post_comment: bool) -> dict:
    owner, repo, num = parse_pr_url(pr_url)
    token = token or settings.github_token
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    results = []
    async with httpx.AsyncClient(timeout=30, headers=headers, follow_redirects=True) as c:
        r = await c.get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}/files", params={"per_page": 100})
        r.raise_for_status()
        files = [f for f in r.json() if _lang(f["filename"]) and f["status"] != "removed"][:MAX_FILES]
        for f in files:
            raw = await c.get(f["raw_url"])
            if raw.status_code != 200 or len(raw.text) > settings.max_code_chars:
                continue
            rev = await review_code(raw.text, _lang(f["filename"]), f["filename"], use_ai)
            changed = _changed_lines(f.get("patch", ""))
            data = rev.model_dump()
            if changed:  # focus on lines this PR touched
                data["findings"] = [x for x in data["findings"] if any(l in changed for l in range(x["line_start"], x["line_end"] + 1))]
            results.append(data)
        markdown = to_markdown(results)
        posted = False
        if post_comment:
            if not token:
                raise ValueError("A GitHub token is required to post a comment.")
            pr = await c.post(f"https://api.github.com/repos/{owner}/{repo}/issues/{num}/comments", json={"body": markdown})
            pr.raise_for_status()
            posted = True
    return {"owner": owner, "repo": repo, "number": num, "files": results, "markdown": markdown, "comment_posted": posted}
