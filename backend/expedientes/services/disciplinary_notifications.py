"""Orquestador centralizado de notificaciones disciplinarias vía EmailOutbox (S5-07.3).

Garantiza:
- Persistencia atómica en EmailOutbox + EmailAttachment dentro de la transacción de negocio.
- Idempotencia determinista por evento, entidad y destinatario.
- Etiquetado `es_disciplinario=True` para aplicación automática de EMAIL_BCC_INSTITUCIONAL.
- Adjuntos PDF oficiales codificados en Base64 para cédulas y resoluciones.
"""

from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Any

from django.conf import settings
from django.utils import timezone

from expedientes.services.resolution_pdf import build_official_resolution_pdf
from notifications.models import EmailOutbox
from notifications.services import EmailDispatcherService, render_institutional_email_html


def _safe_filename_part(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()) or "documento"


def _socio_display(socio) -> str:
    ident = getattr(socio, "numero_socio", None) or getattr(socio, "legajo", "")
    nombre = f"{getattr(socio, 'first_name', '')} {getattr(socio, 'last_name', '')}".strip()
    return f"{nombre} (N.º de socio: {ident})" if nombre else f"N.º de socio: {ident}"


def _involved_socios(expediente) -> list:
    socios_by_id: dict[int, Any] = {}
    if getattr(expediente, "socio", None):
        socios_by_id[expediente.socio.id] = expediente.socio
    if hasattr(expediente, "socios"):
        for s in expediente.socios.all():
            socios_by_id.setdefault(s.id, s)
    return list(socios_by_id.values())


def _enqueue_disciplinary_email(
    *,
    to: list[str],
    subject: str,
    body_text: str,
    idempotency_key: str,
    metadata: dict[str, Any],
    body_html: str | None = None,
    attachments: list[dict[str, str]] | None = None,
) -> EmailOutbox | None:
    clean_to = [addr.strip() for addr in to if addr and addr.strip()]
    if not clean_to:
        return None

    meta = dict(metadata)
    meta["es_disciplinario"] = True

    outbox, _ = EmailDispatcherService.create_or_get_outbox(
        {
            "to": clean_to,
            "subject": subject[:255],
            "body_text": body_text,
            "body_html": body_html,
            "idempotency_key": idempotency_key,
            "metadata": meta,
            "attachments": attachments or [],
        }
    )
    return outbox


def enqueue_solicitud_t01_applicant_ack(solicitud, expediente) -> EmailOutbox | None:
    """Evento 2: Acuse formal de recibo al solicitante tras emitir Solicitud T01."""
    solicitante = getattr(solicitud, "solicitante", None)
    email = (getattr(solicitante, "email", "") or "").strip()
    if not email:
        return None

    numero = getattr(solicitud, "numero_expediente", None) or (
        expediente.numero if expediente else str(solicitud.id)
    )
    titulo = getattr(solicitud, "titulo", "") or getattr(solicitud, "motivo", "")
    accion = "Mérito (+)" if getattr(solicitud, "tipo_accion", "") == "MERIT" else "Sanción (-)"

    body_text = (
        f"Estimado/a {_socio_display(solicitante)}:\n\n"
        f"Acusamos recibo formal de su Solicitud T01 registrada bajo el expediente "
        f"N.º {numero}.\n\n"
        f"• Tipo de acción: {accion}\n"
        f"• Puntos solicitados: {solicitud.puntos}\n"
        f"• Carátula: {titulo}\n\n"
        f"El expediente quedó formalmente ingresado para su sustanciación ante el "
        f"Tribunal de Disciplina de A.V.E.I.T.\n\n"
        f"Atentamente,\n"
        f"Sistema de Gestión Disciplinaria — A.V.E.I.T. (UTN FRC)"
    )

    body_html = render_institutional_email_html(
        subtitle="Acuse de Recibo — Solicitud T01",
        greeting=f"Estimado/a {_socio_display(solicitante)}:",
        intro_paragraphs=[
            f"Acusamos recibo formal de su Solicitud T01 registrada bajo el "
            f"expediente N.º {numero}."
        ],
        detail_rows=[
            ("Expediente", str(numero), None),
            ("Tipo de acción", accion, None),
            ("Puntos solicitados", str(solicitud.puntos), None),
            ("Carátula", str(titulo), None),
        ],
        closing_paragraphs=[
            "El expediente quedó formalmente ingresado para su sustanciación ante el "
            "Tribunal de Disciplina de A.V.E.I.T."
        ],
        note="Conservá este acuse como constancia digital de presentación.",
    )

    return _enqueue_disciplinary_email(
        to=[email],
        subject=f"[SGD-AVEIT] Acuse de Recibo — Solicitud T01 ({numero})",
        body_text=body_text,
        body_html=body_html,
        idempotency_key=f"t01-solicitante-ack-{solicitud.id}",
        metadata={
            "tipo_notificacion": "ACUSE_SOLICITANTE_T01",
            "solicitud_id": str(solicitud.id),
            "expediente_id": expediente.id if expediente else None,
            "expediente_numero": numero,
        },
    )


