"""Plantilla compartida y componentes base para el Manual de Usuario SGD-AVEIT.

Reproduce fielmente la identidad visual institucional de AVEIT
(portada con ondas cyan #29ABE2 y escudo central; páginas de pasos con
cintas curvas cyan, encabezado 'AVEIT | Sistema', pie 'X de Y', píldoras
'PASO N' y bloques de interfaz con focos naranja #FF6D00).
"""

from __future__ import annotations

import html
from pathlib import Path
from typing import Sequence, Union

HtmlPages = Union[str, Sequence[str]]

SHIELD_SVG = """<svg class="aveit-shield-svg" viewBox="0 0 240 244" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Escudo institucional AVEIT" style="width:100%;height:auto;display:block;">
  <!-- Halo blanco exterior para contraste limpio sobre cintas cyan -->
  <path d="M78,10 L162,10 L162,16 L176,16 L176,28 L168,28 C168,36 174,42 183,38 C186,32 193,28 200,32 L228,74 C232,80 227,89 218,88 C212,87 208,82 204,76 C198,81 196,90 202,100 C216,125 220,162 214,191 C207,216 184,228 152,231 C134,233 125,236 120,241 C115,236 106,233 88,231 C56,228 33,216 26,191 C20,162 24,125 38,100 C44,90 42,81 36,76 C32,82 28,87 22,88 C13,89 8,80 12,74 L40,32 C47,28 54,32 57,38 C66,42 72,36 72,28 L64,28 L64,16 L78,16 Z"
        fill="#FFFFFF" stroke="#FFFFFF" stroke-width="8" stroke-linejoin="round"/>
  <!-- Mitad superior cyan (#29ABE2) -->
  <path d="M78,10 L162,10 L162,16 L176,16 L176,28 L168,28 C168,36 174,42 183,38 C186,32 193,28 200,32 L228,74 C232,80 227,89 218,88 C212,87 208,82 204,76 C198,81 196,90 202,100 C203,102 205,105 206,108 L34,108 C35,105 37,102 38,100 C44,90 42,81 36,76 C32,82 28,87 22,88 C13,89 8,80 12,74 L40,32 C47,28 54,32 57,38 C66,42 72,36 72,28 L64,28 L64,16 L78,16 Z"
        fill="#29ABE2"/>
  <!-- Mitad inferior blanca (#FFFFFF) -->
  <path d="M34,108 L206,108 C217,132 219,165 214,191 C207,216 184,228 152,231 C134,233 125,236 120,241 C115,236 106,233 88,231 C56,228 33,216 26,191 C21,165 23,132 34,108 Z"
        fill="#FFFFFF"/>
  <!-- Línea divisoria horizontal y contorno azul marino (#10375C) -->
  <line x1="34" y1="108" x2="206" y2="108" stroke="#10375C" stroke-width="5.5"/>
  <path d="M78,10 L162,10 L162,16 L176,16 L176,28 L168,28 C168,36 174,42 183,38 C186,32 193,28 200,32 L228,74 C232,80 227,89 218,88 C212,87 208,82 204,76 C198,81 196,90 202,100 C216,125 220,162 214,191 C207,216 184,228 152,231 C134,233 125,236 120,241 C115,236 106,233 88,231 C56,228 33,216 26,191 C20,162 24,125 38,100 C44,90 42,81 36,76 C32,82 28,87 22,88 C13,89 8,80 12,74 L40,32 C47,28 54,32 57,38 C66,42 72,36 72,28 L64,28 L64,16 L78,16 Z"
        fill="none" stroke="#10375C" stroke-width="6" stroke-linejoin="round"/>
  <!-- Leyenda superior ARGENTINA -->
  <text x="120" y="61" text-anchor="middle" fill="#FFFFFF"
        font-family="Georgia, 'Times New Roman', serif" font-size="18.5" font-weight="700" letter-spacing="0.8">ARGENTINA</text>
  <!-- Cuadro central blanco con emblema UTN -->
  <rect x="86" y="74" width="68" height="68" fill="#FFFFFF" stroke="#10375C" stroke-width="5.5"/>
  <line x1="120" y1="86" x2="120" y2="130" stroke="#10375C" stroke-width="5.5"/>
  <line x1="98" y1="108" x2="142" y2="108" stroke="#10375C" stroke-width="5.5"/>
  <path d="M103,88 C105,100 112,106 120,106 C128,106 135,100 137,88" fill="none" stroke="#10375C" stroke-width="5.5" stroke-linecap="butt"/>
  <path d="M103,128 C105,116 112,110 120,110 C128,110 135,116 137,128" fill="none" stroke="#10375C" stroke-width="5.5" stroke-linecap="butt"/>
  <!-- Leyenda inferior AVEIT -->
  <text x="120" y="198" text-anchor="middle" fill="#10375C"
        font-family="Rockwell, 'Roboto Slab', Georgia, 'Times New Roman', serif" font-size="42" font-weight="900" letter-spacing="1.2">AVEIT</text>
</svg>"""


