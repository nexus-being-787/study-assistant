"""
llm/engine.py — Thin wrapper around llama-cpp-python.

Provides:
  - Lazy model loading (only loads when first called)
  - Streaming and non-streaming generation
  - A LangChain-compatible interface via LangChainLLMAdapter
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterator

from langchain_core.language_models.llms import LLM
from langchain_core.outputs import GenerationChunk

from study_assistant.config import settings


@dataclass
class GenerationResult:
    text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMEngine:
    """
    Wraps llama-cpp-python's Llama class.

    Usage:
        engine = LLMEngine()
        result = engine.generate("Explain Newton's laws")
        for chunk in engine.stream("Explain Newton's laws"):
            print(chunk, end="", flush=True)
    """

    def __init__(self) -> None:
        self._model: Any = None  # lazy — loaded on first call

    def _load(self) -> None:
        if self._model is not None:
            return

        model_path = settings.abs_llm_model_path
        if not model_path.exists():
            raise FileNotFoundError(
                f"GGUF model not found at: {model_path}\n"
                f"Download a model and place it in the models/ directory.\n"
                f"Example: https://huggingface.co/TheBloke"
            )

        # Import here so the rest of the app works even without llama-cpp installed
        from llama_cpp import Llama

        self._model = Llama(
            model_path=str(model_path),
            n_ctx=settings.llm_n_ctx,
            n_gpu_layers=settings.llm_n_gpu_layers,
            verbose=False,
        )

    def generate(self, prompt: str) -> GenerationResult:
        """Run a single blocking inference and return the full result."""
        self._load()

        response = self._model(
            prompt,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            stream=False,
        )

        text: str = response["choices"][0]["text"]
        usage: dict = response.get("usage", {})

        return GenerationResult(
            text=text.strip(),
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def stream(self, prompt: str) -> Iterator[str]:
        """Yield text tokens one at a time for streaming output."""
        self._load()

        for chunk in self._model(
            prompt,
            max_tokens=settings.llm_max_tokens,
            temperature=settings.llm_temperature,
            stream=True,
        ):
            token: str = chunk["choices"][0]["text"]
            if token:
                yield token

    def as_langchain_llm(self) -> "LangChainLLMAdapter":
        """Return a LangChain-compatible LLM wrapping this engine."""
        return LangChainLLMAdapter(engine=self)

    @property
    def is_loaded(self) -> bool:
        return self._model is not None


class LangChainLLMAdapter(LLM):
    """
    Adapts LLMEngine to LangChain's LLM interface.

    LangChain RAG chains expect an object with ._call() and streaming support.
    We store the engine reference in a private attribute to avoid Pydantic issues.
    """

    engine: Any = field(default=None)

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "llama_cpp_local"

    def _call(self, prompt: str, stop: list[str] | None = None, **kwargs: Any) -> str:
        result = self.engine.generate(prompt)
        return result.text

    def _stream(self, prompt: str, stop: list[str] | None = None, **kwargs: Any) -> Iterator[GenerationChunk]:
        for token in self.engine.stream(prompt):
            yield GenerationChunk(text=token)