def enqueue_descargo_received_notice(
    *,
    expediente,
    descargo,
    socio,
    version_num: int,
    es_correccion: bool,
) -> EmailOutbox | None:
    """Evento 6: Aviso al Tribunal de Disciplina al presentarse o corregirse un descargo T02/T03."""
    tribunal_email = (getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org") or "").strip()
    if not tribunal_email:
        return None

    operacion = "corrección" if es_correccion else "presentación"
    fecha_recepcion = timezone.localtime(descargo.presentado_at).strftime("%d/%m/%Y %H:%M")
    body_text = (
        f"Estimados miembros del Tribunal de Disciplina:\n\n"
        f"Se registró la {operacion} de descargo ({descargo.tipo}, versión {version_num}) "
        f"correspondiente al expediente {expediente.numero}.\n\n"
        f"• Socio imputado: {_socio_display(socio)}\n"
        f"• Fecha y hora de recepción: {fecha_recepcion} hs\n\n"
        f"La documentación queda disponible para su revisión en la Sala del Tribunal.\n\n"
        f"Sistema de Gestión Disciplinaria — A.V.E.I.T. (UTN FRC)"
    )

    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200").rstrip("/")
    body_html = render_institutional_email_html(
        subtitle="Recepción de Descargo en Sala del Tribunal",
        greeting="Estimados miembros del Tribunal de Disciplina:",
        intro_paragraphs=[
            f"Se registró la {operacion} de descargo correspondiente al "
            f"expediente {expediente.numero}."
        ],
        detail_rows=[
            ("Expediente", str(expediente.numero), None),
            ("Tipo de descargo", f"{descargo.tipo} (versión {version_num})", None),
            ("Socio imputado", _socio_display(socio), None),
            ("Fecha y hora de recepción", f"{fecha_recepcion} hs", None),
        ],
        closing_paragraphs=[
            "La documentación queda disponible para su revisión en el módulo "
            "de gestión del Tribunal."
        ],
        cta_label="Ir a Gestionar Expedientes",
        cta_url=f"{base_url}/gestionar-expedientes",
    )

    return _enqueue_disciplinary_email(
        to=[tribunal_email],
        subject=(
            f"[SGD-AVEIT] Descargo {descargo.tipo} recibido — "
            f"Expediente {expediente.numero} (v{version_num})"
        ),
        body_text=body_text,
        body_html=body_html,
        idempotency_key=f"descargo-recibido-{expediente.id}-socio-{socio.id}-v{version_num}",
        metadata={
            "tipo_notificacion": "DESCARGO_RECIBIDO_TD",
            "expediente_id": expediente.id,
            "expediente_numero": expediente.numero,
            "descargo_id": descargo.id,
            "socio_id": socio.id,
            "version": version_num,
            "tipo_descargo": descargo.tipo,
        },
    )


def enqueue_deadline_reminder(
    *,
    expediente,
    socio,
    plazo_limite_at: datetime,
) -> EmailOutbox | None:
    """Evento 7: Recordatorio preventivo 24h antes del vencimiento del plazo de descargo."""
    email = (getattr(socio, "email", "") or "").strip()
    if not email:
        return None

    limite_str = timezone.localtime(plazo_limite_at).strftime("%d/%m/%Y %H:%M hs")
    base_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200").rstrip("/")
    enlace = f"{base_url}/mis-expedientes/{expediente.id}"

    body_text = (
        f"Estimado/a {_socio_display(socio)}:\n\n"
        f"Le recordamos que el plazo perentorio para presentar o corregir su descargo/apelación "
        f"en el expediente {expediente.numero} vence próximamente.\n\n"
        f"• Vencimiento fatal: {limite_str}\n"
        f"• Acceso directo: {enlace}\n\n"
        f"Transcurrido dicho término, el expediente pasará automáticamente a revisión del "
        f"Tribunal de Disciplina.\n\n"
        f"Atentamente,\n"
        f"Tribunal de Disciplina — A.V.E.I.T. (UTN FRC)"
    )

    body_html = render_institutional_email_html(
        subtitle="Recordatorio de Vencimiento Inminente",
        greeting=f"Estimado/a {_socio_display(socio)}:",
        intro_paragraphs=[
            f"Le recordamos que el plazo perentorio para presentar o corregir su "
            f"descargo/apelación en el expediente {expediente.numero} vence próximamente."
        ],
        detail_rows=[
            ("Expediente", str(expediente.numero), None),
            ("Vencimiento fatal", limite_str, "#b71c1c"),
        ],
        closing_paragraphs=[
            "Transcurrido dicho término, el expediente pasará automáticamente a revisión del "
            "Tribunal de Disciplina."
        ],
        cta_label="Acceder a Mis Expedientes",
        cta_url=enlace,
        note="El acceso requiere autenticación institucional obligatoria.",
    )

    return _enqueue_disciplinary_email(
        to=[email],
        subject=(
            f"[SGD-AVEIT] Recordatorio: vencimiento inminente de plazo — "
            f"Expediente {expediente.numero}"
        ),
        body_text=body_text,
        body_html=body_html,
        idempotency_key=f"deadline-reminder-{expediente.id}-socio-{socio.id}",
        metadata={
            "tipo_notificacion": "RECORDATORIO_VENCIMIENTO_PLAZO",
            "expediente_id": expediente.id,
            "expediente_numero": expediente.numero,
            "socio_id": socio.id,
            "plazo_limite_at": plazo_limite_at.isoformat(),
        },
    )


def enqueue_tribunal_substitution_notices(expediente, state) -> EmailOutbox | None:
    """Evento 8: Aviso a integrantes del TD ante apartamiento y designación de suplente."""
    if not state.composition.separated:
        return None

    destinatarios: list[str] = []
    for seat in state.composition.seats:
        if seat.member is not None:
            entry = state.entry(seat.member.socio_id)
            mail = (getattr(entry.socio, "email", "") or "").strip()
            if mail and mail not in destinatarios:
                destinatarios.append(mail)

    tribunal_email = (getattr(settings, "TRIBUNAL_EMAIL", "") or "").strip()
    if not destinatarios and tribunal_email:
        destinatarios.append(tribunal_email)

    if not destinatarios:
        return None

    apartados_txt = "\n".join(
        f"- {state.entry(m.socio_id).member.label} ({m.social_year}.º año)"
        for m in state.composition.separated
    )
    reemplazos_txt = "\n".join(
        f"- {seat.social_year}.º año: {state.entry(seat.member.socio_id).member.label} "
        f"({'Suplente' if seat.replaces else 'Titular'})"
        for seat in state.composition.seats
        if seat.member is not None
    )

    body_text = (
        f"Estimados integrantes del Tribunal de Disciplina:\n\n"
        f"Se informa la integración automática del cuerpo para el expediente {expediente.numero} "
        f"conforme al Art. 95 del Estatuto y Art. 24 del Reglamento Procesal.\n\n"
        f"Integrantes apartados por ser parte interesada:\n{apartados_txt}\n\n"
        f"Composición resultante del Tribunal para esta causa:\n{reemplazos_txt}\n\n"
        f"Sistema de Gestión Disciplinaria — A.V.E.I.T. (UTN FRC)"
    )

    apartados_inline = ", ".join(
        f"{state.entry(m.socio_id).member.label} ({m.social_year}.º año)"
        for m in state.composition.separated
    )
    reemplazos_inline = " | ".join(
        f"{seat.social_year}.º año: {state.entry(seat.member.socio_id).member.label} "
        f"({'Suplente' if seat.replaces else 'Titular'})"
        for seat in state.composition.seats
        if seat.member is not None
    )
    body_html = render_institutional_email_html(
        subtitle="Apartamiento e Integración de Suplente en TD",
        greeting="Estimados integrantes del Tribunal de Disciplina:",
        intro_paragraphs=[
            f"Se informa la integración automática del cuerpo para el expediente "
            f"{expediente.numero} conforme al Art. 95 del Estatuto y Art. 24 del RPD."
        ],
        detail_rows=[
            ("Expediente", str(expediente.numero), None),
            ("Apartados", apartados_inline or "Ninguno", None),
            ("Composición resultante", reemplazos_inline or "Sin asientos asignados", None),
        ],
        note="Los integrantes apartados quedan bloqueados en esta causa por ser parte interesada.",
    )

    return _enqueue_disciplinary_email(
        to=destinatarios,
        subject=(
            f"[SGD-AVEIT] Apartamiento e integración de suplente en TD — "
            f"Expediente {expediente.numero}"
        ),
        body_text=body_text,
        body_html=body_html,
        idempotency_key=f"td-suplencia-expediente-{expediente.pk}",
        metadata={
            "tipo_notificacion": "APARTAMIENTO_SUPLENCIA_TD",
            "expediente_id": expediente.pk,
            "expediente_numero": expediente.numero,
        },
    )


def enqueue_resolution_notifications(resolucion) -> list[EmailOutbox]:
    """Eventos 9 y 10: Notifica la Resolución Final emitida con PDF adjunto al socio y a CD."""
    expediente = resolucion.expediente
    if expediente is None:
        return []

    pdf_bytes = build_official_resolution_pdf(resolucion)
    pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    safe_num = _safe_filename_part(resolucion.numero_expediente_snapshot or expediente.numero)
    attachment = {
        "filename": f"resolucion_{safe_num}_v{resolucion.version}.pdf",
        "content_base64": pdf_b64,
        "mimetype": "application/pdf",
    }

    medidas_txt = ", ".join(resolucion.medidas) if resolucion.medidas else "Sin medidas adicionales"
    enqueued: list[EmailOutbox] = []

    # Evento 9: Al/los socio/s involucrado/s con dictamen, puntos y PDF oficial adjunto
    for socio in _involved_socios(expediente):
        email = (getattr(socio, "email", "") or "").strip()
        if not email:
            continue
        body_socio = (
            f"Estimado/a {_socio_display(socio)}:\n\n"
            f"El Tribunal de Disciplina de A.V.E.I.T. ha emitido la Resolución Final "
            f"correspondiente al expediente N.º {expediente.numero}.\n\n"
            f"• Dictamen / Puntos finales: {resolucion.puntos_finales}\n"
            f"• Medidas dispuestas: {medidas_txt}\n"
            f"• Hash de integridad: {resolucion.contenido_hash}\n\n"
            f"Se adjunta a la presente el documento oficial de la resolución en formato PDF.\n\n"
            f"Atentamente,\n"
            f"Tribunal de Disciplina — A.V.E.I.T. (UTN FRC)"
        )
        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200").rstrip("/")
        body_socio_html = render_institutional_email_html(
            subtitle="Resolución Final Emitida",
            greeting=f"Estimado/a {_socio_display(socio)}:",
            intro_paragraphs=[
                f"El Tribunal de Disciplina de A.V.E.I.T. ha emitido la Resolución Final "
                f"correspondiente al expediente N.º {expediente.numero}."
            ],
            detail_rows=[
                ("Expediente", str(expediente.numero), None),
                ("Dictamen / Puntos finales", str(resolucion.puntos_finales), "#0b3c5d"),
                ("Medidas dispuestas", medidas_txt, None),
                ("Hash de integridad", str(resolucion.contenido_hash), None),
            ],
            closing_paragraphs=[
                "Se adjunta a la presente el documento oficial de la resolución en formato PDF."
            ],
            cta_label="Ver en Mis Expedientes",
            cta_url=f"{base_url}/mis-expedientes/{expediente.id}",
        )
        outbox = _enqueue_disciplinary_email(
            to=[email],
            subject=f"[SGD-AVEIT] Resolución Final Emitida — Expediente {expediente.numero}",
            body_text=body_socio,
            body_html=body_socio_html,
            idempotency_key=f"resolucion-emitida-{resolucion.id}-socio-{socio.id}",
            metadata={
                "tipo_notificacion": "RESOLUCION_FINAL_SOCIO",
                "resolucion_id": resolucion.id,
                "expediente_id": expediente.id,
                "expediente_numero": expediente.numero,
                "socio_id": socio.id,
            },
            attachments=[attachment],
        )
        if outbox:
            enqueued.append(outbox)

    # Evento 10: A Comisión Directiva para conocimiento y archivo
    cd_email = (
        getattr(settings, "CD_EMAIL", "") or getattr(settings, "COMISION_DIRECTIVA_EMAIL", "") or ""
    ).strip()
    if cd_email:
        involucrados_str = ", ".join(_socio_display(s) for s in _involved_socios(expediente))
        body_cd = (
            f"Estimada Comisión Directiva:\n\n"
            f"Para su conocimiento y archivo institucional, se comunica la emisión oficial "
            f"de la Resolución del expediente N.º {expediente.numero}.\n\n"
            f"• Socio(s) involucrado(s): {involucrados_str}\n"
            f"• Puntos finales aplicados: {resolucion.puntos_finales}\n"
            f"• Medidas dispuestas: {medidas_txt}\n"
            f"• Hash de integridad: {resolucion.contenido_hash}\n\n"
            f"Se adjunta la resolución oficial firmada en formato PDF.\n\n"
            f"Tribunal de Disciplina — A.V.E.I.T. (UTN FRC)"
        )
        body_cd_html = render_institutional_email_html(
            header_title="A.V.E.I.T. — Tribunal de Disciplina",
            subtitle="Notificación Oficial de Resolución a Comisión Directiva",
            greeting="Estimada Comisión Directiva:",
            intro_paragraphs=[
                f"Para su conocimiento y archivo institucional, se comunica la emisión oficial "
                f"de la Resolución del expediente N.º {expediente.numero}."
            ],
            detail_rows=[
                ("Expediente", str(expediente.numero), None),
                ("Socio(s) involucrado(s)", involucrados_str, None),
                ("Puntos finales aplicados", str(resolucion.puntos_finales), "#0b3c5d"),
                ("Medidas dispuestas", medidas_txt, None),
                ("Hash de integridad", str(resolucion.contenido_hash), None),
            ],
            closing_paragraphs=[
                "Se adjunta la resolución oficial firmada en formato PDF."
            ],
        )
        outbox_cd = _enqueue_disciplinary_email(
            to=[cd_email],
            subject=(
                f"[SGD-AVEIT] Notificación de Resolución a CD — Expediente {expediente.numero}"
            ),
            body_text=body_cd,
            body_html=body_cd_html,
            idempotency_key=f"resolucion-emitida-{resolucion.id}-cd",
            metadata={
                "tipo_notificacion": "RESOLUCION_FINAL_CD",
                "resolucion_id": resolucion.id,
                "expediente_id": expediente.id,
                "expediente_numero": expediente.numero,
            },
            attachments=[attachment],
        )
        if outbox_cd:
            enqueued.append(outbox_cd)

    return enqueued
