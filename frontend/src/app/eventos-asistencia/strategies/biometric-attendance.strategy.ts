import { Injectable } from '@angular/core';
import { ConvocadoAsistenciaDTO, EstadoAsistenciaEvento, MetodoCapturaAsistencia } from '../models/eventos-asistencia.models';
import { AttendanceCaptureResult, IAttendanceCaptureStrategy } from './attendance-strategy.interface';

@Injectable({
  providedIn: 'root'
})
export class BiometricAttendanceStrategy implements IAttendanceCaptureStrategy {
  readonly tipo: MetodoCapturaAsistencia = 'BIOMETRICO';
  readonly nombre = 'Marcación Biométrica';
  readonly descripcion = 'Captura simulada de huella dactilar/reloj con validación de horario y feedback auditivo.';

  capturar(
    socio: ConvocadoAsistenciaDTO,
    horaReferenciaInicio?: Date,
    toleranciaMinutos = 15
  ): AttendanceCaptureResult {
    const ahora = new Date();
    let estado: EstadoAsistenciaEvento = 'PRESENTE';
    let minutosTardanza = 0;
    let motivo = 'Registro biométrico en sede';

    if (horaReferenciaInicio) {
      const diffMs = ahora.getTime() - horaReferenciaInicio.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins > 0) {
        minutosTardanza = diffMins;
        if (diffMins > 30) {
          estado = 'TARDANZA_GRAVE';
          motivo = `Marcación biométrica tardía (+${diffMins} min, gravedad estatutaria)`;
        } else if (diffMins > toleranciaMinutos) {
          estado = 'TARDANZA_LEVE';
          motivo = `Marcación biométrica con tardanza leve (+${diffMins} min)`;
        }
      }
    }

    this.reproducirBeepConfirmacion();

    return {
      socioId: socio.socio_id,
      estado,
      horaRegistro: ahora.toISOString(),
      minutosTardanza,
      motivo: socio.motivo ? socio.motivo : motivo,
      feedbackMensaje: `Huella verificada para ${socio.socio_nombre} (${estado}).`
    };
  }

  reproducirBeepConfirmacion(): void {
    try {
      const audioWin = window as unknown as { AudioContext?: typeof AudioContext; webkitAudioContext?: typeof AudioContext };
      const AudioCtx = audioWin.AudioContext || audioWin.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.15);
    } catch {
      // AudioContext ignorado si no está habilitado en entorno headless
    }
  }
}
