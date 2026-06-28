"""
config.py — Central configuration loaded from .env / environment variables.

All other modules import `settings` from here. Nothing is hardcoded elsewhere.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Project root (always the repo root, not src/) ─────────────────────────
    # Resolved at import time so every module gets absolute paths.
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_model_path: str = Field("models/mistral-7b-instruct-v0.2.Q4_K_M.gguf")
    llm_n_gpu_layers: int = Field(0)
    llm_n_ctx: int = Field(4096)
    llm_max_tokens: int = Field(512)
    llm_temperature: float = Field(0.2)

    # ── Embeddings ────────────────────────────────────────────────────────────
    embed_model_name: str = Field("BAAI/bge-small-en-v1.5")

    # ── Vector store ──────────────────────────────────────────────────────────
    chroma_persist_dir: str = Field("data/chroma")
    chroma_collection_name: str = Field("study_docs")

    # ── Ingestion ─────────────────────────────────────────────────────────────
    docs_dir: str = Field("data/docs")
    chunk_size: int = Field(512)
    chunk_overlap: int = Field(64)

    # ── Renderer ──────────────────────────────────────────────────────────────
    output_dir: str = Field("output")

    # ── Derived absolute paths ─────────────────────────────────────────────────
    @property
    def abs_llm_model_path(self) -> Path:
        return self.project_root / self.llm_model_path

    @property
    def abs_chroma_persist_dir(self) -> Path:
        return self.project_root / self.chroma_persist_dir

    @property
    def abs_docs_dir(self) -> Path:
        return self.project_root / self.docs_dir

    @property
    def abs_output_dir(self) -> Path:
        return self.project_root / self.output_dir

    @field_validator("llm_temperature")
    @classmethod
    def clamp_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("llm_temperature must be between 0.0 and 2.0")
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_chunk(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 512)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return v

    def ensure_dirs(self) -> None:
        """Create all necessary directories if they don't exist."""
        for path in (
            self.abs_chroma_persist_dir,
            self.abs_docs_dir,
            self.abs_output_dir,
            self.project_root / "models",
        ):
            path.mkdir(parents=True, exist_ok=True)


# Singleton — import this everywhere
settings = Settings()
