"""
rag/prompts.py — Prompt templates for different study output modes.

Each PromptMode generates a different style of study material:
  - EXPLAIN   : Plain explanation of a concept
  - SUMMARIZE : Condensed summary of retrieved context
  - QUIZ      : Multiple-choice questions from context
  - FLASHCARD : Q&A flashcard pairs
  - NOTES     : Structured study notes with key points
"""

from __future__ import annotations

from enum import Enum

from langchain_core.prompts import PromptTemplate


class PromptMode(str, Enum):
    EXPLAIN = "explain"
    SUMMARIZE = "summarize"
    QUIZ = "quiz"
    FLASHCARD = "flashcard"
    NOTES = "notes"


# Shared preamble injected into all prompts
_CONTEXT_BLOCK = (
    "Use ONLY the following retrieved context to answer. "
    "If the context does not contain enough information, say so clearly.\n\n"
    "Context:\n{context}\n\n"
)

_TEMPLATES: dict[PromptMode, str] = {
    PromptMode.EXPLAIN: (
        _CONTEXT_BLOCK
        + "Question: {question}\n\n"
        "Provide a clear, detailed explanation suitable for a student. "
        "Use examples where possible.\n\nAnswer:"
    ),
    PromptMode.SUMMARIZE: (
        _CONTEXT_BLOCK
        + "Topic: {question}\n\n"
        "Write a concise summary of the key ideas from the context above. "
        "Use bullet points for clarity.\n\nSummary:"
    ),
    PromptMode.QUIZ: (
        _CONTEXT_BLOCK
        + "Topic: {question}\n\n"
        "Generate 5 multiple-choice questions based on the context above. "
        "Format each question as:\n"
        "Q1. <question>\n"
        "A) <option>\nB) <option>\nC) <option>\nD) <option>\n"
        "Answer: <letter>\n\nQuestions:"
    ),
    PromptMode.FLASHCARD: (
        _CONTEXT_BLOCK
        + "Topic: {question}\n\n"
        "Generate 8 flashcard pairs from the context. "
        "Format each as:\nFRONT: <term or question>\nBACK: <definition or answer>\n\n"
        "Flashcards:"
    ),
    PromptMode.NOTES: (
        _CONTEXT_BLOCK
        + "Topic: {question}\n\n"
        "Create structured study notes. Include:\n"
        "- Key Concepts\n"
        "- Important Definitions\n"
        "- Core Formulas or Rules (if any)\n"
        "- Quick Summary\n\n"
        "Notes:"
    ),
}


def get_prompt(mode: PromptMode) -> PromptTemplate:
    """Return the PromptTemplate for the given study mode."""
    template = _TEMPLATES[mode]
    return PromptTemplate(
        input_variables=["context", "question"],
        template=template,
    )
