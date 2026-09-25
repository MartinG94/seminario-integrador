import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { SocioApiService, SocioLegajoDTO } from '../../services/socio-api.service';

export interface SocioLegajoDialogData {
  socioId: number | string;
  nombreSocio?: string;
  saldo?: number;
}

@Component({
  selector: 'app-socio-legajo-dialog',
  templateUrl: './socio-legajo-dialog.component.html',
  styleUrls: ['./socio-legajo-dialog.component.scss']
})
export class SocioLegajoDialogComponent implements OnInit {
  cargando = true;
  errorHttp: string | null = null;
  legajo: SocioLegajoDTO | null = null;

  get saldoPuntos(): number {
    if (this.data && this.data.saldo !== undefined && this.data.saldo !== null) {
      return this.data.saldo;
    }
    return this.legajo?.points_balance ?? 0.0;
  }


  constructor(
    public dialogRef: MatDialogRef<SocioLegajoDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: SocioLegajoDialogData,
    private socioApiService: SocioApiService
  ) {}

  ngOnInit(): void {
    this.cargarLegajo();
  }

  cargarLegajo(): void {
    this.cargando = true;
    this.errorHttp = null;

    this.socioApiService.getLegajo(this.data.socioId).subscribe({
      next: (res) => {
        this.legajo = res;
        this.cargando = false;
      },
      error: (err) => {
        this.cargando = false;
        if (err.status === 403) {
          this.errorHttp = 'No posee autorización para consultar este legajo (CA4).';
        } else if (err.status === 404) {
          this.errorHttp = 'El socio solicitado no fue encontrado en el padrón.';
        } else {
          this.errorHttp = 'Ocurrió un error al cargar la información del legajo. Verifique la conexión.';
        }
      }
    });
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  getBadgeClase(category: string): string {
    return category === 'ACTIVE' ? 'badge-mat-primary' : 'badge-mat-info';
  }

  getEstadoClase(isEnabled: boolean): string {
    return isEnabled ? 'badge-mat-success' : 'badge-mat-danger';
  }
}
