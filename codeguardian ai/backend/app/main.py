from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .github import review_pull_request
from .review import review_code
from .schemas import PRRequest, ReviewRequest, ReviewResponse

app = FastAPI(title="CodeGuardian AI", version="1.0.0",
              description="Beginner-friendly AI code review backed by static analysis.")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])

EXT_LANG = {".py": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript"}


def _check_size(code: str):
    if not code.strip():
        raise HTTPException(400, "Paste or upload some code first.")
    if len(code) > settings.max_code_chars:
        raise HTTPException(413, f"File too large (max {settings.max_code_chars} characters).")


@app.get("/api/health")
async def health():
    return {"status": "ok", "model": settings.gemma_model}


@app.post("/api/review", response_model=ReviewResponse)
async def review(req: ReviewRequest):
    _check_size(req.code)
    return await review_code(req.code, req.language, req.filename, req.use_ai)


@app.post("/api/review/upload", response_model=ReviewResponse)
async def review_upload(file: UploadFile = File(...), use_ai: bool = Form(True)):
    name = file.filename or "upload"
    lang = next((v for k, v in EXT_LANG.items() if name.endswith(k)), None)
    if not lang:
        raise HTTPException(400, "Only .py and .js/.jsx files are supported.")
    code = (await file.read()).decode("utf-8", errors="replace")
    _check_size(code)
    return await review_code(code, lang, name, use_ai)


@app.post("/api/github/pr")
async def github_pr(req: PRRequest):
    try:
        return await review_pull_request(req.pr_url, req.github_token, req.use_ai, req.post_comment)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"GitHub request failed: {e}")
