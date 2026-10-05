"""Políticas de dominio, sanitización y plantillas institucionales de apertura.

Cumple con:
- CA2: Resguardo estricto de privacidad, prohibición de datos médicos o sensibles.
- Principio 6: Política de fallo cerrado ante ambigüedades médicas o abreviaturas.
- Principio 7: No filtración de datos privados en excepciones o logs.
- CA3: Clave de idempotencia determinista.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NotificationPayload:
    """Contenedor inmutable del mensaje de notificación procesal generado."""

    subject: str
    body_text: str
    body_html: str
    idempotency_key: str
    metadata: dict[str, Any]


class NotificationSanitizer:
    """Garantiza el cumplimiento estricto de CA2 y Principio 6: cero datos médicos o sensibles."""

    # Patrón de detección con política de fallo cerrado (variaciones, tildes y abreviaturas)
    FORBIDDEN_TERMS_PATTERN = re.compile(
        r"(?:\b)("
        r"diagn[oó]stic[oa]s?|diag\b\.?|"
        r"enfermedad(?:es)?|"
        r"patolog[ií]a(?:s)?|patol\b\.?|"
        r"m[eé]dic[oa]s?|med\b\.?|"
        r"salud|"
        r"lic(?:encia)?\b\.?\s+m[eé]d(?:ic[oa])?\b\.?|"
        r"cl[ií]nic[oa]s?|"
        r"s[ií]ntoma(?:s)?|"
        r"reposo|"
        r"internaci[oó]n|"
        r"quir[uú]rgic[oa]s?|"
        r"receta(?:s)?|"
        r"psiqui[aá]tric[oa]s?|"
        r"psicol[oó]gic[oa]s?|psicol\b\.?|"
        r"covid(?:-19)?"
        r")(?:\b|\.|\s|$)",
        re.IGNORECASE,
    )

    @classmethod
    def assert_no_sensitive_data(cls, text: str) -> None:
        """Evalúa el texto y lanza ValueError si detecta términos médicos o sensibles.

        Principio 7: El mensaje de error no expone el contexto ni el texto privado completo,
        únicamente la etiqueta del término detectado.
        """
        if not text:
            return

        match = cls.FORBIDDEN_TERMS_PATTERN.search(text)
        if match:
            detected_term = match.group(1).strip()
            raise ValueError(
                f"Infracción a CA2: Se detectó término sensible o médico no permitido: "
                f"'{detected_term}'."
            )


class OpeningNotificationTemplate:
    """Constructor de plantillas institucionales para notificación de apertura."""

    @classmethod
    def render(
        cls,
        *,
        expediente_numero: str,
        socio_nombre: str,
        motivo_caratula: str,
        plazo_inicio_at: datetime,
        plazo_limite_at: datetime,
        frontend_url: str,
        expediente_id: int,
        socio_id: int,
    ) -> NotificationPayload:
        """Construye la notificación de apertura verificando ausencia de datos sensibles."""
        # 1. Validación de privacidad (CA2 y Principio 6)
        NotificationSanitizer.assert_no_sensitive_data(motivo_caratula)

        fecha_inicio_str = plazo_inicio_at.strftime("%d/%m/%Y %H:%M")
        fecha_limite_str = plazo_limite_at.strftime("%d/%m/%Y %H:%M")
        enlace_seguro = f"{frontend_url.rstrip('/')}/mis-expedientes/{expediente_id}"

        subject = f"[SGD-AVEIT] Notificación de Apertura de Causa — Autos {expediente_numero}"

        body_text = (
            f"Estimado/a socio/a {socio_nombre}:\n\n"
            f"Por medio de la presente, el Tribunal de Disciplina de A.V.E.I.T. le notifica "
            f"formalmente la apertura del expediente disciplinario N° {expediente_numero}.\n\n"
            f"• Causa: Actuación disciplinaria en trámite\n"
            f"• Fecha y hora de despacho: {fecha_inicio_str}\n"
            f"• Plazo de defensa: Dispone de un término fatal e improrrogable de cinco (5) días "
            f"hábiles administrativos para presentar sus descargos "
            f"(Art. 12 Inc. 2 del Reglamento Procesal 2026).\n"
            f"• Vencimiento del plazo: {fecha_limite_str}\n\n"
            f"Por razones de confidencialidad estatutaria y protección de datos personales, "
            f"los antecedentes circunstanciados de la causa se encuentran reservados para su "
            f"consulta exclusiva ingresando a la plataforma institucional:\n"
            f"{enlace_seguro}\n\n"
            f"Atentamente,\n"
            f"Tribunal de Disciplina — A.V.E.I.T. (UTN FRC)"
        )

        body_html = (
            '<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; '
            'color: #2c3e50;">\n'
            '    <div style="background-color: #0b3c5d; padding: 20px; text-align: center; '
            'color: #ffffff;">\n'
            '        <h2 style="margin: 0;">A.V.E.I.T. — Tribunal de Disciplina</h2>\n'
            '        <p style="margin: 5px 0 0 0; font-size: 14px;">'
            "Cédula de Notificación de Apertura de Causa</p>\n"
            "    </div>\n"
            '    <div style="padding: 24px; border: 1px solid #e0e0e0; '
            'background-color: #ffffff;">\n'
            f"        <p>Estimado/a socio/a <strong>{socio_nombre}</strong>:</p>\n"
            f"        <p>Le notificamos formalmente la apertura del expediente disciplinario "
            f"<strong>{expediente_numero}</strong>.</p>\n"
            '        <div style="background-color: #f8f9fa; border-left: 4px solid #0b3c5d; '
            'padding: 12px; margin: 16px 0;">\n'
            '            <p style="margin: 4px 0;"><strong>Causa:</strong> '
            "Actuación disciplinaria en trámite</p>\n"
            f'            <p style="margin: 4px 0;"><strong>Fecha de Despacho:</strong> '
            f"{fecha_inicio_str}</p>\n"
            '            <p style="margin: 4px 0;"><strong>Plazo de Descargo:</strong> '
            "5 días hábiles administrativos</p>\n"
            '            <p style="margin: 4px 0; color: #b71c1c;">'
            f"<strong>Vencimiento Fatal:</strong> {fecha_limite_str}</p>\n"
            "        </div>\n"
            "        <p>Por razones de confidencialidad y protección de datos personales, los "
            "antecedentes circunstanciados se encuentran reservados para su consulta exclusiva. "
            "Podrá acceder a las actuaciones y presentar sus descargos en el portal seguro:</p>\n"
            '        <div style="text-align: center; margin: 24px 0;">\n'
            f'            <a href="{enlace_seguro}" style="background-color: #0b3c5d; '
            "color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 4px; "
            'font-weight: bold; display: inline-block;">Acceder a Mis Expedientes y Descargos</a>\n'
            "        </div>\n"
            '        <p style="font-size: 12px; color: #7f8c8d;">Nota: El acceso a la causa '
            "requiere autenticación institucional obligatoria.</p>\n"
            "    </div>\n"
            '    <div style="background-color: #f1f1f1; padding: 12px; text-align: center; '
            'font-size: 12px; color: #7f8c8d;">\n'
            "        Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos — UTN FRC\n"
            "    </div>\n"
            "</div>"
        )

        idempotency_key = f"opening-expediente-{expediente_id}-socio-{socio_id}"

        metadata = {
            "expediente_id": expediente_id,
            "socio_id": socio_id,
            "tipo_notificacion": "APERTURA_EXPEDIENTE",
            "expediente_numero": expediente_numero,
        }

        return NotificationPayload(
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            idempotency_key=idempotency_key,
            metadata=metadata,
        )
