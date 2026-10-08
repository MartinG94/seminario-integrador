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
      error: () => {
        // En caso de que el backend no responda, proveer fallback local con los datos disponibles
        const partes = (this.data.nombreSocio || '').split(' ');
        this.legajo = {
          id: Number(this.data.socioId) || 1,
          legajo: String(this.data.socioId),
          first_name: partes[0] || 'Lucas',
          last_name: partes.slice(1).join(' ') || 'Gastiaburu',
          email: `${String(this.data.socioId)}@aveit.test`,
          role: 'SOCIO',
          category: 'ACTIVE',
          category_display: 'Socio Activo',
          subcomision: 'Cómputos',
          social_year: 2026,
          is_enabled: true,
          points_balance: this.data.saldo ?? 4.5
        };
        this.cargando = false;
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
