"""Generación de previsualizaciones PDF de resoluciones, sin emisión."""

from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _paragraph_text(value: object) -> str:
    """Escapa texto de dominio y conserva sus saltos de línea."""
    return escape(str(value or "")).replace("\n", "<br/>")


def build_resolution_preview_pdf(resolucion) -> bytes:
    """Construye el PDF de previsualización institucional de la resolución."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    story = [
        Paragraph("TRIBUNAL DE DISCIPLINA — A.V.E.I.T. (UTN FRC)", styles["Heading3"]),
        Spacer(1, 6),
        Paragraph("RESOLUCIÓN", title_style),
        Spacer(1, 12),
    ]

    if resolucion.estado == "DRAFT":
        story.append(Paragraph("BORRADOR - SIN VALIDEZ OFICIAL", styles["Heading2"]))
        story.append(Spacer(1, 10))

    raw_numero = (resolucion.numero_expediente_snapshot or "").replace("EXP-", "").strip()
    identificador_res = f"RESOLUCIÓN {raw_numero}" if raw_numero else "RESOLUCIÓN"

    story.extend(
        [
            Paragraph(
                f"Identificación: {_paragraph_text(identificador_res)}",
                styles["Normal"],
            ),
            Paragraph(
                f"Expediente: {_paragraph_text(resolucion.numero_expediente_snapshot)}",
                styles["Normal"],
            ),
            Paragraph(
                f"Versión de resolución: {_paragraph_text(resolucion.version)}",
                styles["Normal"],
            ),
            Paragraph(
                f"Versión de plantilla: {_paragraph_text(resolucion.plantilla_version)}",
                styles["Normal"],
            ),
            Spacer(1, 14),
            Paragraph("VISTOS", styles["Heading2"]),
            Paragraph(_paragraph_text(resolucion.vistos), styles["BodyText"]),
            Spacer(1, 10),
            Paragraph("CONSIDERANDOS", styles["Heading2"]),
            Paragraph(_paragraph_text(resolucion.considerandos), styles["BodyText"]),
            Spacer(1, 10),
            Paragraph("SE RESUELVE — ARTÍCULOS RESOLUTIVOS", styles["Heading2"]),
            Paragraph(_paragraph_text(resolucion.articulos_resolutivos), styles["BodyText"]),
            Spacer(1, 20),
            Paragraph("TRIBUNAL DE DISCIPLINA — FIRMANTES", styles["Heading3"]),
            Spacer(1, 8),
        ]
    )

    firmantes_dict = {}
    for f in getattr(resolucion, "firmantes", []) or []:
        anio = f.get("social_year") or f.get("anio_social")
        if anio:
            firmantes_dict[int(anio)] = f.get("etiqueta") or f.get("firma") or str(f)

    for anio in (4, 5, 6):
        texto_firmante = firmantes_dict.get(anio, "Pendiente de firma")
        story.append(
            Paragraph(f"{anio}.º Año Social: {_paragraph_text(texto_firmante)}", styles["Normal"])
        )

    document.build(story)
    return output.getvalue()
