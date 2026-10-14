"""Servicio orquestador del procesamiento de asistencia y graduación sancionatoria.

Implementa:
- Coordinación transaccional de captura mediante Strategy (Manual / Biométrico).
- Auditoría procesal de plazos con MeetingComplianceService.
- Inhibición de sanciones y apercibimientos cuando el evento es NO_SANCIONABLE (CA2).
- Graduación de escala decimal (-0.5, -1.0, -1.5, -2.0) (CA3).
- Generación de expedientes CREADO sin tocar saldos manualmente (CA5 / Regla 3).
- Derivación de tardanzas leves al motor atómico 3:1 (CA4).
- Registro del motivo circunstanciado por socio (CA10).
"""

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone

from expedientes.domain.attendance_strategy import AttendanceStrategyFactory
from expedientes.models import (
    AsistenciaEvento,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EventoInstitucional,
    MetodoCapturaAsistenciaEnum,
    ModoConvocatoriaEnum,
    SubtipoReunionEnum,
)
from expedientes.services.meeting_compliance_service import MeetingComplianceService
from expedientes.services.warning_accumulation_service import WarningAccumulationService
from expedientes.services.workflow_service import ExpedienteWorkflowService
from socios.models import Socio

if TYPE_CHECKING:
    from expedientes.domain.ports import HolidayProviderPort

logger = logging.getLogger(__name__)


