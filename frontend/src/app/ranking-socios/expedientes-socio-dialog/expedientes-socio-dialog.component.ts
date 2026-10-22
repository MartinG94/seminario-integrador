import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

import {
  ExpedienteApiService,
  ExpedienteRankingDetalle
} from '../../services/expediente-api.service';

export interface ExpedientesSocioDialogData {
  legajo: string;
  nombreSocio: string;
}

@Component({
  selector: 'app-expedientes-socio-dialog',
  templateUrl: './expedientes-socio-dialog.component.html',
  styleUrls: ['./expedientes-socio-dialog.component.scss']
})
export class ExpedientesSocioDialogComponent implements OnInit {
  expedientes: ExpedienteRankingDetalle[] = [];
  cargando = true;
  error: string | null = null;

  constructor(
    public dialogRef: MatDialogRef<ExpedientesSocioDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ExpedientesSocioDialogData,
    private expedienteApiService: ExpedienteApiService
  ) {}

  ngOnInit(): void {
    this.cargarExpedientes();
  }

  cargarExpedientes(): void {
    this.cargando = true;
    this.error = null;

    this.expedienteApiService.listarPorLegajo(this.data.legajo).subscribe({
      next: (expedientes) => {
        this.expedientes = expedientes;
        this.cargando = false;
      },
      error: (err) => {
        this.expedientes = [];
        this.cargando = false;

        if (err.status === 403) {
          this.error = 'No posee autorizaci?n para consultar los expedientes de este socio.';
        } else {
          this.error = 'No se pudieron cargar los expedientes del socio.';
        }
      }
    });
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  puntosNumero(expediente: ExpedienteRankingDetalle): number {
    return Number(expediente.puntos);
  }
}
