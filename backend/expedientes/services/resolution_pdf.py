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
    """Construye el PDF de previsualización usando únicamente la resolución."""

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
    story = [Paragraph("RESOLUCIÓN", title_style), Spacer(1, 12)]

    if resolucion.estado == "DRAFT":
        story.append(Paragraph("BORRADOR - SIN VALIDEZ OFICIAL", styles["Heading2"]))
        story.append(Spacer(1, 10))

    story.extend(
        [
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
            Paragraph("ARTÍCULOS RESOLUTIVOS", styles["Heading2"]),
            Paragraph(_paragraph_text(resolucion.articulos_resolutivos), styles["BodyText"]),
        ]
    )
    document.build(story)
    return output.getvalue()