def _join_html(fragments: HtmlPages) -> str:
    if isinstance(fragments, str):
        return fragments
    return "\n".join(fragments)


def render_cover_page(title: str, subtitle: str) -> str:
    """Genera la portada A4 (.page-cover) sin numeración de página."""
    safe_title = html.escape(str(title), quote=False)
    safe_subtitle = html.escape(str(subtitle), quote=False)
    return f"""<section class="page-cover">
  <div class="cover-content">
    <div class="cover-shield">
      {SHIELD_SVG}
    </div>
    <h1 class="cover-title">{safe_title}</h1>
    <p class="cover-subtitle">{safe_subtitle}</p>
  </div>
</section>"""


def render_step_page(
    steps_html: HtmlPages,
    page_num: int,
    total_pages: int,
    *,
    top_aligned: bool = False,
) -> str:
    """Genera una página de pasos A4 (.page-step) con encabezado AVEIT y pie 'X de Y'."""
    body_html = _join_html(steps_html)
    container_class = "steps-container top-aligned" if top_aligned else "steps-container"
    return f"""<section class="page-step">
  <header class="step-header">
    <h2 class="step-brand-title">AVEIT | Sistema</h2>
    <p class="step-brand-url">https://aveit.frc.utn.edu.ar/</p>
    <div class="step-header-shield">
      {SHIELD_SVG}
    </div>
  </header>
  <main class="{container_class}">
    {body_html}
  </main>
  <footer class="step-footer">
    <span class="page-number">{int(page_num)} de {int(total_pages)}</span>
  </footer>
</section>"""


def render_step_row(
    step_num: int,
    text_html: str,
    ui_html: str,
    *,
    reverse: bool = False,
    note_html: str = "",
) -> str:
    """Helper opcional para construir un bloque horizontal de 2 columnas (.step-row)."""
    row_cls = "step-row reverse" if reverse else "step-row"
    note_block = f'\n      <p class="step-note">{note_html}</p>' if note_html else ""
    return f"""<article class="{row_cls}">
  <div class="step-info">
    <span class="step-pill">PASO {int(step_num)}</span>
    <p class="step-text">{text_html}</p>{note_block}
  </div>
  <div class="step-visual">
    {ui_html}
  </div>
</article>"""


def render_step_stack(
    step_num: int,
    text_html: str,
    ui_html: str,
    *,
    inline_info: bool = False,
    note_html: str = "",
) -> str:
    """Helper opcional para construir un bloque vertical centrado (.step-stack)."""
    stack_cls = "step-stack inline-info" if inline_info else "step-stack"
    note_block = f'\n      <p class="step-note">{note_html}</p>' if note_html else ""
    return f"""<article class="{stack_cls}">
  <div class="step-info">
    <span class="step-pill">PASO {int(step_num)}</span>
    <p class="step-text">{text_html}</p>{note_block}
  </div>
  <div class="step-visual">
    {ui_html}
  </div>
</article>"""


def build_document(
    doc_title: str,
    pages_html: HtmlPages,
    css_rel_path: str = "../shared/manual-base.css",
) -> str:
    """Ensambla el documento HTML5 UTF-8 completo listo para renderizado a PDF A4."""
    safe_doc_title = html.escape(str(doc_title), quote=False)
    safe_css_path = html.escape(str(css_rel_path), quote=True)
    joined_pages = _join_html(pages_html)
    return f"""<!DOCTYPE html>
<html lang="es-AR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{safe_doc_title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Sans:wght@400;500;600;700&family=Playfair+Display:wght@700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{safe_css_path}">
</head>
<body>
{joined_pages}
</body>
</html>
"""


def save_document(output_path: Union[str, Path], html_content: str) -> Path:
    """Guarda el documento HTML en UTF-8 creando directorios intermedios si faltan."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html_content, encoding="utf-8")
    return target
