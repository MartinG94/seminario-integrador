"""Servicio de dominio para la exclusión fundada de socios involucrados (SCRUM-102, EARS-102)."""

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    EstadoResolucionEnum,
    Expediente,
    TipoDescargoEnum,
)
from notifications.services import EmailDispatcherService
from socios.models import Role, Socio

logger = logging.getLogger(__name__)


class ExclusionInvolucradoService:
    """Gestiona la exclusión fundada de socios imputados por el Tribunal de Disciplina."""

    @classmethod
    @transaction.atomic
    def excluir_involucrado(
        cls,
        *,
        expediente_id: int,
        socio_id: int,
        user: Any,
        motivo: str,
    ) -> dict[str, Any]:
        """Excluye de forma fundada a un socio imputado en un expediente."""
        # 1. Validar permisos: Rol TD o Staff/Superuser
        if not user or not user.is_authenticated:
            raise PermissionDenied("Debe autenticarse para excluir involucrados.")

        socio_user = getattr(user, "socio", None)
        rol = getattr(socio_user, "role", "") if socio_user else ""
        es_td = (
            (socio_user and getattr(socio_user, "is_enabled", True) and rol == Role.TD)
            or user.is_staff
            or user.is_superuser
        )
        if not es_td:
            raise PermissionDenied(
                "Solo integrantes del Tribunal de Disciplina pueden excluir involucrados."
            )

        # 2. Validar motivo obligatorio (>= 10 caracteres)
        if not motivo or len(motivo.strip()) < 10:
            raise ValidationError(
                "El motivo de exclusión es obligatorio y debe tener al menos 10 caracteres."
            )

        motivo_limpio = motivo.strip()

        # 3. Obtener expediente con lock transaccional
        try:
            expediente = (
                Expediente.objects.select_for_update()
                .prefetch_related("socios", "descargos")
                .get(pk=expediente_id)
            )
        except Expediente.DoesNotExist:
            raise ValidationError(f"No existe el expediente con ID {expediente_id}.")

        # Estados permitidos: previo a EMITIDO
        if expediente.estado == EstadoExpedienteEnum.EMITIDO:
            raise ValidationError(
                "No se puede excluir un socio de un expediente ya emitido o cerrado."
            )

        # 4. Validar pertenencia del socio al expediente
        todos_socios = list(expediente.socios.all())
        if not todos_socios and expediente.socio:
            todos_socios = [expediente.socio]

        socio_imputado = next((s for s in todos_socios if s.id == socio_id), None)
        if socio_imputado is None:
            socio_db = Socio.objects.filter(pk=socio_id).first()
            if not socio_db or (
                socio_db.id != expediente.socio_id and socio_db not in expediente.socios.all()
            ):
                raise ValidationError(
                    "El socio especificado no se encuentra involucrado en este expediente."
                )
            socio_imputado = socio_db

        # 5. Obtener o crear DescargoExpediente para persistir la exclusión
        descargo, _ = DescargoExpediente.objects.select_for_update().get_or_create(
            expediente=expediente,
            socio=socio_imputado,
            defaults={
                "tipo": TipoDescargoEnum.T02_CERTIFICADO,
                "es_vigente": False,
                "texto": "",
            },
        )

        nro_socio = getattr(socio_imputado, "numero_socio", None) or socio_imputado.legajo
        if descargo.esta_excluido:
            raise ValidationError(
                f"El socio {nro_socio} ya fue excluido previamente de este expediente."
            )

        # Registrar la exclusión inmutable
        descargo.esta_excluido = True
        descargo.motivo_exclusion = motivo_limpio
        descargo.excluido_por = user
        descargo.excluido_at = timezone.now()
        descargo.es_vigente = False
        descargo.puntaje_ratificado = "0.00"
        descargo.save()

        # 6. Despacho de notificaciones vía EmailOutbox (Socio imputado y Solicitante)
        cls._despachar_notificaciones_exclusion(
            expediente=expediente,
            socio=socio_imputado,
            motivo=motivo_limpio,
        )

        # 7. Verificar involucrados activos restantes
        todos_socios_ids = {s.id for s in todos_socios}
        if expediente.socio_id:
            todos_socios_ids.add(expediente.socio_id)

        excluidos_ids = set(
            DescargoExpediente.objects.filter(
                expediente=expediente,
                socio_id__in=todos_socios_ids,
                esta_excluido=True,
            ).values_list("socio_id", flat=True)
        )
        activos_restantes = todos_socios_ids - excluidos_ids
        expediente_archivado = False

        if len(activos_restantes) == 0:
            # Cierre administrativo directo a EMITIDO como causa archivada (Decisión PO 12/11/2026)
            estado_anterior = expediente.estado
            expediente.estado = EstadoExpedienteEnum.EMITIDO
            expediente.puntos = 0
            expediente.save(update_fields=["estado", "puntos", "updated_at"])

            actor_nro = (
                (getattr(socio_user, "numero_socio", None) or getattr(socio_user, "legajo", ""))
                if socio_user
                else getattr(user, "username", str(user))
            )
            actor_str = f"Socio {actor_nro}" if actor_nro else "Tribunal de Disciplina"

            CambioEstadoExpediente.objects.create(
                expediente=expediente,
                estado_anterior=estado_anterior,
                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
                actor=actor_str,
                motivo=(
                    "Sin efecto / Expediente archivado por exclusión fundada de la totalidad "
                    f"de involucrados. Fundamento: {motivo_limpio}"
                ),
            )

            # Si existía una resolución borrador, archivarla; si no, crear resolución administrativa
            from expedientes.models import Resolucion

            resolucion_draft = expediente.resoluciones.filter(
                estado=EstadoResolucionEnum.DRAFT
            ).first()
            if resolucion_draft:
                resolucion_draft.vistos = (
                    resolucion_draft.vistos or ""
                ) + "\nExclusión fundada de imputados."
                resolucion_draft.considerandos = (
                    f"Exclusión fundada de la totalidad de involucrados: {motivo_limpio}."
                )
                resolucion_draft.articulos_resolutivos = (
                    "Artículo 1°: Archivar el presente expediente sin sanción ni impacto en puntos."
                )
                resolucion_draft.puntos_finales = 0
                resolucion_draft.estado = EstadoResolucionEnum.ISSUED
                resolucion_draft.issued_by = user
                resolucion_draft.issued_at = timezone.now()
                resolucion_draft.save()
            elif not expediente.resoluciones.filter(estado=EstadoResolucionEnum.ISSUED).exists():
                Resolucion.objects.create(
                    expediente=expediente,
                    version=1,
                    plantilla_version="v1",
                    estado=EstadoResolucionEnum.ISSUED,
                    numero_expediente_snapshot=expediente.numero,
                    vistos=(
                        f"Las actuaciones obrantes en el Expediente {expediente.numero} "
                        "y la exclusión fundada de la totalidad de los socios involucrados."
                    ),
                    considerandos=(
                        f"Sin efecto / Expediente archivado por exclusión fundada: {motivo_limpio}."
                    ),
                    articulos_resolutivos=(
                        "Artículo 1°: Archivar el presente expediente sin sanción "
                        "ni impacto en puntos."
                    ),
                    puntos_finales=0,
                    created_by=user,
                    issued_by=user,
                    issued_at=timezone.now(),
                )

            expediente_archivado = True

        return {
            "expediente": expediente,
            "descargo": descargo,
            "socio": socio_imputado,
            "expediente_archivado": expediente_archivado,
            "activos_restantes_count": len(activos_restantes),
        }

    @classmethod
    def _despachar_notificaciones_exclusion(
        cls,
        *,
        expediente: Expediente,
        socio: Socio,
        motivo: str,
    ) -> None:
        """Despacha notificaciones atómicas en EmailOutbox hacia el socio y el solicitante."""
        # 1. Notificación al socio imputado excluido
        socio_email = (
            getattr(getattr(socio, "user", None), "email", None)
            or getattr(socio, "email", None)
            or f"socio.{socio.legajo}@aveit.test"
        )

        idempotency_socio = f"exclusion-expediente-{expediente.id}-socio-{socio.id}-notif"
        subject_socio = (
            f"[AVEIT] Expediente {expediente.numero}: Desestimación e imputación sin efecto"
        )
        body_socio = (
            f"Estimado/a {socio.first_name} {socio.last_name}:\n\n"
            "Por disposición formal del Tribunal de Disciplina de A.V.E.I.T. en el marco del "
            f"expediente {expediente.numero}, se ha resuelto su EXCLUSIÓN FUNDADA.\n\n"
            f"Fundamento del Tribunal:\n{motivo}\n\n"
            "En consecuencia, se deja sin efecto todo cargo u obligación procesal respecto a su "
            "persona en estas actuaciones.\n\n"
            "Atentamente,\nTribunal de Disciplina — A.V.E.I.T."
        )

        try:
            outbox_socio, _ = EmailDispatcherService.create_or_get_outbox(
                {
                    "to": [socio_email],
                    "subject": subject_socio,
                    "body_text": body_socio,
                    "idempotency_key": idempotency_socio,
                    "metadata": {
                        "tipo": "EXCLUSION_INVOLUCRADO",
                        "expediente_id": expediente.id,
                        "socio_id": socio.id,
                    },
                }
            )
            EmailDispatcherService.dispatch(outbox_socio)
        except Exception as exc:
            logger.warning("Fallo al despachar notificación de exclusión al socio: %s", exc)

        # 2. Notificación al solicitante de la causa si existe
        solicitante_email = None
        solicitud = getattr(expediente, "solicitud_t01", None)
        if solicitud and getattr(solicitud, "solicitante", None):
            sol = solicitud.solicitante
            solicitante_email = (
                getattr(getattr(sol, "user", None), "email", None)
                or getattr(sol, "email", None)
                or f"solicitante.{sol.legajo}@aveit.test"
            )

        if solicitante_email:
            idempotency_sol = f"exclusion-expediente-{expediente.id}-solicitante-socio-{socio.id}"
            subject_sol = f"[AVEIT] Expediente {expediente.numero}: Exclusión de socio imputado"
            nombre_soc = f"{socio.first_name} {socio.last_name}".strip()
            nro_socio_msg = getattr(socio, "numero_socio", None) or socio.legajo
            body_sol = (
                "Estimado/a solicitante:\n\n"
                "Se le notifica que el TD ha dispuesto la exclusión fundada del socio "
                f"{nro_socio_msg} ({nombre_soc}) en el expediente {expediente.numero}.\n\n"
                f"Fundamento:\n{motivo}\n\n"
                "Atentamente,\nTribunal de Disciplina — A.V.E.I.T."
            )
            try:
                outbox_sol, _ = EmailDispatcherService.create_or_get_outbox(
                    {
                        "to": [solicitante_email],
                        "subject": subject_sol,
                        "body_text": body_sol,
                        "idempotency_key": idempotency_sol,
                        "metadata": {
                            "tipo": "EXCLUSION_INVOLUCRADO_SOLICITANTE",
                            "expediente_id": expediente.id,
                            "socio_id": socio.id,
                        },
                    }
                )
                EmailDispatcherService.dispatch(outbox_sol)
            except Exception as exc:
                logger.warning(
                    "Fallo al despachar notificación de exclusión al solicitante: %s", exc
                )
