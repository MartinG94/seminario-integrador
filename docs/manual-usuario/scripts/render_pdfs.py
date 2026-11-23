#!/usr/bin/env python3
"""Renderiza los módulos HTML (src/0*.html) del Manual de Usuario SGD-AVEIT a PDF A4.

Usa Microsoft Edge o Google Chrome en modo headless (o Playwright como respaldo),
almacena los PDFs en pdfs/<nombre>.pdf y los copia a Google Drive:
G:\\My Drive\\Estudios\\Seminario\\Manual de Usuario\\
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANUAL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC_DIR = MANUAL_ROOT / "src"
DEFAULT_PDF_DIR = MANUAL_ROOT / "pdfs"
DEFAULT_DRIVE_DIR = Path(r"G:\My Drive\Estudios\Seminario\Manual de Usuario")


def find_headless_browser() -> Optional[Path]:
    """Localiza el ejecutable de Microsoft Edge o Google Chrome."""
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    for cmd in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(cmd)
        if found:
            return Path(found)
    return None


def count_pdf_pages(pdf_path: Path) -> int:
    """Devuelve la cantidad de páginas del PDF usando pymupdf o pypdf."""
    try:
        import pymupdf  # type: ignore

        with pymupdf.open(pdf_path) as doc:
            return len(doc)
    except ImportError:
        pass
    try:
        from pypdf import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        pass
    try:
        from PyPDF2 import PdfReader  # type: ignore

        return len(PdfReader(str(pdf_path)).pages)
    except ImportError:
        return -1


def render_with_browser(browser_path: Path, html_path: Path, pdf_path: Path) -> None:
    """Imprime un HTML local a PDF A4 mediante Edge/Chrome headless con perfil aislado."""
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    with tempfile.TemporaryDirectory(prefix="aveit_pdf_profile_") as tmp_profile:
        cmd = [
            str(browser_path),
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            f"--user-data-dir={tmp_profile}",
            f"--print-to-pdf={pdf_path.resolve()}",
            html_path.resolve().as_uri(),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if result.returncode != 0 or not pdf_path.is_file() or pdf_path.stat().st_size == 0:
            raise RuntimeError(
                f"Falló la renderización de {html_path.name} (código {result.returncode}).\n"
                f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )


def render_with_playwright(html_path: Path, pdf_path: Path) -> None:
    """Respaldo usando Playwright Chromium si no hay Edge/Chrome instalado."""
    from playwright.sync_api import sync_playwright  # type: ignore

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.pdf(
            path=str(pdf_path.resolve()),
            format="A4",
            print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        browser.close()


def render_all(
    src_dir: Path,
    pdf_dir: Path,
    drive_dir: Optional[Path],
    pattern: str = "0*.html",
) -> List[Tuple[str, int, Path, Optional[Path]]]:
    """Renderiza todos los módulos HTML coincidentes y devuelve el resumen."""
    html_files = sorted(src_dir.glob(pattern))
    if not html_files:
        print(f"[AVISO] No se encontraron archivos '{pattern}' en {src_dir}")
        return []

    browser_path = find_headless_browser()
    use_playwright = False
    if browser_path is None:
        try:
            import playwright.sync_api  # noqa: F401

            use_playwright = True
        except ImportError as exc:
            raise RuntimeError(
                "No se encontró Microsoft Edge, Google Chrome ni Playwright para renderizar PDFs."
            ) from exc

    pdf_dir.mkdir(parents=True, exist_ok=True)
    if drive_dir is not None:
        try:
            drive_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"[AVISO] No se pudo crear/acceder al destino en Drive ({drive_dir}): {exc}")
            drive_dir = None

    engine_label = f"Playwright" if use_playwright else browser_path.name
    print(f"Motor de renderización: {engine_label}")
    print(f"Origen HTML: {src_dir}")
    print(f"Salida PDF : {pdf_dir}")
    if drive_dir is not None:
        print(f"Copia Drive: {drive_dir}")
    print("-" * 76)

    summary: List[Tuple[str, int, Path, Optional[Path]]] = []
    for html_file in html_files:
        pdf_file = pdf_dir / f"{html_file.stem}.pdf"
        if use_playwright:
            render_with_playwright(html_file, pdf_file)
        else:
            assert browser_path is not None
            render_with_browser(browser_path, html_file, pdf_file)

        pages = count_pdf_pages(pdf_file)
        drive_dest: Optional[Path] = None
        if drive_dir is not None:
            drive_dest = drive_dir / pdf_file.name
            shutil.copy2(pdf_file, drive_dest)

        size_kb = pdf_file.stat().st_size / 1024.0
        pages_str = str(pages) if pages >= 0 else "?"
        drive_str = "OK" if drive_dest else "omitido"
        print(f"  {html_file.name:<42} | {pages_str:>3} págs | {size_kb:6.1f} KB | Drive: {drive_str}")
        summary.append((html_file.name, pages, pdf_file, drive_dest))

    total_pages = sum(p for _, p, _, _ in summary if p > 0)
    print("-" * 76)
    print(f"Total renderizado: {len(summary)} módulo(s), {total_pages} páginas.")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Renderiza los manuales HTML de SGD-AVEIT a PDF A4."
    )
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC_DIR, help="Directorio de entrada HTML")
    parser.add_argument("--out", type=Path, default=DEFAULT_PDF_DIR, help="Directorio de salida PDF")
    parser.add_argument("--drive", type=Path, default=DEFAULT_DRIVE_DIR, help="Carpeta destino en Google Drive")
    parser.add_argument("--no-drive", action="store_true", help="Omitir copia a Google Drive")
    parser.add_argument("--pattern", default="0*.html", help="Patrón glob de módulos HTML")
    args = parser.parse_args()

    drive_target = None if args.no_drive else args.drive
    render_all(args.src, args.out, drive_target, pattern=args.pattern)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
