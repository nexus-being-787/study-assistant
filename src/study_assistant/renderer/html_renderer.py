"""
renderer/html_renderer.py — Renders RAGResult into a styled HTML study sheet.

Uses a Jinja2 template (template.html.j2) and writes the output to the
configured output directory.

Special handling:
  - FLASHCARD mode: parses "FRONT: ... BACK: ..." pairs from the answer
    and renders them in a card grid instead of a plain text block.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from study_assistant.config import settings
from study_assistant.rag.chain import RAGResult
from study_assistant.rag.prompts import PromptMode

_TEMPLATE_DIR = Path(__file__).parent
_TEMPLATE_FILE = "template.html.j2"

_MODE_LABELS: dict[PromptMode, str] = {
    PromptMode.EXPLAIN: "Explanation",
    PromptMode.SUMMARIZE: "Summary",
    PromptMode.QUIZ: "Quiz",
    PromptMode.FLASHCARD: "Flashcards",
    PromptMode.NOTES: "Study Notes",
}


@dataclass
class Flashcard:
    front: str
    back: str


class HTMLRenderer:
    """
    Renders a RAGResult to an HTML file.

    Usage:
        renderer = HTMLRenderer()
        output_path = renderer.render(result)
    """

    def __init__(self, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir or settings.abs_output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATE_DIR)),
            autoescape=True,
        )

    def render(self, result: RAGResult, filename: str | None = None) -> Path:
        """
        Render a RAGResult to an HTML file and return the output path.

        Args:
            result:   The RAGResult from the RAG chain.
            filename: Optional output filename (without extension).
                      Defaults to a slug derived from the question.
        """
        template = self._env.get_template(_TEMPLATE_FILE)

        flashcards: list[Flashcard] = []
        if result.mode == PromptMode.FLASHCARD:
            flashcards = self._parse_flashcards(result.answer)

        context = {
            "title": self._make_title(result.question),
            "mode": result.mode.value,
            "section_label": _MODE_LABELS.get(result.mode, "Answer"),
            "answer": result.answer,
            "flashcards": flashcards,
            "sources": result.sources,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "model_name": settings.abs_llm_model_path.name,
        }

        html = template.render(**context)

        output_path = self._output_dir / f"{filename or self._slugify(result.question)}.html"
        output_path.write_text(html, encoding="utf-8")

        return output_path

    # ── Private ───────────────────────────────────────────────────────────────

    def _parse_flashcards(self, text: str) -> list[Flashcard]:
        """
        Parse flashcard pairs from LLM output.

        Expected format (flexible):
          FRONT: <text>
          BACK: <text>
        """
        cards: list[Flashcard] = []
        pattern = re.compile(
            r"FRONT:\s*(.+?)\s*BACK:\s*(.+?)(?=FRONT:|$)",
            re.DOTALL | re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            front = match.group(1).strip()
            back = match.group(2).strip()
            if front and back:
                cards.append(Flashcard(front=front, back=back))
        return cards

    @staticmethod
    def _make_title(question: str) -> str:
        """Truncate question to a reasonable title length."""
        q = question.strip()
        return q if len(q) <= 80 else q[:77] + "..."

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert a question string into a safe filename slug."""
        slug = re.sub(r"[^\w\s-]", "", text.lower())
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
        return slug[:60] or "study-sheet"
