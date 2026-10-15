import { Component, Inject, OnInit, Optional } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import {
  ConvocadoAsistenciaDTO,
  EstadoAsistenciaEvento,
  EventoInstitucional
} from '../../../../models/evento.model';

export interface ActuacionPrevista {
  socioId: number;
  socioNombre: string;
  socioLegajo: string;
  estadoAsistencia: EstadoAsistenciaEvento;
  tipoActuacion: 'EXPEDIENTE' | 'APERCIBIMIENTO' | 'NINGUNA';
  actuacionLabel: string;
  norma: string;
  puntos: number;
  motivo: string;
}

export interface ResumenCierreDialogData {
  evento: EventoInstitucional;
  convocados: ConvocadoAsistenciaDTO[];
}

@Component({
  selector: 'app-resumen-cierre-dialog',
  templateUrl: './resumen-cierre-dialog.component.html',
  styleUrls: ['./resumen-cierre-dialog.component.scss']
})
export class ResumenCierreDialogComponent implements OnInit {
  actuacionesPrevistas: ActuacionPrevista[] = [];
  totalPresentes = 0;
  totalExpedientes = 0;
  totalApercibimientos = 0;

  constructor(
    @Optional() public dialogRef: MatDialogRef<ResumenCierreDialogComponent>,
    @Optional() @Inject(MAT_DIALOG_DATA) public data: ResumenCierreDialogData
  ) {}

  ngOnInit(): void {
    if (this.data && this.data.evento && this.data.convocados) {
      this.calcularActuaciones();
    }
  }

  calcularActuaciones(): void {
    const evento = this.data.evento;
    const esSancionable = evento.es_sancionable ?? true;

    this.actuacionesPrevistas = this.data.convocados.map(socio => {
      let tipoActuacion: 'EXPEDIENTE' | 'APERCIBIMIENTO' | 'NINGUNA' = 'NINGUNA';
      let actuacionLabel = 'Sin actuación disciplinaria';
      let norma = 'Asistencia conforme';
      let puntos = 0;

      if (socio.estado_asistencia === 'PRESENTE' || socio.estado_asistencia === 'JUSTIFICADO') {
        this.totalPresentes++;
        tipoActuacion = 'NINGUNA';
        actuacionLabel = socio.estado_asistencia === 'PRESENTE' ? 'Presente en Sesión' : 'Ausencia Justificada';
        norma = 'Art. 84';
      } else if (!esSancionable) {
        tipoActuacion = 'NINGUNA';
        actuacionLabel = 'Sin sanción (Evento Extemporáneo / No Sancionable)';
        norma = 'Art. 95 (Preaviso fuera de término)';
      } else if (socio.estado_asistencia === 'AUSENTE_INJUSTIFICADO') {
        tipoActuacion = 'EXPEDIENTE';
        this.totalExpedientes++;

        if (evento.categoria === 'REUNION') {
          if (evento.tipo === 'ASAMBLEA') {
            puntos = -2.0;
            actuacionLabel = 'Expediente por Inasistencia a Asamblea';
            norma = 'Art. 85.c R.I.';
          } else if (evento.tipo === 'EXTRAORDINARIA') {
            puntos = -1.5;
            actuacionLabel = 'Expediente por Inasistencia a Reunión Extraordinaria';
            norma = 'Art. 85.b R.I.';
          } else {
            puntos = -1.0;
            actuacionLabel = 'Expediente por Inasistencia a Reunión Ordinaria';
            norma = 'Art. 85.b R.I.';
          }
        } else {
          puntos = -1.0;
          actuacionLabel = `Expediente por Inasistencia a Actividad (${evento.tipo})`;
          norma = 'Art. 85.a/d R.I.';
        }
      } else if (socio.estado_asistencia === 'TARDANZA_GRAVE' || socio.estado_asistencia === 'RETIRO_ANTICIPADO') {
        tipoActuacion = 'EXPEDIENTE';
        puntos = -0.5;
        this.totalExpedientes++;
        actuacionLabel = 'Expediente por Tardanza Grave (> 30 min)';
        norma = 'Art. 100.b R.I.';
      } else if (socio.estado_asistencia === 'TARDANZA_LEVE') {
        tipoActuacion = 'APERCIBIMIENTO';
        puntos = 0;
        this.totalApercibimientos++;
        actuacionLabel = 'Registro en Libro Mayor (Acumulación 3:1)';
        norma = 'Art. 100.a / Art. 83 (Regla 3:1)';
      }

      return {
        socioId: socio.socio_id,
        socioNombre: socio.socio_nombre,
        socioLegajo: socio.socio_legajo,
        estadoAsistencia: socio.estado_asistencia,
        tipoActuacion,
        actuacionLabel,
        norma,
        puntos,
        motivo: socio.motivo
      };
    });
  }

  cancelar(): void {
    if (this.dialogRef) {
      this.dialogRef.close(false);
    }
  }

  confirmar(): void {
    if (this.dialogRef) {
      this.dialogRef.close(true);
    }
  }
}
