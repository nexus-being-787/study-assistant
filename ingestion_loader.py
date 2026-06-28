"""
ingestion/loader.py — Loads PDFs and plain-text files into LangChain Documents.

Supports:
  - .pdf  — via pypdf (no OCR; text-based PDFs only)
  - .txt  — plain UTF-8 text files
  - .md   — Markdown files (treated as plain text)

Each loaded Document carries metadata:
  source   — absolute path string
  filename — basename
  filetype — "pdf" | "txt" | "md"
  page     — page number (PDFs only)
"""

from __future__ import annotations

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from study_assistant.config import settings

_SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


class DocumentLoader:
    """
    Discovers and loads all supported documents from a directory.

    Usage:
        loader = DocumentLoader()
        docs = loader.load_all()          # load everything in data/docs/
        docs = loader.load_file(path)     # load a single file
    """

    def __init__(self, docs_dir: Path | None = None) -> None:
        self._docs_dir = docs_dir or settings.abs_docs_dir

    def load_all(self) -> list[Document]:
        """Load every supported file from the configured docs directory."""
        all_docs: list[Document] = []
        files = sorted(self._docs_dir.rglob("*"))

        for file_path in files:
            if file_path.suffix.lower() in _SUPPORTED_EXTENSIONS:
                loaded = self.load_file(file_path)
                all_docs.extend(loaded)

        return all_docs

    def load_file(self, path: Path) -> list[Document]:
        """Load a single file and return its Document(s)."""
        path = Path(path).resolve()
        suffix = path.suffix.lower()

        if suffix not in _SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: '{suffix}'. "
                f"Supported: {_SUPPORTED_EXTENSIONS}"
            )

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        if suffix == ".pdf":
            return self._load_pdf(path)
        else:
            return self._load_text(path, filetype=suffix.lstrip("."))

    # ── Private ───────────────────────────────────────────────────────────────

    def _load_pdf(self, path: Path) -> list[Document]:
        loader = PyPDFLoader(str(path))
        docs = loader.load()
        for doc in docs:
            doc.metadata.update(
                {
                    "filename": path.name,
                    "filetype": "pdf",
                    "source": str(path),
                }
            )
        return docs

    def _load_text(self, path: Path, filetype: str) -> list[Document]:
        loader = TextLoader(str(path), encoding="utf-8")
        docs = loader.load()
        for doc in docs:
            doc.metadata.update(
                {
                    "filename": path.name,
                    "filetype": filetype,
                    "source": str(path),
                }
            )
        return docs

    @property
    def docs_dir(self) -> Path:
        return self._docs_dir

    def list_files(self) -> list[Path]:
        """List all supported files in the docs directory."""
        return sorted(
            f for f in self._docs_dir.rglob("*")
            if f.suffix.lower() in _SUPPORTED_EXTENSIONS
        )
