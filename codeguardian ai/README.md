# 🛡️ CodeGuardian AI

An open-source AI code reviewer for beginner developers. Paste or upload Python/JavaScript and get:

- **Bugs and security issues** with severity, affected lines and plain-English explanations
- **Confidence indicators**: findings confirmed by static tools are marked ✔, AI-only ideas are capped and labelled "not verified"
- **Suggested patch** with a side-by-side before/after diff (patches that don't parse are discarded)
- **GitHub PR review**: reviews only the lines a pull request changed, optionally posts the result as a comment
- **Evaluation suite** that measures precision/recall of the findings

## How it works

```
code ─► Bandit + Ruff (Python) / pattern rules (JS)  ─► verified findings ─┐
                                                                            ├─► merge ─► confidence ─► diff
code + findings ─► Gemma (via Ollama) ─► explanations, extra ideas, patch ──┘
```
Static tools are the source of truth for security; Gemma explains, reasons about extra bugs, and proposes the fix.
User code is **never executed**.

## Quick start

### 1. Model
```bash
ollama pull <your-gemma-tag>      # check `ollama list` for the exact Gemma 4 tag
cp .env.example .env              # set GEMMA_MODEL to that tag
```

### 2. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a; source ../.env; set +a
uvicorn app.main:app --reload     # http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

### Docker
```bash
docker compose up --build         # app on http://localhost
```
Ollama runs on the host; the backend reaches it via `host.docker.internal`.

## API

| Method | Path | Body |
|---|---|---|
| GET | `/api/health` | |
| POST | `/api/review` | `{code, language: "python"\|"javascript", filename, use_ai}` |
| POST | `/api/review/upload` | multipart `file`, `use_ai` |
| POST | `/api/github/pr` | `{pr_url, github_token?, use_ai, post_comment}` |

## Tests and evaluation
```bash
cd backend
pytest -q                          # unit + API tests (AI is mocked)
python -m eval.run_eval --no-ai    # static layer precision/recall
python -m eval.run_eval            # full pipeline with Gemma
```
Add labelled examples in `backend/eval/cases.py`, the easiest way to contribute.

## Deploy on DigitalOcean
1. Create a Droplet (Ubuntu, 4 GB+ RAM for small models; or use a GPU Droplet for larger Gemma sizes).
2. `curl -fsSL https://ollama.com/install.sh | sh && ollama pull <gemma-tag>`
3. Install Docker, clone this repo, `cp .env.example .env`, `docker compose up -d --build`.
4. Point a domain at the Droplet and add HTTPS with Caddy or Certbot.

## Project layout
```
backend/app/analyzers/   Bandit, Ruff, JS rules, beginner explanations
backend/app/ai/gemma.py  Gemma prompt + client
backend/app/review.py    merge, confidence, health score, diff
backend/app/github.py    PR review
backend/eval/            labelled cases + metrics
frontend/src/            React + Tailwind UI
```

## Limitations
- The JavaScript layer is regex-based, so it can miss issues or flag false positives. Swapping in ESLint/Semgrep is a great contribution.
- Small models can hallucinate. That's why AI-only findings are capped at 70% confidence.
- Files over 60k characters are rejected, and PR review covers at most 10 files.

License: MIT. See [CONTRIBUTING.md](CONTRIBUTING.md).
