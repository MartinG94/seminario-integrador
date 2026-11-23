#!/usr/bin/env python3
"""Concatena los PDFs 01..09 del Manual de Usuario SGD-AVEIT en orden numérico.

Genera:
- pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf
- G:\\My Drive\\Estudios\\Seminario\\Manual de Usuario\\Manual_Usuario_SGD_AVEIT_Completo.pdf
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MANUAL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF_DIR = MANUAL_ROOT / "pdfs"
DEFAULT_DRIVE_DIR = Path(r"G:\My Drive\Estudios\Seminario\Manual de Usuario")
MERGED_FILENAME = "Manual_Usuario_SGD_AVEIT_Completo.pdf"


def _module_sort_key(path: Path) -> Tuple[int, str]:
    match = re.match(r"^(\d+)", path.stem)
    num = int(match.group(1)) if match else 9999
    return (num, path.name.lower())


def discover_module_pdfs(pdf_dir: Path) -> List[Path]:
    """Obtiene los PDFs numerados 01..09 en orden numérico estricto."""
    candidates = [
        p
        for p in pdf_dir.glob("0[1-9]*.pdf")
        if p.is_file() and p.name != MERGED_FILENAME
    ]
    return sorted(candidates, key=_module_sort_key)


def _ensure_pdf_backend() -> str:
    """Detecta librería PDF disponible (pypdf, pymupdf o PyPDF2); instala pypdf solo si faltan todas."""
    for mod_name in ("pypdf", "pymupdf", "PyPDF2"):
        try:
            __import__(mod_name)
            return mod_name
        except ImportError:
            continue

    print("[INFO] No se detectó pypdf, pymupdf ni PyPDF2. Instalando pypdf...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    return "pypdf"


def merge_module_pdfs(pdf_files: List[Path], output_pdf: Path) -> Tuple[int, List[Tuple[str, int]]]:
    """Concatena la lista ordenada de PDFs en output_pdf y devuelve (total_págs, detalle)."""
    backend = _ensure_pdf_backend()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    details: List[Tuple[str, int]] = []

    if backend == "pypdf":
        from pypdf import PdfReader, PdfWriter  # type: ignore

        writer = PdfWriter()
        for pdf_path in pdf_files:
            reader = PdfReader(str(pdf_path))
            pages = len(reader.pages)
            writer.append(reader)
            details.append((pdf_path.name, pages))
        with open(output_pdf, "wb") as f:
            writer.write(f)
        return sum(p for _, p in details), details

    if backend == "pymupdf":
        import pymupdf  # type: ignore

        merged = pymupdf.open()
        for pdf_path in pdf_files:
            with pymupdf.open(pdf_path) as src_doc:
                pages = len(src_doc)
                merged.insert_pdf(src_doc)
                details.append((pdf_path.name, pages))
        merged.save(output_pdf)
        total = len(merged)
        merged.close()
        return total, details

    from PyPDF2 import PdfMerger, PdfReader  # type: ignore

    merger = PdfMerger()
    for pdf_path in pdf_files:
        pages = len(PdfReader(str(pdf_path)).pages)
        merger.append(str(pdf_path))
        details.append((pdf_path.name, pages))
    with open(output_pdf, "wb") as f:
        merger.write(f)
    merger.close()
    return sum(p for _, p in details), details


def run_merge(
    pdf_dir: Path,
    drive_dir: Optional[Path],
    output_name: str = MERGED_FILENAME,
) -> Path:
    pdf_files = discover_module_pdfs(pdf_dir)
    if not pdf_files:
        raise FileNotFoundError(
            f"No se encontraron módulos PDF (01*.pdf .. 09*.pdf) en {pdf_dir}. "
            "Ejecutá primero scripts/render_pdfs.py."
        )

    present_nums = {_module_sort_key(p)[0] for p in pdf_files}
    missing = [f"{n:02d}" for n in range(1, 10) if n not in present_nums]
    if missing:
        print(f"[AVISO] Módulos faltantes en {pdf_dir}: {', '.join(missing)}")

    output_pdf = pdf_dir / output_name
    total_pages, details = merge_module_pdfs(pdf_files, output_pdf)

    print(f"Concatenando {len(details)} módulo(s) hacia {output_pdf}:")
    print("-" * 68)
    for name, pages in details:
        print(f"  + {name:<48} ({pages:>2} págs)")
    print("-" * 68)
    size_kb = output_pdf.stat().st_size / 1024.0
    print(f"PDF completo generado: {output_pdf} ({total_pages} págs, {size_kb:.1f} KB)")

    if drive_dir is not None:
        try:
            drive_dir.mkdir(parents=True, exist_ok=True)
            drive_target = drive_dir / output_name
            shutil.copy2(output_pdf, drive_target)
            print(f"Copiado a Google Drive: {drive_target}")
        except OSError as exc:
            print(f"[AVISO] No se pudo copiar a Google Drive ({drive_dir}): {exc}")

    return output_pdf


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Concatena los módulos PDF 01..09 del Manual de Usuario SGD-AVEIT."
    )
    parser.add_argument("--pdfs", type=Path, default=DEFAULT_PDF_DIR, help="Directorio con PDFs por módulo")
    parser.add_argument("--drive", type=Path, default=DEFAULT_DRIVE_DIR, help="Carpeta destino en Google Drive")
    parser.add_argument("--no-drive", action="store_true", help="Omitir copia a Google Drive")
    parser.add_argument("--output-name", default=MERGED_FILENAME, help="Nombre del archivo combinado")
    args = parser.parse_args()

    drive_target = None if args.no_drive else args.drive
    run_merge(args.pdfs, drive_target, output_name=args.output_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
