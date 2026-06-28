"""
rag/chain.py — Retrieval-Augmented Generation chain.

Flow:
  query → VectorStore retrieval → prompt assembly → LLM → RAGResult

The chain is built using LangChain's LCEL (LangChain Expression Language)
for clean, composable pipeline definition.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from study_assistant.llm.engine import LLMEngine
from study_assistant.rag.prompts import PromptMode, get_prompt
from study_assistant.vectorstore.store import VectorStore


@dataclass
class RAGResult:
    question: str
    answer: str
    mode: PromptMode
    source_documents: list[Document] = field(default_factory=list)

    @property
    def sources(self) -> list[str]:
        """Unique source file names used to build this answer."""
        seen: set[str] = set()
        result: list[str] = []
        for doc in self.source_documents:
            src = doc.metadata.get("filename", doc.metadata.get("source", "unknown"))
            if src not in seen:
                seen.add(src)
                result.append(src)
        return result


class RAGChain:
    """
    Orchestrates retrieval + generation for a given study mode.

    Usage:
        chain = RAGChain()
        result = chain.query("Explain the OSI model", mode=PromptMode.EXPLAIN)
        print(result.answer)
        print(result.sources)
    """

    def __init__(
        self,
        store: VectorStore | None = None,
        engine: LLMEngine | None = None,
        retrieval_k: int = 4,
    ) -> None:
        self._store = store or VectorStore()
        self._engine = engine or LLMEngine()
        self._retrieval_k = retrieval_k

    def query(self, question: str, mode: PromptMode = PromptMode.EXPLAIN) -> RAGResult:
        """
        Retrieve relevant context and generate a study-mode-appropriate response.
        """
        # 1. Retrieve relevant chunks
        source_docs = self._store.search(question, k=self._retrieval_k)

        # 2. Build context string from retrieved chunks
        context = self._format_context(source_docs)

        # 3. Build prompt
        prompt_template = get_prompt(mode)
        prompt_text = prompt_template.format(context=context, question=question)

        # 4. Generate response
        result = self._engine.generate(prompt_text)

        return RAGResult(
            question=question,
            answer=result.text,
            mode=mode,
            source_documents=source_docs,
        )

    def stream_query(self, question: str, mode: PromptMode = PromptMode.EXPLAIN):
        """
        Same as query() but streams tokens as they are generated.
        Yields (token: str) until completion, then yields the RAGResult.
        """
        source_docs = self._store.search(question, k=self._retrieval_k)
        context = self._format_context(source_docs)
        prompt_template = get_prompt(mode)
        prompt_text = prompt_template.format(context=context, question=question)

        full_answer = ""
        for token in self._engine.stream(prompt_text):
            full_answer += token
            yield token

        # Final yield — the complete result object
        yield RAGResult(
            question=question,
            answer=full_answer.strip(),
            mode=mode,
            source_documents=source_docs,
        )

    def as_langchain_chain(self, mode: PromptMode = PromptMode.EXPLAIN):
        """
        Return a pure LCEL chain for integration with other LangChain components.

        Returns: Runnable that accepts {"question": str} and returns str
        """
        retriever = self._store.as_retriever(k=self._retrieval_k)
        prompt = get_prompt(mode)
        llm = self._engine.as_langchain_llm()

        def format_docs(docs: list[Document]) -> str:
            return self._format_context(docs)

        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        return chain

    # ── Private ───────────────────────────────────────────────────────────────

    def _format_context(self, docs: list[Document]) -> str:
        """Concatenate document chunks into a single context string."""
        if not docs:
            return "No relevant context found."

        parts: list[str] = []
        for i, doc in enumerate(docs, start=1):
            source = doc.metadata.get("filename", "unknown")
            page = doc.metadata.get("page", "")
            page_tag = f" (p.{page})" if page else ""
            parts.append(f"[{i}] Source: {source}{page_tag}\n{doc.page_content.strip()}")

        return "\n\n---\n\n".join(parts)
