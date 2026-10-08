import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { CalendarioVersionDto, CreateCalendarioVersionRequest } from '../../services/calendario-api.service';

export interface NuevaVersionDialogData {
  versionesDisponibles: CalendarioVersionDto[];
  versionActivaActual: CalendarioVersionDto | null;
}

@Component({
  selector: 'app-nueva-version-dialog',
  templateUrl: './nueva-version-dialog.component.html',
  styleUrls: ['./nueva-version-dialog.component.scss']
})
export class NuevaVersionDialogComponent implements OnInit {
  nombre = '';
  vigenciaDesde = '';
  vigenciaHasta = '';
  motivoCambio = '';
  activa = true;
  clonarFeriados = true;
  versionBaseId: number | null = null;
  errorMensaje = '';

  constructor(
    public dialogRef: MatDialogRef<NuevaVersionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: NuevaVersionDialogData
  ) {}

  ngOnInit(): void {
    const today = new Date().toISOString().split('T')[0];
    this.vigenciaDesde = today;

    if (this.data.versionActivaActual) {
      this.versionBaseId = this.data.versionActivaActual.version;
      const nextNum = (this.data.versionesDisponibles.length || 1) + 1;
      this.nombre = `Calendario Oficial AVEIT 2026 - v${nextNum}`;
    } else {
      this.nombre = 'Calendario Oficial AVEIT 2026 - v2';
    }
  }

  cancelar(): void {
    this.dialogRef.close(null);
  }

  guardar(): void {
    this.errorMensaje = '';

    if (!this.nombre.trim()) {
      this.errorMensaje = 'El nombre de la versión es obligatorio.';
      return;
    }

    if (!this.vigenciaDesde) {
      this.errorMensaje = 'La fecha de inicio de vigencia es obligatoria.';
      return;
    }

    if (!this.motivoCambio.trim() || this.motivoCambio.trim().length < 5) {
      this.errorMensaje = 'Debe ingresar una justificación formal de auditoría de al menos 5 caracteres (CA2).';
      return;
    }

    const request: CreateCalendarioVersionRequest = {
      nombre: this.nombre.trim(),
      vigencia_desde: this.vigenciaDesde,
      vigencia_hasta: this.vigenciaHasta ? this.vigenciaHasta : null,
      activa: this.activa,
      motivo_cambio: this.motivoCambio.trim(),
      clonar_de_version_id: this.clonarFeriados ? this.versionBaseId : null,
      feriados: []
    };

    this.dialogRef.close(request);
  }
}
