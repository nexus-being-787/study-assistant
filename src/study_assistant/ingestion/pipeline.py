"""
ingestion/pipeline.py — Orchestrates load → chunk → embed → store.

Responsibilities:
  - Split raw Documents into chunks via RecursiveCharacterTextSplitter
  - Deduplicate chunks already in the store (by source file)
  - Push chunks into the VectorStore
  - Report ingestion statistics
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from study_assistant.config import settings
from study_assistant.ingestion.loader import DocumentLoader
from study_assistant.vectorstore.store import VectorStore


@dataclass
class IngestionReport:
    files_processed: int
    chunks_added: int
    chunks_skipped: int
    sources: list[str]


class IngestionPipeline:
    """
    Full document ingestion pipeline: load → chunk → index.

    Usage:
        pipeline = IngestionPipeline()
        report = pipeline.ingest_all()
        report = pipeline.ingest_file(Path("data/docs/notes.pdf"))
    """

    def __init__(
        self,
        loader: DocumentLoader | None = None,
        store: VectorStore | None = None,
    ) -> None:
        self._loader = loader or DocumentLoader()
        self._store = store or VectorStore()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            # These separators preserve semantic boundaries
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

    def ingest_all(self) -> IngestionReport:
        """Load and index all documents in the docs directory."""
        raw_docs = self._loader.load_all()
        return self._process(raw_docs)

    def ingest_file(self, path) -> IngestionReport:
        """Load and index a single file."""
        from pathlib import Path
        raw_docs = self._loader.load_file(Path(path))
        return self._process(raw_docs)

    # ── Private ───────────────────────────────────────────────────────────────

    def _process(self, raw_docs: list[Document]) -> IngestionReport:
        if not raw_docs:
            return IngestionReport(
                files_processed=0, chunks_added=0, chunks_skipped=0, sources=[]
            )

        # Gather unique source file paths
        sources = list({doc.metadata.get("source", "") for doc in raw_docs})

        # Split into chunks
        chunks = self._splitter.split_documents(raw_docs)

        # Filter out empty chunks
        chunks = [c for c in chunks if c.page_content.strip()]

        # Check existing sources in the store to skip re-indexing
        existing = self._get_indexed_sources()
        new_chunks = [c for c in chunks if c.metadata.get("source") not in existing]
        skipped = len(chunks) - len(new_chunks)

        if new_chunks:
            self._store.add_documents(new_chunks)

        return IngestionReport(
            files_processed=len(sources),
            chunks_added=len(new_chunks),
            chunks_skipped=skipped,
            sources=sources,
        )

    def _get_indexed_sources(self) -> set[str]:
        """Return the set of source paths already present in the vector store."""
        try:
            # Access the underlying ChromaDB collection directly
            collection = self._store._db._collection
            results = collection.get(include=["metadatas"])
            metadatas = results.get("metadatas") or []
            return {m.get("source", "") for m in metadatas if m}
        except Exception:
            return set()
