import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import type { SolicitudMonitoreo } from '../../services/expediente-api.service';
import { formatCaseNumber } from '../../utils/case-number.util';
import {
  parseReglamentoCite,
  parseReglamentosList,
  ReglamentoCiteView
} from '../../utils/reglamento-format.util';

@Component({
  selector: 'app-solicitud-detalle-dialog',
  templateUrl: './solicitud-detalle-dialog.component.html',
  styleUrls: ['./solicitud-detalle-dialog.component.scss']
})
export class SolicitudDetalleDialogComponent {
  reglamentoExpandido: string | null = null;

  constructor(
    public dialogRef: MatDialogRef<SolicitudDetalleDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public solicitud: SolicitudMonitoreo
  ) {}

  cerrar(): void {
    this.dialogRef.close();
  }

  formatCaseNumber(numero: string | null | undefined): string {
    return formatCaseNumber(numero);
  }

  get reglamentosCitas(): ReglamentoCiteView[] {
    return parseReglamentosList(this.solicitud?.reglamentos_respaldantes);
  }

  get reglamentoExpandidoDetalle(): ReglamentoCiteView | null {
    if (!this.reglamentoExpandido) return null;
    return parseReglamentoCite(this.reglamentoExpandido);
  }

  toggleExpandirReglamento(raw: string): void {
    this.reglamentoExpandido = this.reglamentoExpandido === raw ? null : raw;
  }

  obtenerClaseEstado(estadoProcesal?: string): string {
    switch (estadoProcesal) {
      case 'creado':
        return 'badge-mat-info';
      case 'justificando':
      case 'en_descargo':
        return 'badge-mat-warning';
      case 'revision_resolucion':
      case 'espera_resolucion':
      case 'evaluacion':
        return 'badge-mat-primary';
      case 'pendiente_correos':
        return 'badge-mat-rose';
      case 'emitido':
      case 'resuelto':
        return 'badge-mat-success';
      case 'rechazado':
      case 'desestimado':
        return 'badge-mat-danger';
      case 'borrador':
      default:
        return 'badge-mat-info';
    }
  }

  obtenerClaseUrgencia(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente':
        return 'badge-mat-danger';
      case 'baja':
        return 'badge-mat-success';
      case 'normal':
      default:
        return 'badge-mat-info';
    }
  }

  obtenerIconoUrgencia(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente':
        return 'priority_high';
      case 'baja':
        return 'arrow_downward';
      case 'normal':
      default:
        return 'horizontal_rule';
    }
  }
}
