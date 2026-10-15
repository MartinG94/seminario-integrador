"""Re-export del patrón Strategy para Asistencia en la capa de servicios."""

from expedientes.domain.attendance_strategy import (
    AttendanceCaptureStrategy,
    AttendanceRecordDTO,
    AttendanceStrategyFactory,
    BiometricAttendanceStrategy,
    ManualAttendanceStrategy,
)

__all__ = [
    "AttendanceCaptureStrategy",
    "AttendanceRecordDTO",
    "AttendanceStrategyFactory",
    "BiometricAttendanceStrategy",
    "ManualAttendanceStrategy",
]
