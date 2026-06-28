"""
renderer/pdf_exporter.py — Exports HTML study sheets to PDF via Playwright.

Playwright headless Chromium renders the HTML (preserving all CSS) and
prints it to PDF. This produces pixel-perfect output matching the HTML preview.

Requirements:
  - playwright must be installed: `pip install playwright`
  - Chromium must be installed: `playwright install chromium`
"""

from __future__ import annotations

from pathlib import Path


class PDFExporter:
    """
    Converts an HTML file to a PDF using Playwright's headless Chromium.

    Usage:
        exporter = PDFExporter()
        pdf_path = exporter.export(html_path)
        pdf_path = exporter.export(html_path, output_path=Path("output/report.pdf"))
    """

    def export(self, html_path: Path, output_path: Path | None = None) -> Path:
        """
        Render html_path to PDF and return the output path.

        Args:
            html_path:   Path to the HTML file to render.
            output_path: Where to save the PDF. Defaults to same dir as HTML
                         with .pdf extension.
        """
        html_path = Path(html_path).resolve()

        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_path}")

        if output_path is None:
            output_path = html_path.with_suffix(".pdf")

        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._render(html_path, output_path)
        return output_path

    # ── Private ───────────────────────────────────────────────────────────────

    def _render(self, html_path: Path, output_path: Path) -> None:
        """Launch Playwright, open the HTML, and print to PDF."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError(
                "Playwright is not installed. Run: pip install playwright && playwright install chromium"
            ) from e

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()

            # Use file:// URI so local assets (if any) resolve correctly
            page.goto(f"file://{html_path}", wait_until="networkidle")

            page.pdf(
                path=str(output_path),
                format="A4",
                print_background=True,   # Render dark background
                margin={
                    "top": "20mm",
                    "right": "18mm",
                    "bottom": "20mm",
                    "left": "18mm",
                },
            )

            browser.close()
