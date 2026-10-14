import { Observable } from 'rxjs';
import { ConvocadoAsistenciaDTO, EstadoAsistenciaEvento, MetodoCapturaAsistencia } from '../models/eventos-asistencia.models';

export interface AttendanceCaptureResult {
  socioId: number;
  estado: EstadoAsistenciaEvento;
  horaRegistro: string;
  minutosTardanza?: number;
  motivo: string;
  feedbackMensaje: string;
}

export interface IAttendanceCaptureStrategy {
  readonly tipo: MetodoCapturaAsistencia;
  readonly nombre: string;
  readonly descripcion: string;

  capturar(
    socio: ConvocadoAsistenciaDTO,
    horaReferenciaInicio?: Date,
    toleranciaMinutos?: number
  ): Observable<AttendanceCaptureResult> | Promise<AttendanceCaptureResult> | AttendanceCaptureResult;
}
