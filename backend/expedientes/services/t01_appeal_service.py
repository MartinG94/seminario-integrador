"""Servicio de aplicación para apelar y adecuar un T01 (PB-02, art. 14 del Reglamento Procesal).

- OP 20: períodos de apelación por socio con plazo parametrizado y apelación versionada.
- OP 30: adecuación versionada de puntos e involucrados con mail de motivos y, si el TD
  lo aprueba, un nuevo período de apelación para los afectados.
"""

from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import DbHolidayProvider
from expedientes.domain.t01_appeal import (
    ActionType,
    AppealError,
    evaluate_adjustment,
    validate_appeal_text,
    validate_business_days,
)
from expedientes.models import (
    AdecuacionT01,
    ApelacionT01,
    EstadoExpedienteEnum,
    Expediente,
    OrigenPeriodoApelacionEnum,
    ParametroPlazoApelacion,
    PeriodoApelacion,
    SolicitudT01,
)
from notifications.services import EmailDispatcherService
from socios.models import Role, Socio

AUTHORITY_ROLES = (Role.TD, Role.CD, Role.ADMIN)


class T01AppealError(Exception):
    """Error base de la apelación y adecuación del T01."""


class T01AppealNotFound(T01AppealError):
    pass


class T01AppealForbidden(T01AppealError):
    pass


class T01AppealStateError(T01AppealError):
    pass


class T01AppealValidationError(T01AppealError):
    pass


def _socio_label(socio: Socio) -> str:
    return f"{socio.first_name} {socio.last_name}".strip() + f" (N° {socio.legajo})"


def _socio_snapshot(socio: Socio) -> dict:
    return {"id": socio.id, "legajo": socio.legajo, "nombre": _socio_label(socio)}


def _involved_ids(expediente: Expediente) -> set[int]:
    return {expediente.socio_id, *expediente.socios.values_list("pk", flat=True)}


def _enqueue_mail(*, key: str, to: str, subject: str, body: str, metadata: dict) -> None:
    if not to:
        return
    EmailDispatcherService.create_or_get_outbox(
        {
            "to": [to],
            "subject": subject,
            "body_text": body,
            "idempotency_key": key,
            "metadata": metadata,
        }
    )


