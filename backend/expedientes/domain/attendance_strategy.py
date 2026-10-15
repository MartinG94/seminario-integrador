"""Patrón Strategy para captura y procesamiento de asistencia a eventos institucionales (CA10).

Implementa:
- AttendanceCaptureStrategy (interfaz base abstracta).
- ManualAttendanceStrategy (carga manual desde formulario o grilla web).
- BiometricAttendanceStrategy (procesamiento de marcaciones de reloj / lector biométrico).
- AttendanceStrategyFactory (factoría desacoplada según MetodoCapturaAsistenciaEnum).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

from expedientes.models import (
    EstadoAsistenciaEventoEnum,
    MetodoCapturaAsistenciaEnum,
)

if TYPE_CHECKING:
    from expedientes.models import EventoInstitucional


@dataclass
class AttendanceRecordDTO:
    """DTO tipado que encapsula el resultado del análisis de asistencia por socio."""

    socio_id: int
    estado_asistencia: str
    hora_registro: datetime | None = None
    hora_salida: datetime | None = None
    minutos_tardanza: int = 0
    minutos_retiro_anticipado: int = 0
    metodo_captura: str = MetodoCapturaAsistenciaEnum.MANUAL
    dispositivo_id: str | None = None
    motivo: str = ""
    observaciones: str = ""


class AttendanceCaptureStrategy(ABC):
    """Estrategia abstracta de captura y tipificación de asistencia."""

    @abstractmethod
    def process(
        self,
        *,
        evento: "EventoInstitucional",
        marcaciones: list[dict[str, Any]],
        convocados_ids: list[int] | None = None,
        **kwargs: Any,
    ) -> list[AttendanceRecordDTO]:
        """Procesa una lista de marcaciones y devuelve lista de AttendanceRecordDTO."""
        raise NotImplementedError


class ManualAttendanceStrategy(AttendanceCaptureStrategy):
    """
    Estrategia para carga manual de asistencia.
    Todo socio convocado no reportado en el payload pasa automáticamente a AUSENTE.
    """

    def process(
        self,
        *,
        evento: "EventoInstitucional",
        marcaciones: list[dict[str, Any]],
        convocados_ids: list[int] | None = None,
        **kwargs: Any,
    ) -> list[AttendanceRecordDTO]:
        records: list[AttendanceRecordDTO] = []
        reported_socio_ids: set[int] = set()

        for item in marcaciones:
            socio_id = item["socio_id"]
            reported_socio_ids.add(socio_id)
            estado = item.get("estado_asistencia", EstadoAsistenciaEventoEnum.PRESENTE)
            if estado not in EstadoAsistenciaEventoEnum.values:
                raise ValueError(f"Estado de asistencia '{estado}' no es válido.")

            minutos_tardanza = int(item.get("minutos_tardanza", 0))
            if estado == EstadoAsistenciaEventoEnum.TARDE_LEVE and minutos_tardanza == 0:
                minutos_tardanza = 20
            elif estado == EstadoAsistenciaEventoEnum.TARDE_GRAVE and minutos_tardanza == 0:
                minutos_tardanza = 35

            minutos_retiro = int(item.get("minutos_retiro_anticipado", 0))
            if estado == EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE and minutos_retiro == 0:
                minutos_retiro = 20
            elif (
                estado == EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_GRAVE and minutos_retiro == 0
            ):
                minutos_retiro = 35

            hora_registro = item.get("hora_registro")
            if isinstance(hora_registro, str):
                hora_registro = datetime.fromisoformat(hora_registro)

            hora_salida = item.get("hora_salida")
            if isinstance(hora_salida, str):
                hora_salida = datetime.fromisoformat(hora_salida)

            motivo = str(item.get("motivo", "")).strip()
            observaciones = str(item.get("observaciones", "")).strip()

            records.append(
                AttendanceRecordDTO(
                    socio_id=socio_id,
                    estado_asistencia=estado,
                    hora_registro=hora_registro,
                    hora_salida=hora_salida,
                    minutos_tardanza=minutos_tardanza,
                    minutos_retiro_anticipado=minutos_retiro,
                    metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                    dispositivo_id=item.get("dispositivo_id"),
                    motivo=motivo,
                    observaciones=observaciones,
                )
            )

        # Socios citados no reportados -> AUSENTE
        if convocados_ids:
            for c_id in convocados_ids:
                if c_id not in reported_socio_ids:
                    records.append(
                        AttendanceRecordDTO(
                            socio_id=c_id,
                            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
                            metodo_captura=MetodoCapturaAsistenciaEnum.MANUAL,
                            motivo="Inasistencia no justificada (no reportado en grilla).",
                        )
                    )

        return records


class BiometricAttendanceStrategy(AttendanceCaptureStrategy):
    """
    Estrategia para lectura de reloj biométrico.
    Calcula deltas de tardanza y retiro anticipado según marcas horarias y tolerancias del evento.
    """

    def process(
        self,
        *,
        evento: "EventoInstitucional",
        marcaciones: list[dict[str, Any]],
        convocados_ids: list[int] | None = None,
        **kwargs: Any,
    ) -> list[AttendanceRecordDTO]:
        records: list[AttendanceRecordDTO] = []
        marcaciones_by_socio = {m["socio_id"]: m for m in marcaciones}
        all_socio_ids = set(convocados_ids or []) | set(marcaciones_by_socio.keys())

        tolerancia_tardanza = evento.tolerancia_tardanza_minutos
        tolerancia_retiro = evento.tolerancia_retiro_minutos
        inicio_evento = evento.fecha_programada
        fin_evento = evento.fecha_hora_cierre_efectivo or evento.fecha_fin

        for s_id in all_socio_ids:
            item = marcaciones_by_socio.get(s_id)
            if not item or not item.get("hora_registro"):
                # No hay marca de entrada -> Ausente
                motivo = item.get("motivo", "") if item else ""
                records.append(
                    AttendanceRecordDTO(
                        socio_id=s_id,
                        estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
                        metodo_captura=MetodoCapturaAsistenciaEnum.BIOMETRICO,
                        dispositivo_id=item.get("dispositivo_id") if item else None,
                        motivo=motivo or "Sin registro de huella o fichada en reloj biométrico.",
                    )
                )
                continue

            hora_registro = item["hora_registro"]
            if isinstance(hora_registro, str):
                hora_registro = datetime.fromisoformat(hora_registro)

            hora_salida = item.get("hora_salida")
            if isinstance(hora_salida, str):
                hora_salida = datetime.fromisoformat(hora_salida)

            # Cálculo de tardanza
            diff_tardanza_sec = (hora_registro - inicio_evento).total_seconds()
            minutos_tardanza = max(0, int(diff_tardanza_sec // 60))

            if minutos_tardanza <= tolerancia_tardanza:
                estado = EstadoAsistenciaEventoEnum.PRESENTE
            elif minutos_tardanza <= 30:
                estado = EstadoAsistenciaEventoEnum.TARDE_LEVE
            else:
                estado = EstadoAsistenciaEventoEnum.TARDE_GRAVE

            # Cálculo de retiro anticipado si hay hora_salida y fin_evento
            minutos_retiro = 0
            if hora_salida and fin_evento and hora_salida < fin_evento:
                diff_retiro_sec = (fin_evento - hora_salida).total_seconds()
                minutos_retiro = max(0, int(diff_retiro_sec // 60))
                if minutos_retiro > 30:
                    if estado != EstadoAsistenciaEventoEnum.TARDE_GRAVE:
                        estado = EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_GRAVE
                elif minutos_retiro > tolerancia_retiro:
                    if estado == EstadoAsistenciaEventoEnum.PRESENTE:
                        estado = EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE

            motivo = item.get("motivo", "")
            observaciones = item.get("observaciones", "")

            records.append(
                AttendanceRecordDTO(
                    socio_id=s_id,
                    estado_asistencia=estado,
                    hora_registro=hora_registro,
                    hora_salida=hora_salida,
                    minutos_tardanza=minutos_tardanza,
                    minutos_retiro_anticipado=minutos_retiro,
                    metodo_captura=MetodoCapturaAsistenciaEnum.BIOMETRICO,
                    dispositivo_id=item.get("dispositivo_id"),
                    motivo=motivo,
                    observaciones=observaciones,
                )
            )

        return records


class AttendanceStrategyFactory:
    """Factoría de instanciación de estrategias de asistencia."""

    _STRATEGIES: dict[str, type[AttendanceCaptureStrategy]] = {
        MetodoCapturaAsistenciaEnum.MANUAL: ManualAttendanceStrategy,
        MetodoCapturaAsistenciaEnum.BIOMETRICO: BiometricAttendanceStrategy,
        "MANUAL": ManualAttendanceStrategy,
        "BIOMETRICO": BiometricAttendanceStrategy,
    }

    @classmethod
    def get_strategy(cls, metodo: str | MetodoCapturaAsistenciaEnum) -> AttendanceCaptureStrategy:
        metodo_key = str(metodo).upper()
        strategy_class = cls._STRATEGIES.get(metodo_key)
        if not strategy_class:
            opciones = list(cls._STRATEGIES.keys())
            raise ValueError(f"Método de captura '{metodo}' no reconocido. Opciones: {opciones}")
        return strategy_class()