class AttendanceProcessingService:
    """Orquestador central para la toma, validación y graduación disciplinaria de asistencias."""

    PUNTOS_TARDANZA_GRAVE: Decimal = Decimal("-0.50")
    PUNTOS_RETIRO_GRAVE: Decimal = Decimal("-0.50")
    PUNTOS_FALTA_ORDINARIA: Decimal = Decimal("-1.00")
    PUNTOS_FALTA_EXTRAORDINARIA: Decimal = Decimal("-1.50")
    PUNTOS_FALTA_ASAMBLEA: Decimal = Decimal("-2.00")
    PUNTOS_FALTA_ACTIVIDAD_OPERATIVA: Decimal = Decimal("-1.00")

    @classmethod
    def get_penalty_points_for_absence(cls, evento: EventoInstitucional) -> Decimal:
        """Determina los puntos por inasistencia según categoría y subtipo."""
        if evento.categoria == CategoriaEventoEnum.REUNION:
            if evento.tipo == SubtipoReunionEnum.EXTRAORDINARIA:
                return cls.PUNTOS_FALTA_EXTRAORDINARIA
            elif evento.tipo == SubtipoReunionEnum.ASAMBLEA:
                return cls.PUNTOS_FALTA_ASAMBLEA
            else:
                return cls.PUNTOS_FALTA_ORDINARIA
        elif evento.categoria == CategoriaEventoEnum.ACTIVIDAD:
            return cls.PUNTOS_FALTA_ACTIVIDAD_OPERATIVA
        return cls.PUNTOS_FALTA_ORDINARIA

    @classmethod
    @transaction.atomic
    def process_event_attendance(
        cls,
        *,
        evento_id: int,
        marcaciones: list[dict[str, Any]],
        metodo_captura: str = MetodoCapturaAsistenciaEnum.MANUAL,
        actor: str = "SISTEMA",
        reportado_por_id: int | None = None,
        fecha_reporte: Any = None,
        fecha_hora_cierre_efectivo: Any = None,
        cerrar_evento: bool = True,
        holiday_provider: "HolidayProviderPort | None" = None,
    ) -> dict[str, Any]:
        """
        Procesa el lote completo de asistencia para un evento institucional.

        Flujo:
        1. Bloqueo pesimista del evento.
        2. Fijación de timestamps de reporte y cierre efectivo.
        3. Evaluación de cumplimiento y sancionabilidad (MeetingComplianceService).
        4. Procesamiento de marcas mediante Strategy Pattern.
        5. Persistencia de AsistenciaEvento con motivo circunstanciado.
        6. Si es sancionable, graduación y emisión de sanciones/apercibimientos.
        7. Cero UPDATE manual de saldos en MySQL.
        """
        evento = EventoInstitucional.objects.select_for_update().get(pk=evento_id)
        ahora = timezone.now()

        # Configurar timestamp de reporte
        momento_reporte = fecha_reporte or ahora
        evento.fecha_reporte = momento_reporte

        if reportado_por_id:
            evento.reportado_por_id = reportado_por_id

        # Configurar cierre efectivo si aplica
        if fecha_hora_cierre_efectivo:
            evento.fecha_hora_cierre_efectivo = fecha_hora_cierre_efectivo
        elif cerrar_evento and not evento.fecha_hora_cierre_efectivo:
            evento.fecha_hora_cierre_efectivo = ahora

        # 1. Evaluar si el evento es sancionable (preaviso y reporte dentro de plazos)
        es_sancionable, motivo_no_sancionable = (
            MeetingComplianceService.evaluate_event_sanctionability(
                evento=evento,
                fecha_reporte=momento_reporte,
                holiday_provider=holiday_provider,
            )
        )
        evento.es_sancionable = es_sancionable
        evento.motivo_no_sancionable = motivo_no_sancionable

        if cerrar_evento:
            evento.estado = EstadoEventoEnum.CERRADA

        evento.save(
            update_fields=[
                "fecha_reporte",
                "fecha_hora_cierre_efectivo",
                "es_sancionable",
                "motivo_no_sancionable",
                "estado",
                "reportado_por",
                "updated_at",
            ]
        )

        # 2. Resolver nómina de convocados para la estrategia
        convocados_ids: list[int] = []
        if evento.modo_convocatoria == ModoConvocatoriaEnum.GRUPO and evento.grupo_convocado:
            convocados_ids = list(
                Socio.objects.filter(is_enabled=True)
                .filter(legajo__isnull=False)
                .values_list("id", flat=True)
            )
        elif evento.modo_convocatoria == ModoConvocatoriaEnum.SUBCOMISION and evento.subcomision_id:
            convocados_ids = list(
                Socio.objects.filter(
                    is_enabled=True, subcomision_id=evento.subcomision_id
                ).values_list("id", flat=True)
            )
        else:
            convocados_ids = [m["socio_id"] for m in marcaciones if "socio_id" in m]

        # 3. Procesar mediante el patrón Strategy
        strategy = AttendanceStrategyFactory.get_strategy(metodo_captura)
        records_dto = strategy.process(
            evento=evento,
            marcaciones=marcaciones,
            convocados_ids=convocados_ids,
        )

        asistencias_guardadas: list[AsistenciaEvento] = []
        expedientes_creados: list[dict[str, Any]] = []
        apercibimientos_creados: list[dict[str, Any]] = []

        # 4. Persistir cada asistencia y derivar sanciones si corresponde
        for dto in records_dto:
            asistencia, _ = AsistenciaEvento.objects.update_or_create(
                evento=evento,
                socio_id=dto.socio_id,
                defaults={
                    "estado_asistencia": dto.estado_asistencia,
                    "hora_registro": dto.hora_registro,
                    "hora_salida": dto.hora_salida,
                    "minutos_tardanza": dto.minutos_tardanza,
                    "minutos_retiro_anticipado": dto.minutos_retiro_anticipado,
                    "metodo_captura": dto.metodo_captura,
                    "dispositivo_id": dto.dispositivo_id,
                    "motivo": dto.motivo,
                    "observaciones": dto.observaciones,
                    "procesado_disciplinario": True,
                },
            )

            # Si el evento NO es sancionable, no se emite ninguna sanción ni apercibimiento
            if not es_sancionable:
                asistencia.expediente_generado = None
                asistencia.apercibimiento_generado = None
                asistencia.save(update_fields=["expediente_generado", "apercibimiento_generado"])
                asistencias_guardadas.append(asistencia)
                continue

            # Evento SANCIONABLE: Aplicar escala reglamentaria
            if dto.estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE:
                asistencia.expediente_generado = None
                asistencia.apercibimiento_generado = None
                asistencia.save(update_fields=["expediente_generado", "apercibimiento_generado"])

            elif dto.estado_asistencia in (
                EstadoAsistenciaEventoEnum.TARDE_LEVE,
                EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE,
            ):
                minutos = dto.minutos_tardanza or dto.minutos_retiro_anticipado
                origen = (
                    "REUNION_TARDANZA_LEVE"
                    if dto.estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_LEVE
                    else "REUNION_RETIRO_LEVE"
                )
                motivo_ap = dto.motivo or f"Impuntualidad leve ({minutos} min) en {evento.titulo}"
                apercibimiento, exp_consolidado = WarningAccumulationService.register_warning(
                    socio_id=dto.socio_id,
                    origen_tipo=origen,
                    motivo=motivo_ap,
                    fecha_hecho=evento.fecha_programada.date(),
                    articulo_reglamento="Art. 100.a",
                    asistencia_id=asistencia.id,
                    actor=actor,
                )
                asistencia.apercibimiento_generado = apercibimiento
                if exp_consolidado:
                    asistencia.expediente_generado = exp_consolidado
                    expedientes_creados.append(
                        {
                            "socio_id": dto.socio_id,
                            "numero": exp_consolidado.numero,
                            "puntos": float(exp_consolidado.puntos),
                            "tipo": "CONSOLIDACION_3_1",
                        }
                    )
                asistencia.save(update_fields=["apercibimiento_generado", "expediente_generado"])
                apercibimientos_creados.append(
                    {
                        "socio_id": dto.socio_id,
                        "id": apercibimiento.id,
                        "origen_tipo": origen,
                        "motivo": motivo_ap,
                    }
                )

            elif dto.estado_asistencia in (
                EstadoAsistenciaEventoEnum.TARDE_GRAVE,
                EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_GRAVE,
            ):
                puntos = (
                    cls.PUNTOS_TARDANZA_GRAVE
                    if dto.estado_asistencia == EstadoAsistenciaEventoEnum.TARDE_GRAVE
                    else cls.PUNTOS_RETIRO_GRAVE
                )
                motivo_exp = (
                    dto.motivo
                    or f"Impuntualidad grave en {evento.categoria}: {evento.titulo} (Art. 100.b)"
                )
                expediente = ExpedienteWorkflowService.open_expediente(
                    motivo=motivo_exp,
                    socio_ids=[dto.socio_id],
                    actor=actor,
                    points=puntos,
                )
                asistencia.expediente_generado = expediente
                asistencia.save(update_fields=["expediente_generado"])
                expedientes_creados.append(
                    {
                        "socio_id": dto.socio_id,
                        "numero": expediente.numero,
                        "puntos": float(puntos),
                        "tipo": "TARDANZA_GRAVE",
                    }
                )

            elif dto.estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE:
                puntos = cls.get_penalty_points_for_absence(evento)
                motivo_exp = (
                    dto.motivo
                    or f"Inasistencia a {evento.categoria} ({evento.tipo}): "
                    f"{evento.titulo} (Art. 85 R.I.)"
                )
                expediente = ExpedienteWorkflowService.open_expediente(
                    motivo=motivo_exp,
                    socio_ids=[dto.socio_id],
                    actor=actor,
                    points=puntos,
                )
                asistencia.expediente_generado = expediente
                asistencia.save(update_fields=["expediente_generado"])
                expedientes_creados.append(
                    {
                        "socio_id": dto.socio_id,
                        "numero": expediente.numero,
                        "puntos": float(puntos),
                        "tipo": "INASISTENCIA_INJUSTIFICADA",
                    }
                )

            asistencias_guardadas.append(asistencia)

        logger.info(
            "Asistencia evento ID %s. Sancionable: %s. Asist: %d, Exp: %d, Aperc: %d",
            evento.id,
            es_sancionable,
            len(asistencias_guardadas),
            len(expedientes_creados),
            len(apercibimientos_creados),
        )

        return {
            "evento_id": evento.id,
            "es_sancionable": es_sancionable,
            "motivo_no_sancionable": motivo_no_sancionable,
            "total_asistencias": len(asistencias_guardadas),
            "expedientes_creados": expedientes_creados,
            "apercibimientos_creados": apercibimientos_creados,
        }
