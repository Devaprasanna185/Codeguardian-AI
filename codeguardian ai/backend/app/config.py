import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemma4")
    ai_timeout: float = float(os.getenv("AI_TIMEOUT", "120"))
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    cors_origins: list = field(
        default_factory=lambda: os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    )
    max_code_chars: int = 60_000


settings = Settings()
