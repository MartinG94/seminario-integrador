import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { formatCaseNumber, humanizeEstado } from '../../utils/case-number.util';

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
export class ExpedientesSocioDialogComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();
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

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  cargarExpedientes(): void {
    this.cargando = true;
    this.error = null;

    this.expedienteApiService.listarPorSocio(this.data.legajo).pipe(takeUntil(this.destroy$)).subscribe({
      next: (expedientes) => {
        this.expedientes = expedientes;
        this.cargando = false;
      },
      error: () => {
        this.expedientes = [];
        this.cargando = false;
        this.error = 'No se pudieron cargar los expedientes del socio.';
      }
    });
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  puntosNumero(expediente: ExpedienteRankingDetalle): number {
    return Number(expediente.puntos);
  }

  formatCaseNumber(numero: string | null | undefined): string {
    return formatCaseNumber(numero);
  }

  humanizeEstado(estado: string | null | undefined): string {
    return humanizeEstado(estado);
  }
}
