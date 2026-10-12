from typing import Literal, Optional
from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "medium", "low", "info"]
Language = Literal["python", "javascript"]


class Finding(BaseModel):
    id: str = ""
    rule_id: str = ""
    title: str
    severity: Severity = "low"
    category: Literal["security", "bug", "style"] = "bug"
    line_start: int = 1
    line_end: int = 1
    source: Literal["bandit", "ruff", "pattern", "syntax", "gemma"] = "pattern"
    explanation: str = ""        # beginner-friendly "what is wrong"
    why_it_matters: str = ""     # impact
    suggested_fix: str = ""      # prose / small snippet
    confidence: float = Field(0.5, ge=0, le=1)
    verified_by_static: bool = False
    cwe: Optional[str] = None


class DiffRow(BaseModel):
    tag: Literal["equal", "replace", "delete", "insert"]
    left_no: Optional[int] = None
    right_no: Optional[int] = None
    left: str = ""
    right: str = ""


class ReviewRequest(BaseModel):
    code: str
    language: Language = "python"
    filename: str = "snippet"
    use_ai: bool = True


class Summary(BaseModel):
    total: int
    counts: dict
    score: int  # 0-100 health score


class ReviewResponse(BaseModel):
    language: Language
    filename: str = "snippet"
    findings: list[Finding]
    summary: Summary
    fixed_code: Optional[str] = None
    diff_rows: list[DiffRow] = []
    ai_used: bool = False
    ai_error: Optional[str] = None
    warnings: list[str] = []


class PRRequest(BaseModel):
    pr_url: str
    github_token: Optional[str] = None
    use_ai: bool = True
    post_comment: bool = False
