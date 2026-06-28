"""
cli/main.py — Typer CLI for study-assistant.

Commands:
  study ingest          — Index all documents in data/docs/
  study ingest FILE     — Index a single file
  study ask QUESTION    — Ask a question (RAG)
  study ask QUESTION --mode quiz
  study info            — Show config and store stats
  study reset           — Wipe the vector store
  study export PATH     — Convert an HTML study sheet to PDF
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from study_assistant.config import settings
from study_assistant.rag.prompts import PromptMode

app = typer.Typer(
    name="study",
    help="📚 CLI-first AI study assistant — powered by local LLM + RAG",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_store():
    from study_assistant.vectorstore.store import VectorStore
    return VectorStore()


def _get_pipeline():
    from study_assistant.ingestion.pipeline import IngestionPipeline
    return IngestionPipeline()


def _get_chain():
    from study_assistant.rag.chain import RAGChain
    return RAGChain()


def _get_renderer():
    from study_assistant.renderer.html_renderer import HTMLRenderer
    return HTMLRenderer()


def _get_exporter():
    from study_assistant.renderer.pdf_exporter import PDFExporter
    return PDFExporter()


# ── Commands ──────────────────────────────────────────────────────────────────


@app.command()
def ingest(
    file: Annotated[Optional[Path], typer.Argument(help="Single file to ingest (optional)")] = None,
):
    """
    Index documents into the vector store.

    Without arguments: indexes everything in data/docs/.
    With a file path: indexes that specific file only.
    """
    settings.ensure_dirs()
    pipeline = _get_pipeline()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        if file:
            progress.add_task(f"Ingesting [cyan]{file.name}[/cyan]...", total=None)
            report = pipeline.ingest_file(file)
        else:
            progress.add_task("Scanning [cyan]data/docs/[/cyan]...", total=None)
            report = pipeline.ingest_all()

    # ── Report ────────────────────────────────────────────────────────────────
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]Files processed[/dim]", f"[bold]{report.files_processed}[/bold]")
    table.add_row("[dim]Chunks added[/dim]", f"[green bold]{report.chunks_added}[/green bold]")
    table.add_row("[dim]Chunks skipped[/dim]", f"[yellow]{report.chunks_skipped}[/yellow] (already indexed)")

    console.print(Panel(table, title="[bold green]✓ Ingestion complete[/bold green]", border_style="green"))

    if report.sources:
        console.print("\n[dim]Sources:[/dim]")
        for src in report.sources:
            console.print(f"  [cyan]→[/cyan] {src}")


@app.command()
def ask(
    question: Annotated[str, typer.Argument(help="Your study question")],
    mode: Annotated[PromptMode, typer.Option("--mode", "-m", help="Study mode")] = PromptMode.EXPLAIN,
    k: Annotated[int, typer.Option("--k", help="Number of context chunks to retrieve")] = 4,
    save: Annotated[bool, typer.Option("--save", "-s", help="Save result as HTML study sheet")] = False,
    pdf: Annotated[bool, typer.Option("--pdf", help="Also export to PDF (requires --save)")] = False,
    stream: Annotated[bool, typer.Option("--stream", help="Stream tokens as they generate")] = False,
):
    """
    Ask a question and get a study-mode-appropriate answer.

    [bold]Modes:[/bold]
      explain    — Detailed explanation with examples
      summarize  — Bullet-point summary
      quiz       — 5 multiple-choice questions
      flashcard  — 8 Q&A flashcard pairs
      notes      — Structured study notes
    """
    settings.ensure_dirs()

    console.print(f"\n[bold]❓ Question:[/bold] {question}")
    console.print(f"[dim]Mode: {mode.value}  |  Retrieving top-{k} chunks[/dim]\n")

    from study_assistant.rag.chain import RAGChain, RAGResult

    chain = RAGChain(retrieval_k=k)

    result: RAGResult | None = None

    if stream:
        console.print("[bold]Answer:[/bold]")
        for item in chain.stream_query(question, mode=mode):
            if isinstance(item, str):
                console.print(item, end="")
            else:
                result = item
        console.print()  # newline after stream
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Thinking...", total=None)
            result = chain.query(question, mode=mode)

        console.print(Panel(
            result.answer,
            title=f"[bold purple]{mode.value.upper()}[/bold purple]",
            border_style="purple",
        ))

    if result and result.sources:
        console.print("\n[dim]Sources used:[/dim]")
        for src in result.sources:
            console.print(f"  [green]→[/green] {src}")

    # ── Save HTML ─────────────────────────────────────────────────────────────
    if save and result:
        renderer = _get_renderer()
        html_path = renderer.render(result)
        console.print(f"\n[bold green]✓ HTML saved:[/bold green] {html_path}")

        if pdf:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task("Exporting PDF...", total=None)
                exporter = _get_exporter()
                pdf_path = exporter.export(html_path)
            console.print(f"[bold green]✓ PDF saved:[/bold green]  {pdf_path}")


@app.command()
def info():
    """Show current configuration and vector store statistics."""
    settings.ensure_dirs()

    store = _get_store()
    stats = store.stats()

    table = Table(title="Study Assistant — Config & Stats", border_style="dim")
    table.add_column("Setting", style="dim", no_wrap=True)
    table.add_column("Value", style="bold")

    table.add_row("Model path", str(settings.abs_llm_model_path))
    table.add_row("Model exists", "[green]✓[/green]" if settings.abs_llm_model_path.exists() else "[red]✗ not found[/red]")
    table.add_row("Embedding model", settings.embed_model_name)
    table.add_row("Context window", str(settings.llm_n_ctx))
    table.add_row("Max tokens", str(settings.llm_max_tokens))
    table.add_row("Temperature", str(settings.llm_temperature))
    table.add_row("Chunk size", str(settings.chunk_size))
    table.add_row("Chunk overlap", str(settings.chunk_overlap))
    table.add_row("Docs directory", str(settings.abs_docs_dir))
    table.add_row("Output directory", str(settings.abs_output_dir))
    table.add_row("ChromaDB path", str(settings.abs_chroma_persist_dir))
    table.add_row("Collection", stats.collection_name)
    table.add_row("Indexed chunks", f"[cyan]{stats.document_count}[/cyan]")

    console.print(table)


@app.command()
def reset(
    confirm: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
):
    """
    Wipe all indexed documents from the vector store.

    [bold red]Warning:[/bold red] This cannot be undone. Re-run [cyan]study ingest[/cyan] to rebuild.
    """
    if not confirm:
        confirmed = typer.confirm(
            "⚠️  This will delete all indexed documents. Are you sure?",
            default=False,
        )
        if not confirmed:
            rprint("[yellow]Aborted.[/yellow]")
            raise typer.Exit()

    store = _get_store()
    store.delete_collection()
    rprint("[bold red]✓ Vector store wiped.[/bold red] Run [cyan]study ingest[/cyan] to re-index.")


@app.command()
def export(
    html_file: Annotated[Path, typer.Argument(help="Path to an HTML study sheet")],
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Output PDF path")] = None,
):
    """Convert an existing HTML study sheet to PDF using Playwright."""
    if not html_file.exists():
        rprint(f"[red]Error:[/red] File not found: {html_file}")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(f"Rendering [cyan]{html_file.name}[/cyan] to PDF...", total=None)
        exporter = _get_exporter()
        pdf_path = exporter.export(html_file, output_path=output)

    console.print(f"[bold green]✓ PDF saved:[/bold green] {pdf_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
