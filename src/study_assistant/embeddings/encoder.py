"""
embeddings/encoder.py — Wraps sentence-transformers for embedding generation.

Supports:
  - BGE-small-en-v1.5  (default, fast, good quality)
  - nomic-ai/nomic-embed-text-v1  (larger, better recall)

BGE requires a query prefix "Represent this sentence for searching relevant passages: "
for asymmetric retrieval. This is handled automatically.
"""

from __future__ import annotations

from functools import cached_property
from typing import Any

from langchain_core.embeddings import Embeddings

from study_assistant.config import settings

# BGE models use a specific query prefix for better asymmetric retrieval
_BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_BGE_MODEL_PREFIX = "BAAI/bge"


class EmbeddingEncoder(Embeddings):
    """
    Sentence-transformer embedding encoder.

    Implements LangChain's Embeddings interface so it can be dropped
    directly into LangChain's Chroma vectorstore.

    Usage:
        encoder = EmbeddingEncoder()
        vecs = encoder.embed_documents(["Newton's first law...", "..."])
        query_vec = encoder.embed_query("What is inertia?")
    """

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.embed_model_name
        self._model: Any = None  # lazy load

    @cached_property
    def _is_bge(self) -> bool:
        return self._model_name.startswith(_BGE_MODEL_PREFIX)

    def _load(self) -> None:
        if self._model is not None:
            return

        from sentence_transformers import SentenceTransformer

        # trust_remote_code required by nomic-embed-text-v1
        self._model = SentenceTransformer(
            self._model_name,
            trust_remote_code=True,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of document chunks (no prefix)."""
        self._load()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (BGE prefix applied if needed)."""
        self._load()
        query = f"{_BGE_QUERY_PREFIX}{text}" if self._is_bge else text
        embedding = self._model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_loaded(self) -> bool:
        return self._model is not None
