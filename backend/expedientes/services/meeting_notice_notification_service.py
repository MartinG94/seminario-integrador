"""Servicio de notificación automática de convocatorias (CA7 / Art. 95 R.I.).

Implementa:
- Resolución de convocados por Grupo Social (G57-G60), Subcomisión o Lista Personalizada.
- Construcción de contenido formal con fecha, hora, modalidad y carácter reglamentario.
- Persistencia transaccional en la cola EmailOutbox mediante EmailDispatcherService.
- Clave de idempotencia por evento y socio (f"meeting_notice_{evento.id}_socio_{socio.id}").
"""

import logging
from typing import TYPE_CHECKING, Any

from django.conf import settings

from expedientes.models import (
    EventoInstitucional,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
)
from notifications.models import EmailOutbox
from notifications.services import EmailDispatcherService
from socios.models import Socio

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MeetingNoticeNotificationService:
    """Gestiona el encolado y despacho de citaciones institucionales a eventos obligatorios."""

    GROUP_TO_SOCIAL_YEAR: dict[str, int] = {
        "G60": 1,
        "G59": 2,
        "G58": 3,
        "G57": 4,
    }

    @classmethod
    def resolve_convocados(
        cls,
        evento: EventoInstitucional,
        socios_ids: list[int] | None = None,
    ) -> list[Socio]:
        """Resuelve la lista de socios a convocar según el modo de convocatoria del evento."""
        if socios_ids:
            return list(Socio.objects.filter(pk__in=socios_ids, is_enabled=True))

        if evento.modo_convocatoria == ModoConvocatoriaEnum.GRUPO and evento.grupo_convocado:
            grupo_clean = evento.grupo_convocado.strip().upper()
            social_year = cls.GROUP_TO_SOCIAL_YEAR.get(grupo_clean)
            if social_year:
                return list(Socio.objects.filter(social_year=social_year, is_enabled=True))
            return list(Socio.objects.filter(is_enabled=True))

        elif evento.modo_convocatoria == ModoConvocatoriaEnum.SUBCOMISION and evento.subcomision_id:
            return list(Socio.objects.filter(subcomision_id=evento.subcomision_id, is_enabled=True))

        elif (
            evento.modo_convocatoria == ModoConvocatoriaEnum.ESTADO_SOCIAL
            and evento.estado_social_convocado
        ):
            if evento.estado_social_convocado.upper() == "JUNIORS":
                return list(Socio.objects.filter(social_year__lte=3, is_enabled=True))
            elif evento.estado_social_convocado.upper() == "SENIORS":
                return list(Socio.objects.filter(social_year__gte=4, is_enabled=True))

        # Si existen convocados formalmente registrados en tribunal_evento_convocado
        convocados_ids = list(evento.convocados.values_list("socio_id", flat=True))
        if convocados_ids:
            return list(Socio.objects.filter(pk__in=convocados_ids, is_enabled=True))

        asistencias_socios = list(evento.asistencias.values_list("socio_id", flat=True))
        if asistencias_socios:
            return list(Socio.objects.filter(pk__in=asistencias_socios, is_enabled=True))

        return []

    @classmethod
    def format_modalidad_desc(cls, evento: EventoInstitucional) -> str:
        """Formatea la descripción de la modalidad para el correo."""
        if evento.modalidad == ModalidadEventoEnum.PRESENCIAL_SEDE:
            return f"Presencial en {evento.lugar or 'Sede Central AVEIT'}"
        elif evento.modalidad == ModalidadEventoEnum.PRESENCIAL_EXTERNA:
            loc = evento.ubicacion or evento.lugar or "Lugar a confirmar"
            return f"Presencial Fuera de Sede — Ubicación: {loc}"
        elif evento.modalidad == ModalidadEventoEnum.VIRTUAL:
            enlace = evento.ubicacion or "Enlace pendiente de envío"
            return f"Virtual por Videoconferencia — Acceso: {enlace}"
        return evento.get_modalidad_display()

    @classmethod
    def build_notice_payload(
        cls,
        evento: EventoInstitucional,
        socio: Socio,
    ) -> dict[str, Any]:
        """Construye el payload para el encolador de salida Outbox."""
        base_url = getattr(settings, "FRONTEND_URL", "http://localhost:4200")
        evento_url = f"{base_url}/eventos-asistencia/{evento.id}"

        categoria_label = evento.get_categoria_display()
        subtipo_label = evento.tipo
        fecha_str = evento.fecha_programada.strftime("%d/%m/%Y a las %H:%M hs")
        modalidad_str = cls.format_modalidad_desc(evento)
        caracter_str = (
            "OBLIGATORIA Y SANCIONABLE"
            if (evento.es_obligatoria and evento.es_sancionable)
            else "INFORMATIVA / NO SANCIONABLE"
        )

        subject = f"Convocatoria Institucional a {categoria_label}: {evento.titulo}"
        socio_identificador = socio.numero_socio or socio.legajo

        body_text = (
            f"Estimado/a {socio.first_name} {socio.last_name} "
            f"(N.º de socio: {socio_identificador}):\n\n"
            f"Se le notifica formalmente la citación para el siguiente evento institucional:\n\n"
            f"• Denominación: {evento.titulo}\n"
            f"• Categoría: {categoria_label} ({subtipo_label})\n"
            f"• Fecha y Hora de Inicio: {fecha_str}\n"
            f"• Modalidad / Locación: {modalidad_str}\n"
            f"• Tolerancia de Tardanza: {evento.tolerancia_tardanza_minutos} minutos\n"
            f"• Carácter: {caracter_str}\n\n"
            f"Puede consultar los detalles y la nómina de convocados en la plataforma:\n"
            f"{evento_url}\n\n"
            f"Atentamente,\n"
            f"Comisión Directiva / Autoridades de Subcomisión\n"
            f"Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T.)"
        )

        from notifications.services import render_institutional_email_html

        body_html = render_institutional_email_html(
            header_title="A.V.E.I.T. — Convocatoria Institucional",
            subtitle=f"{categoria_label}: {evento.titulo}",
            greeting=(
                f"Estimado/a {socio.first_name} {socio.last_name} "
                f"(N.º de socio: {socio_identificador}):"
            ),
            intro_paragraphs=[
                "Se le notifica formalmente la citación para el siguiente evento institucional:"
            ],
            detail_rows=[
                ("Denominación", str(evento.titulo), None),
                ("Categoría", f"{categoria_label} ({subtipo_label})", None),
                ("Fecha y Hora", fecha_str, None),
                ("Modalidad", modalidad_str, None),
                ("Tolerancia", f"{evento.tolerancia_tardanza_minutos} minutos", None),
                ("Carácter", caracter_str, "#b71c1c" if evento.es_sancionable else None),
            ],
            cta_label="Ver Convocatoria",
            cta_url=evento_url,
        )

        idempotency_key = f"meeting_notice_{evento.id}_socio_{socio.id}"

        return {
            "to": [socio.email],
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "idempotency_key": idempotency_key,
            "metadata": {
                "tipo_notificacion": "CONVOCATORIA_EVENTO",
                "evento_id": evento.id,
                "socio_id": socio.id,
                "categoria": evento.categoria,
                "tipo": evento.tipo,
                "es_disciplinario": bool(evento.es_sancionable),
            },
        }

    @classmethod
    def enqueue_meeting_notices(
        cls,
        evento: EventoInstitucional,
        socios_ids: list[int] | None = None,
        auto_dispatch: bool = False,
    ) -> list[EmailOutbox]:
        """
        Encola las notificaciones por correo para cada socio convocado.

        Retorna:
            Lista de instancias de EmailOutbox generadas o recuperadas por idempotencia.
        """
        convocados = cls.resolve_convocados(evento, socios_ids=socios_ids)
        if not convocados:
            logger.info("No se encontraron socios convocados para el evento ID %s.", evento.id)
            return []

        outbox_items: list[EmailOutbox] = []
        for socio in convocados:
            payload = cls.build_notice_payload(evento, socio)
            outbox, created = EmailDispatcherService.create_or_get_outbox(payload)
            if auto_dispatch:
                EmailDispatcherService.dispatch(outbox)
            outbox_items.append(outbox)

        logger.info(
            "Encoladas %d notificaciones de convocatoria para evento ID %s.",
            len(outbox_items),
            evento.id,
        )
        return outbox_items

    @classmethod
    def send_cancellation_notices(
        cls,
        evento: EventoInstitucional,
        motivo: str | None = None,
        auto_dispatch: bool = False,
    ) -> list[EmailOutbox]:
        """
        Encola y despacha avisos formales de cancelación a todos los socios citados,
        pidiendo disculpas institucionales e informando el motivo si fue especificado.
        """
        convocados = cls.resolve_convocados(evento)
        if not convocados:
            logger.info(
                "No se encontraron convocados para notificar cancelación del evento %s.", evento.id
            )
            return []

        motivo_texto = (
            motivo.strip()
            if (motivo and motivo.strip())
            else "Razones operativas y de fuerza mayor comunicadas por la autoridad convocante."
        )
        fecha_str = evento.fecha_programada.strftime("%d/%m/%Y a las %H:%M hs")
        subject = f"[AVISO FORMAL] Cancelación de Convocatoria: {evento.titulo}"

        outbox_items: list[EmailOutbox] = []
        for socio in convocados:
            socio_identificador = socio.numero_socio or socio.legajo
            body_text = (
                f"Estimado/a {socio.first_name} {socio.last_name} "
                f"(N.º de socio: {socio_identificador}):\n\n"
                "Le notificamos formalmente que la convocatoria al siguiente evento institucional "
                "ha sido CANCELADA:\n\n"
                f"• Denominación: {evento.titulo}\n"
                f"• Categoría: {evento.get_categoria_display()} ({evento.tipo})\n"
                f"• Fecha prevista: {fecha_str}\n"
                f"• Motivo de Cancelación: {motivo_texto}\n\n"
                "Pedimos sinceras disculpas por los inconvenientes y cambios de agenda "
                "ocasionados.\n\n"
                "Atentamente,\n"
                "Comisión Directiva / Autoridades Convocantes\n"
                "Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T.)"
            )

            from notifications.services import render_institutional_email_html

            body_html = render_institutional_email_html(
                header_title="A.V.E.I.T. — Aviso Formal de Cancelación",
                subtitle=f"Cancelación de Convocatoria: {evento.titulo}",
                greeting=(
                    f"Estimado/a {socio.first_name} {socio.last_name} "
                    f"(N.º de socio: {socio_identificador}):"
                ),
                intro_paragraphs=[
                    "Le informamos que la siguiente convocatoria institucional ha sido "
                    "CANCELADA y queda sin efecto:"
                ],
                detail_rows=[
                    ("Denominación", str(evento.titulo), None),
                    ("Categoría", f"{evento.get_categoria_display()} ({evento.tipo})", None),
                    ("Fecha prevista", fecha_str, None),
                    ("Motivo informado", motivo_texto, "#b71c1c"),
                ],
                closing_paragraphs=[
                    "Pedimos sinceras disculpas por los inconvenientes que esta cancelación "
                    "pudiera ocasionarle."
                ],
                accent_color="#b71c1c",
            )

            idempotency_key = f"meeting_cancellation_{evento.id}_socio_{socio.id}"
            payload = {
                "to": [socio.email],
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
                "idempotency_key": idempotency_key,
                "metadata": {
                    "tipo_notificacion": "CANCELACION_EVENTO",
                    "evento_id": evento.id,
                    "socio_id": socio.id,
                    "motivo": motivo_texto,
                    "es_disciplinario": bool(evento.es_sancionable),
                },
            }
            outbox, _ = EmailDispatcherService.create_or_get_outbox(payload)
            if auto_dispatch:
                EmailDispatcherService.dispatch(outbox)
            outbox_items.append(outbox)

        logger.info(
            "Encoladas %d notificaciones de cancelación para evento ID %s.",
            len(outbox_items),
            evento.id,
        )
        return outbox_items
