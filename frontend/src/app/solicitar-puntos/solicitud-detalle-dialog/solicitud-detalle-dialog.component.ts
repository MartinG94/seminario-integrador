import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import type { SolicitudMonitoreo } from '../../services/expediente-api.service';

@Component({
  selector: 'app-solicitud-detalle-dialog',
  templateUrl: './solicitud-detalle-dialog.component.html',
  styleUrls: ['./solicitud-detalle-dialog.component.scss']
})
export class SolicitudDetalleDialogComponent {
  constructor(
    public dialogRef: MatDialogRef<SolicitudDetalleDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public solicitud: SolicitudMonitoreo
  ) {}

  cerrar(): void {
    this.dialogRef.close();
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
}
