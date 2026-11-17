"""Generación de previsualizaciones y documentos PDF institucionales de resoluciones."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from django.utils import timezone
from reportlab.graphics.shapes import Drawing, Polygon, Rect
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

TD_LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "td_logo.png"

COLOR_NAVY = colors.HexColor("#151846")
COLOR_CYAN = colors.HexColor("#0097A7")
COLOR_CYAN_BRIGHT = colors.HexColor("#13B5EA")
COLOR_TEXT = colors.HexColor("#1E293B")
COLOR_MUTED = colors.HexColor("#64748B")
COLOR_SURFACE = colors.HexColor("#F8FAFC")
COLOR_BORDER = colors.HexColor("#E2E8F0")
COLOR_DRAFT_BG = colors.HexColor("#FFFBEB")
COLOR_DRAFT_BORDER = colors.HexColor("#F59E0B")
COLOR_DRAFT_TEXT = colors.HexColor("#B45309")
COLOR_SIGNED_BG = colors.HexColor("#F0FDF4")
COLOR_SIGNED_BORDER = colors.HexColor("#86EFAC")
COLOR_SIGNED_TEXT = colors.HexColor("#15803D")

MESES_ES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _paragraph_text(value: object) -> str:
    """Escapa texto de dominio y conserva sus saltos de línea."""
    return escape(str(value or "")).replace("\n", "<br/>")


def _format_fecha_cordoba(resolucion) -> str:
    """Formatea la fecha institucional de la resolución al estilo AVEIT."""
    dt = getattr(resolucion, "issued_at", None) or getattr(resolucion, "created_at", None)
    if dt is None:
        dt = timezone.now()
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    mes = MESES_ES[dt.month - 1].capitalize()
    return f"Córdoba, {dt.day} de {mes} de {dt.year}, {dt.hour:02d}:{dt.minute:02d} hs"


def _build_aveit_shield(size: float = 46.0) -> Drawing:
    """Dibuja el escudo vectorial institucional de A.V.E.I.T. en cyan."""
    d = Drawing(size, size)
    s = size / 100.0
    # Silueta exterior del escudo hexagonal/diamante redondeado
    outer = Polygon(
        [
            30 * s,
            94 * s,
            70 * s,
            94 * s,
            88 * s,
            66 * s,
            50 * s,
            6 * s,
            12 * s,
            66 * s,
        ],
        fillColor=COLOR_CYAN_BRIGHT,
        strokeColor=COLOR_CYAN_BRIGHT,
        strokeWidth=0,
    )
    d.add(outer)
    # Trazos internos blancos geométricos (T / flecha institucional)
    d.add(Rect(45 * s, 20 * s, 10 * s, 60 * s, fillColor=colors.white, strokeWidth=0))
    d.add(Rect(24 * s, 72 * s, 52 * s, 9 * s, fillColor=colors.white, strokeWidth=0))
    d.add(
        Polygon(
            [
                24 * s,
                60 * s,
                50 * s,
                84 * s,
                76 * s,
                60 * s,
                69 * s,
                54 * s,
                50 * s,
                72 * s,
                31 * s,
                54 * s,
            ],
            fillColor=colors.white,
            strokeWidth=0,
        )
    )
    d.add(
        Polygon(
            [
                31 * s,
                38 * s,
                50 * s,
                20 * s,
                69 * s,
                38 * s,
                63 * s,
                44 * s,
                50 * s,
                31 * s,
                37 * s,
                44 * s,
            ],
            fillColor=colors.white,
            strokeWidth=0,
        )
    )
    return d


def _section_header(title: str, style: ParagraphStyle) -> Table:
    """Crea un encabezado de sección moderno con acento lateral cyan."""
    tbl = Table([[Paragraph(title, style)]], colWidths=[172 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("LINEBEFORE", (0, 0), (0, 0), 3, COLOR_CYAN_BRIGHT),
                ("BACKGROUND", (0, 0), (0, 0), COLOR_SURFACE),
                ("LEFTPADDING", (0, 0), (0, 0), 8),
                ("RIGHTPADDING", (0, 0), (0, 0), 8),
                ("TOPPADDING", (0, 0), (0, 0), 5),
                ("BOTTOMPADDING", (0, 0), (0, 0), 5),
            ]
        )
    )
    return tbl


def build_resolution_preview_pdf(resolucion) -> bytes:
    """Construye el PDF institucional moderno de la resolución del Tribunal de Disciplina."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        pageCompression=0,
        title=f"Resolución {resolucion.numero_expediente_snapshot or ''}".strip(),
        author="Tribunal de Disciplina — A.V.E.I.T.",
    )

    base_styles = getSampleStyleSheet()

    inst_style = ParagraphStyle(
        "AveitInstitution",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=COLOR_NAVY,
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    res_title_style = ParagraphStyle(
        "AveitResTitle",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=COLOR_NAVY,
        alignment=TA_LEFT,
        spaceBefore=0,
        spaceAfter=2,
    )
    ref_style = ParagraphStyle(
        "AveitRef",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=COLOR_MUTED,
        alignment=TA_LEFT,
    )
    date_style = ParagraphStyle(
        "AveitDate",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=COLOR_MUTED,
        alignment=TA_RIGHT,
    )
    meta_style = ParagraphStyle(
        "AveitMeta",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=COLOR_TEXT,
    )
    draft_style = ParagraphStyle(
        "AveitDraft",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=13,
        textColor=COLOR_DRAFT_TEXT,
        alignment=TA_CENTER,
    )
    section_title_style = ParagraphStyle(
        "AveitSectionTitle",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=COLOR_NAVY,
        spaceBefore=0,
        spaceAfter=0,
    )
    body_style = ParagraphStyle(
        "AveitBody",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.8,
        leading=14.5,
        textColor=COLOR_TEXT,
        alignment=TA_JUSTIFY,
        spaceBefore=0,
        spaceAfter=0,
    )
    resolutivo_style = ParagraphStyle(
        "AveitResolutivo",
        parent=body_style,
        leftIndent=10,
        spaceAfter=4,
    )
    firmantes_hdr_style = ParagraphStyle(
        "AveitFirmantesHdr",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=COLOR_NAVY,
        alignment=TA_CENTER,
    )
    firma_year_style = ParagraphStyle(
        "AveitFirmaYear",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_MUTED,
        alignment=TA_CENTER,
    )
    firma_name_style = ParagraphStyle(
        "AveitFirmaName",
        parent=base_styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=11,
        textColor=COLOR_SIGNED_TEXT,
        alignment=TA_CENTER,
    )
    firma_pending_style = ParagraphStyle(
        "AveitFirmaPending",
        parent=base_styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.2,
        leading=11,
        textColor=COLOR_MUTED,
        alignment=TA_CENTER,
    )

    raw_numero = (resolucion.numero_expediente_snapshot or "").replace("EXP-", "").strip()
    identificador_res = f"RESOLUCIÓN {raw_numero}" if raw_numero else "RESOLUCIÓN"

    expediente = getattr(resolucion, "expediente", None)
    titulo_ref = ""
    if expediente is not None:
        solicitud = getattr(expediente, "solicitud_t01", None)
        if solicitud and getattr(solicitud, "titulo", None):
            titulo_ref = str(solicitud.titulo).strip()
        elif getattr(expediente, "motivo", None):
            titulo_ref = str(expediente.motivo).strip()

    # 1. Encabezado con escudo oficial del Tribunal de Disciplina y título institucional
    if TD_LOGO_PATH.exists():
        shield = Image(str(TD_LOGO_PATH), width=48.0, height=48.0)
    else:
        shield = _build_aveit_shield(46.0)
    shield_table = Table([[shield]], colWidths=[172 * mm])
    shield_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    story = [
        shield_table,
        Paragraph("TRIBUNAL DE DISCIPLINA — A.V.E.I.T. (UTN FRC)", inst_style),
        Spacer(1, 3),
        HRFlowable(width="100%", thickness=1.5, color=COLOR_NAVY, spaceBefore=2, spaceAfter=1),
        HRFlowable(
            width="100%", thickness=0.75, color=COLOR_CYAN_BRIGHT, spaceBefore=0, spaceAfter=10
        ),
    ]

    # 2. Banner de estado borrador (si aplica)
    if resolucion.estado == "DRAFT":
        draft_banner = Table(
            [[Paragraph("BORRADOR - SIN VALIDEZ OFICIAL", draft_style)]],
            colWidths=[172 * mm],
        )
        draft_banner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), COLOR_DRAFT_BG),
                    ("BOX", (0, 0), (-1, -1), 0.75, COLOR_DRAFT_BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.extend([draft_banner, Spacer(1, 8)])

    # 3. Título RESOLUCIÓN, Referencia y Fecha Córdoba
    fecha_str = _format_fecha_cordoba(resolucion)
    header_row = [
        [
            Paragraph(_paragraph_text(identificador_res), res_title_style),
            Paragraph(_paragraph_text(fecha_str), date_style),
        ]
    ]
    if titulo_ref:
        header_row.append(
            [
                Paragraph(f"<b>Ref:</b> {_paragraph_text(titulo_ref)}", ref_style),
                "",
            ]
        )

    title_block = Table(header_row, colWidths=[102 * mm, 70 * mm])
    title_block.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                *([("SPAN", (0, 1), (1, 1))] if len(header_row) > 1 else []),
            ]
        )
    )
    story.extend([title_block, Spacer(1, 6)])

    # 4. Tarjeta de metadatos trazables
    meta_table = Table(
        [
            [
                Paragraph(
                    f"<b>Identificación:</b> {_paragraph_text(identificador_res)}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Expediente:</b> {_paragraph_text(resolucion.numero_expediente_snapshot)}",
                    meta_style,
                ),
            ],
            [
                Paragraph(
                    f"<b>Versión de resolución:</b> {_paragraph_text(resolucion.version)}",
                    meta_style,
                ),
                Paragraph(
                    f"<b>Versión de plantilla:</b> {_paragraph_text(resolucion.plantilla_version)}",
                    meta_style,
                ),
            ],
        ],
        colWidths=[86 * mm, 86 * mm],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_SURFACE),
                ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, COLOR_BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend([meta_table, Spacer(1, 12)])

    # 5. Secciones Canónicas: VISTOS, CONSIDERANDOS, SE RESUELVE
    story.extend(
        [
            _section_header("VISTOS", section_title_style),
            Spacer(1, 5),
            Paragraph(_paragraph_text(resolucion.vistos), body_style),
            Spacer(1, 11),
            _section_header("CONSIDERANDOS", section_title_style),
            Spacer(1, 5),
            Paragraph(_paragraph_text(resolucion.considerandos), body_style),
            Spacer(1, 11),
            _section_header("SE RESUELVE — ARTÍCULOS RESOLUTIVOS", section_title_style),
            Spacer(1, 5),
        ]
    )

    for bloque in (str(resolucion.articulos_resolutivos or "")).split("\n\n"):
        if bloque.strip():
            story.append(Paragraph(_paragraph_text(bloque.strip()), resolutivo_style))
    story.append(Spacer(1, 16))

    # 6. Grilla moderna de Firmas Colegiadas por Año Social (4.º, 5.º y 6.º)
    story.extend(
        [
            HRFlowable(
                width="100%", thickness=0.6, color=COLOR_BORDER, spaceBefore=0, spaceAfter=8
            ),
            Paragraph("TRIBUNAL DE DISCIPLINA — FIRMANTES", firmantes_hdr_style),
            Spacer(1, 8),
        ]
    )

    firmantes_dict: dict[int, str] = {}
    for f in getattr(resolucion, "firmantes", []) or []:
        anio = f.get("social_year") or f.get("anio_social")
        if anio:
            firmantes_dict[int(anio)] = f.get("etiqueta") or f.get("firma") or str(f)

    cards_row = []
    card_styles = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
        ("BOX", (0, 0), (-1, -1), 0.6, COLOR_BORDER),
    ]

    for idx, anio in enumerate((4, 5, 6)):
        texto_firmante = firmantes_dict.get(anio)
        if texto_firmante:
            cell_content = [
                Paragraph(f"{anio}.º Año Social", firma_year_style),
                Spacer(1, 3),
                Paragraph(_paragraph_text(texto_firmante), firma_name_style),
            ]
            card_styles.append(("BACKGROUND", (idx, 0), (idx, 0), COLOR_SIGNED_BG))
        else:
            cell_content = [
                Paragraph(f"{anio}.º Año Social", firma_year_style),
                Spacer(1, 3),
                Paragraph("Pendiente de firma", firma_pending_style),
            ]
            card_styles.append(("BACKGROUND", (idx, 0), (idx, 0), COLOR_SURFACE))
        cards_row.append(cell_content)

    firmas_table = Table([cards_row], colWidths=[57.3 * mm, 57.3 * mm, 57.4 * mm])
    firmas_table.setStyle(TableStyle(card_styles))
    story.append(firmas_table)

    contenido_hash = (getattr(resolucion, "contenido_hash", "") or "").strip()

    def _draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(COLOR_BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(19 * mm, 13 * mm, 191 * mm, 13 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(COLOR_MUTED)
        footer_left = f"A.V.E.I.T. — Tribunal de Disciplina • {identificador_res}"
        if contenido_hash:
            footer_left += f" • SHA-256: {contenido_hash[:16]}…"
        canvas.drawString(19 * mm, 9 * mm, footer_left)
        canvas.drawRightString(191 * mm, 9 * mm, f"Página {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return output.getvalue()