class T01AppealService:
    # --- Períodos y plazo (CA1) ---

    @staticmethod
    def solicitud_of(expediente: Expediente) -> SolicitudT01 | None:
        return SolicitudT01.objects.filter(expediente=expediente).first()

    @staticmethod
    def is_t01(expediente: Expediente) -> bool:
        return SolicitudT01.objects.filter(expediente=expediente).exists()

    @staticmethod
    def _open_periods(
        expediente: Expediente,
        socios: list[Socio],
        inicio_at: datetime,
        origen: str,
        adecuacion: AdecuacionT01 | None = None,
    ) -> datetime:
        dias = ParametroPlazoApelacion.vigente()
        limite = compute_business_deadline(
            start_at=inicio_at, business_days=dias, holiday_provider=DbHolidayProvider()
        )
        for socio in socios:
            PeriodoApelacion.objects.create(
                expediente=expediente,
                socio=socio,
                origen=origen,
                adecuacion=adecuacion,
                dias_habiles=dias,
                inicio_at=inicio_at,
                limite_at=limite,
            )
        return limite

    @classmethod
    def open_initial_periods(cls, expediente: Expediente, inicio_at: datetime) -> datetime | None:
        """Abre el período de cada involucrado al iniciar la etapa de apelación (OP 20)."""
        if not cls.is_t01(expediente):
            return None
        existentes = expediente.periodos_apelacion.order_by("-limite_at").first()
        if existentes is not None:
            return existentes.limite_at
        socios = list(Socio.objects.filter(pk__in=_involved_ids(expediente)))
        return cls._open_periods(expediente, socios, inicio_at, OrigenPeriodoApelacionEnum.APERTURA)

    @staticmethod
    def effective_deadline(expediente: Expediente) -> datetime | None:
        """Vencimiento efectivo: el último período abierto o, sin períodos, el plazo congelado."""
        ultimo = expediente.periodos_apelacion.aggregate(limite=Max("limite_at"))["limite"]
        return ultimo or expediente.plazo_limite_at

    @staticmethod
    def set_business_days(*, dias_habiles: int, user) -> ParametroPlazoApelacion:
        try:
            validate_business_days(dias_habiles)
        except AppealError as exc:
            raise T01AppealValidationError(str(exc)) from exc
        return ParametroPlazoApelacion.objects.create(dias_habiles=dias_habiles, autor=user)

    # --- Apelación (OP 20) ---

    @classmethod
    @transaction.atomic
    def present_appeal(cls, *, expediente_id: int, user, texto: str) -> ApelacionT01:
        expediente = Expediente.objects.select_for_update().filter(pk=expediente_id).first()
        if expediente is None:
            raise T01AppealNotFound("Expediente no encontrado.")
        socio = getattr(user, "socio", None)
        if socio is None or socio.id not in _involved_ids(expediente):
            raise T01AppealForbidden("No estás involucrado en este expediente.")
        if not cls.is_t01(expediente):
            raise T01AppealValidationError("Este expediente no se originó en un T01.")
        if expediente.estado != EstadoExpedienteEnum.JUSTIFICANDO:
            raise T01AppealStateError(
                f"El expediente está en '{expediente.get_estado_display()}' "
                "y no admite apelaciones."
            )
        periodo = expediente.periodos_apelacion.filter(socio=socio).order_by("-limite_at").first()
        ahora = timezone.now()
        if periodo is None:
            raise T01AppealStateError("No tenés un período de apelación abierto.")
        if ahora > periodo.limite_at:
            raise T01AppealStateError(
                "Tu plazo de apelación venció el "
                f"{timezone.localtime(periodo.limite_at):%d/%m/%Y %H:%M} hs."
            )
        try:
            texto = validate_appeal_text(texto)
        except AppealError as exc:
            raise T01AppealValidationError(str(exc)) from exc

        ultimo = (
            ApelacionT01.objects.filter(expediente=expediente, socio=socio).aggregate(
                n=Max("numero")
            )["n"]
            or 0
        )
        apelacion = ApelacionT01.objects.create(
            expediente=expediente, socio=socio, numero=ultimo + 1, texto=texto
        )

        cuerpo = (
            f"Se registró la apelación (versión {apelacion.numero}) de {_socio_label(socio)} "
            f"en el expediente {expediente.numero}.\n\n"
            f"Fecha: {timezone.localtime(apelacion.created_at):%d/%m/%Y %H:%M} hs.\n"
            f"Plazo: hasta el {timezone.localtime(periodo.limite_at):%d/%m/%Y %H:%M} hs.\n\n"
            f"{texto}"
        )
        asunto = f"Expediente {expediente.numero}: apelación registrada"
        metadata = {"expediente_id": expediente.pk, "apelacion_id": apelacion.pk}
        _enqueue_mail(
            key=f"t01-apelacion-{apelacion.pk}-socio",
            to=socio.email,
            subject=asunto,
            body=cuerpo,
            metadata=metadata,
        )
        _enqueue_mail(
            key=f"t01-apelacion-{apelacion.pk}-tribunal",
            to=settings.TRIBUNAL_EMAIL,
            subject=asunto,
            body=cuerpo,
            metadata=metadata,
        )
        return apelacion

    # --- Debate y adecuación (OP 30) ---

    @classmethod
    @transaction.atomic
    def adjust(
        cls,
        *,
        expediente_id: int,
        user,
        puntos: Decimal,
        socio_ids: list[int],
        motivos: str,
        reabrir_plazo: bool,
    ) -> AdecuacionT01:
        expediente = Expediente.objects.select_for_update().filter(pk=expediente_id).first()
        if expediente is None:
            raise T01AppealNotFound("Expediente no encontrado.")
        solicitud = cls.solicitud_of(expediente)
        if solicitud is None:
            raise T01AppealValidationError("Este expediente no se originó en un T01.")
        if expediente.estado != EstadoExpedienteEnum.REVISION_RESOLUCION:
            raise T01AppealStateError(
                "La adecuación se debate con el expediente en 'Justificaciones en revisión'."
            )

        nuevos_ids = list(dict.fromkeys(socio_ids))
        nuevos = {s.id: s for s in Socio.objects.filter(pk__in=nuevos_ids)}
        if len(nuevos) != len(nuevos_ids):
            raise T01AppealValidationError("Uno o más socios indicados no existen.")
        anteriores_ids = _involved_ids(expediente)
        try:
            cambio = evaluate_adjustment(
                action=ActionType(solicitud.tipo_accion),
                old_points=expediente.puntos,
                new_points=puntos,
                old_ids=anteriores_ids,
                new_ids=set(nuevos_ids),
                grounds=motivos,
                reopen=reabrir_plazo,
            )
        except AppealError as exc:
            raise T01AppealValidationError(str(exc)) from exc

        anteriores = {s.id: s for s in Socio.objects.filter(pk__in=anteriores_ids)}
        version = (
            AdecuacionT01.objects.filter(expediente=expediente).aggregate(v=Max("version"))["v"]
            or 0
        ) + 1
        socio = getattr(user, "socio", None)
        afectados = sorted(cambio.affected) if reabrir_plazo else []
        adecuacion = AdecuacionT01.objects.create(
            expediente=expediente,
            version=version,
            puntos_anteriores=expediente.puntos,
            puntos_nuevos=puntos,
            socios_anteriores=[_socio_snapshot(anteriores[i]) for i in sorted(anteriores)],
            socios_nuevos=[_socio_snapshot(nuevos[i]) for i in nuevos_ids],
            motivos=motivos.strip(),
            reabre_plazo=reabrir_plazo,
            socios_con_nuevo_plazo=afectados,
            autor=user,
            autor_legajo=socio.legajo if socio else user.get_username(),
        )

        expediente.puntos = puntos
        if expediente.socio_id not in nuevos:
            expediente.socio_id = nuevos_ids[0]
        expediente.save(update_fields=["puntos", "socio", "updated_at"])
        expediente.socios.set(nuevos_ids)

        limite = None
        if reabrir_plazo:
            from expedientes.services.workflow_service import ExpedienteWorkflowService

            limite = cls._open_periods(
                expediente,
                [nuevos[i] for i in afectados],
                timezone.now(),
                OrigenPeriodoApelacionEnum.ADECUACION,
                adecuacion,
            )
            ExpedienteWorkflowService.reopen_appeal_period(
                expediente_id=expediente.pk,
                actor=user.get_username(),
                motivo=(
                    f"Nuevo período de apelación por la adecuación v{version} "
                    "(derecho de defensa, art. 14)."
                ),
            )

        cls._notify_adjustment(expediente, solicitud, adecuacion, anteriores | nuevos, limite)
        return adecuacion

    @staticmethod
    def _notify_adjustment(
        expediente: Expediente,
        solicitud: SolicitudT01,
        adecuacion: AdecuacionT01,
        destinatarios: dict[int, Socio],
        limite: datetime | None,
    ) -> None:
        """Mail con los motivos de la adecuación al solicitante y a los solicitados (CA3)."""
        involucrados = ", ".join(s["nombre"] for s in adecuacion.socios_nuevos)
        cuerpo = (
            f"El Tribunal de Disciplina adecuó el expediente {expediente.numero} "
            f"(versión {adecuacion.version}).\n\n"
            f"Puntos: {adecuacion.puntos_anteriores} → {adecuacion.puntos_nuevos}\n"
            f"Involucrados: {involucrados}\n\n"
            f"Motivos:\n{adecuacion.motivos}\n"
        )
        metadata = {"expediente_id": expediente.pk, "adecuacion_id": adecuacion.pk}
        asunto = f"Expediente {expediente.numero}: adecuación del T01"
        _enqueue_mail(
            key=f"t01-adecuacion-{adecuacion.pk}-solicitante",
            to=solicitud.solicitante.email,
            subject=asunto,
            body=cuerpo,
            metadata=metadata,
        )
        for socio in destinatarios.values():
            extra = ""
            if limite and socio.id in adecuacion.socios_con_nuevo_plazo:
                extra = (
                    "\nSe abrió un nuevo período de apelación para vos hasta el "
                    f"{timezone.localtime(limite):%d/%m/%Y %H:%M} hs.\n"
                )
            _enqueue_mail(
                key=f"t01-adecuacion-{adecuacion.pk}-socio-{socio.id}",
                to=socio.email,
                subject=asunto,
                body=cuerpo + extra,
                metadata=metadata,
            )

    # --- Trazabilidad (CA4) ---

    @classmethod
    def history(cls, *, expediente_id: int, user) -> dict:
        expediente = Expediente.objects.filter(pk=expediente_id).first()
        if expediente is None:
            raise T01AppealNotFound("Expediente no encontrado.")
        socio = getattr(user, "socio", None)
        es_autoridad = bool(socio and socio.is_enabled and socio.role in AUTHORITY_ROLES)
        periodos = expediente.periodos_apelacion.select_related("socio")
        if not es_autoridad:
            participa = socio is not None and (
                socio.id in _involved_ids(expediente) or periodos.filter(socio=socio).exists()
            )
            if not participa:
                raise T01AppealForbidden("No posee autorización para consultar este expediente.")

        solicitud = cls.solicitud_of(expediente)
        apelaciones = expediente.apelaciones_t01.select_related("socio")
        if not es_autoridad:
            periodos = periodos.filter(socio=socio)
            apelaciones = apelaciones.filter(socio=socio)
        ahora = timezone.now()
        return {
            "es_t01": solicitud is not None,
            "estado": expediente.estado,
            "plazo_dias_vigente": ParametroPlazoApelacion.vigente(),
            "puntos_vigentes": str(expediente.puntos),
            "involucrados": [
                _socio_snapshot(s)
                for s in Socio.objects.filter(pk__in=_involved_ids(expediente)).order_by("pk")
            ],
            "original": (
                {
                    "numero_t01": solicitud.numero_expediente,
                    "tipo_accion": solicitud.tipo_accion,
                    "emitido_at": solicitud.issued_at,
                    "solicitante": _socio_label(solicitud.solicitante),
                    "snapshot": solicitud.snapshot_emitido,
                }
                if solicitud
                else None
            ),
            "periodos": [
                {
                    "socio_id": p.socio_id,
                    "socio": _socio_label(p.socio),
                    "origen": p.origen,
                    "dias_habiles": p.dias_habiles,
                    "inicio_at": p.inicio_at,
                    "limite_at": p.limite_at,
                    "abierto": expediente.estado == EstadoExpedienteEnum.JUSTIFICANDO
                    and ahora <= p.limite_at,
                }
                for p in periodos
            ],
            "apelaciones": [
                {
                    "socio_id": a.socio_id,
                    "socio": _socio_label(a.socio),
                    "numero": a.numero,
                    "texto": a.texto,
                    "created_at": a.created_at,
                }
                for a in apelaciones
            ],
            "adecuaciones": [
                {
                    "version": a.version,
                    "puntos_anteriores": str(a.puntos_anteriores),
                    "puntos_nuevos": str(a.puntos_nuevos),
                    "socios_anteriores": a.socios_anteriores,
                    "socios_nuevos": a.socios_nuevos,
                    "motivos": a.motivos,
                    "reabre_plazo": a.reabre_plazo,
                    "socios_con_nuevo_plazo": a.socios_con_nuevo_plazo,
                    "autor_legajo": a.autor_legajo,
                    "created_at": a.created_at,
                }
                for a in expediente.adecuaciones_t01.all()
            ],
        }
