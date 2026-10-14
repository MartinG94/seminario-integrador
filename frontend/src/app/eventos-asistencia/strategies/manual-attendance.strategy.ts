import { Injectable } from '@angular/core';
import { ConvocadoAsistenciaDTO, MetodoCapturaAsistencia } from '../models/eventos-asistencia.models';
import { AttendanceCaptureResult, IAttendanceCaptureStrategy } from './attendance-strategy.interface';

@Injectable({
  providedIn: 'root'
})
export class ManualAttendanceStrategy implements IAttendanceCaptureStrategy {
  readonly tipo: MetodoCapturaAsistencia = 'MANUAL';
  readonly nombre = 'Marcación Manual';
  readonly descripcion = 'Carga manual de estados y motivos circunstanciados en la planilla.';

  capturar(
    socio: ConvocadoAsistenciaDTO,
    horaReferenciaInicio?: Date,
    toleranciaMinutos = 15
  ): AttendanceCaptureResult {
    const ahora = new Date();
    let minutosTardanza = socio.minutos_tardanza || 0;

    if (horaReferenciaInicio && socio.estado_asistencia === 'PRESENTE') {
      const diffMs = ahora.getTime() - horaReferenciaInicio.getTime();
      const diffMins = Math.max(0, Math.floor(diffMs / 60000));
      if (diffMins > toleranciaMinutos) {
        minutosTardanza = diffMins;
      }
    }

    return {
      socioId: socio.socio_id,
      estado: socio.estado_asistencia,
      horaRegistro: ahora.toISOString(),
      minutosTardanza,
      motivo: socio.motivo || 'Marcación manual en planilla',
      feedbackMensaje: `Marcación manual registrada para ${socio.socio_nombre}: ${socio.estado_asistencia}`
    };
  }
}
