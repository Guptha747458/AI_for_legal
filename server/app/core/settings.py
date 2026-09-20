"""
Configuration management for LegalLens.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self) -> None:
        self.api_key: str | None = os.getenv("GROQ_API_KEY")
        self.model: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.max_tokens: int = int(os.getenv("GROQ_MAX_TOKENS", "4096"))
        self.temperature: float = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
        self.max_document_chars: int = int(os.getenv("MAX_DOCUMENT_CHARS", "60000"))
        self.max_context_chars: int = int(os.getenv("MAX_CONTEXT_CHARS", "35000"))
        self.max_chunks: int = int(os.getenv("MAX_CHUNKS", "40"))
        self.demo_mode: bool = os.getenv("LEGALLENS_DEMO_MODE", "true").lower() in ("1", "true", "yes")
        base = Path(os.getenv("LEGALLENS_DATA_DIR", "data"))
        # Resolve relative to the server/ directory so cwd doesn't matter.
        if not base.is_absolute():
            base = Path(__file__).resolve().parents[2] / base
        self.data_dir: Path = base
        self.upload_dir: Path = self.data_dir / "uploads"
        self.output_dir: Path = self.data_dir / "outputs"
        origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
        self.cors_origins: list[str] = [o.strip() for o in origins.split(",") if o.strip()]

    def is_available(self) -> bool:
        """True when a real Groq key is configured and demo mode is disabled."""
        return (
            not self.demo_mode
            and self.api_key is not None
            and len(self.api_key.strip()) > 0
        )

    @property
    def requires_api_key(self) -> bool:
        return not self.is_available()


settings = Settings()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
