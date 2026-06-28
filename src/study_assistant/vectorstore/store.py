"""
vectorstore/store.py — ChromaDB persistent vector store.

Wraps langchain-chroma so the rest of the app never touches
ChromaDB internals directly. All persistence is handled here.

Responsibilities:
  - Create / open a named collection
  - Add LangChain Documents with their embeddings
  - Similarity search (returns top-k Documents)
  - Delete a collection (reset)
  - Collection stats
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.documents import Document

from study_assistant.config import settings
from study_assistant.embeddings.encoder import EmbeddingEncoder


@dataclass
class StoreStats:
    collection_name: str
    document_count: int
    persist_dir: str


class VectorStore:
    """
    Persistent ChromaDB vector store using LangChain's Chroma wrapper.

    Usage:
        store = VectorStore()
        store.add_documents(docs)
        results = store.search("What is a TCP handshake?", k=4)
    """

    def __init__(
        self,
        encoder: EmbeddingEncoder | None = None,
        collection_name: str | None = None,
    ) -> None:
        self._encoder = encoder or EmbeddingEncoder()
        self._collection_name = collection_name or settings.chroma_collection_name
        self._persist_dir = str(settings.abs_chroma_persist_dir)

        # Ensure the directory exists before Chroma tries to use it
        settings.abs_chroma_persist_dir.mkdir(parents=True, exist_ok=True)

        self._db = Chroma(
            collection_name=self._collection_name,
            embedding_function=self._encoder,
            persist_directory=self._persist_dir,
        )

    # ── Write ─────────────────────────────────────────────────────────────────

    def add_documents(self, documents: list[Document]) -> list[str]:
        """
        Add a list of LangChain Documents to the store.
        Returns the list of generated IDs.
        """
        if not documents:
            return []
        return self._db.add_documents(documents)

    # ── Read ──────────────────────────────────────────────────────────────────

    def search(self, query: str, k: int = 4) -> list[Document]:
        """Return the top-k most relevant documents for a query."""
        return self._db.similarity_search(query, k=k)

    def search_with_scores(self, query: str, k: int = 4) -> list[tuple[Document, float]]:
        """Return top-k documents with their cosine similarity scores."""
        return self._db.similarity_search_with_score(query, k=k)

    def as_retriever(self, k: int = 4):
        """Return a LangChain BaseRetriever for use in RAG chains."""
        return self._db.as_retriever(search_kwargs={"k": k})

    # ── Admin ─────────────────────────────────────────────────────────────────

    def stats(self) -> StoreStats:
        """Return basic statistics about the current collection."""
        count = self._db._collection.count()
        return StoreStats(
            collection_name=self._collection_name,
            document_count=count,
            persist_dir=self._persist_dir,
        )

    def reset(self) -> None:
        """Delete all documents in the collection (keeps the collection itself)."""
        self._db._collection.delete(where={"source": {"$ne": ""}})

    def delete_collection(self) -> None:
        """Completely drop the collection from ChromaDB."""
        self._db.delete_collection()
