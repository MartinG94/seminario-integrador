import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { AppliedPointsEntryDTO, SocioApiService, SocioIdentitySource, SocioLegajoDTO, OwnPointsHistoryDTO } from '../../services/socio-api.service';
import { NotificationService } from '../../services/notification.service';
import { AuthService } from '../../services/auth.service';
import { PointsHistoryStatus } from '../../mis-expedientes/applied-points-history/applied-points-history.component';
import { Subscription } from 'rxjs';
import { skip } from 'rxjs/operators';

export interface SocioLegajoDialogData {
  socioId: number | string;
  nombreSocio?: string;
  saldo?: number;
  identitySource?: SocioIdentitySource;
}

@Component({
  selector: 'app-socio-legajo-dialog',
  templateUrl: './socio-legajo-dialog.component.html',
  styleUrls: ['./socio-legajo-dialog.component.scss']
})
export class SocioLegajoDialogComponent implements OnInit, OnDestroy {
  cargando = true;
  errorHttp: string | null = null;
  legajo: SocioLegajoDTO | null = null;
  history: OwnPointsHistoryDTO | null = null;
  historyStatus: PointsHistoryStatus = 'idle';
  private loadSubscriptions = new Subscription();
  private sessionSubscription: Subscription | null = null;
  private readonly emptyEntries: readonly AppliedPointsEntryDTO[] = [];

  get appliedEntries(): readonly AppliedPointsEntryDTO[] { return this.history?.entries ?? this.emptyEntries; }

  get saldoPuntos(): number | null {
    const points = this.historyStatus === 'ready' ? this.history?.points_balance : null;
    return typeof points === 'number' && Number.isFinite(points) ? points : null;
  }

  get socialYearLabel(): string | null {
    const year = this.legajo?.social_year;
    if (
      !this.legajo || this.legajo.category === 'EX_TRAVELER' || this.legajo.category === 'UNKNOWN' ||
      typeof year !== 'number' || !Number.isInteger(year) || year < 1 || year > 6
    ) {
      return null;
    }
    return `${year}º Año`;
  }

  constructor(
    public dialogRef: MatDialogRef<SocioLegajoDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: SocioLegajoDialogData,
    private socioApiService: SocioApiService,
    private notifications: NotificationService,
    private auth: AuthService
  ) {}

  ngOnInit(): void {
    this.sessionSubscription = this.auth.perfil$.pipe(skip(1)).subscribe(() => {
      this.loadSubscriptions.unsubscribe();
      this.legajo = null;
      this.history = null;
      this.historyStatus = 'idle';
      this.dialogRef.close();
    });
    this.cargarLegajo();
  }

  ngOnDestroy(): void {
    this.loadSubscriptions.unsubscribe();
    this.sessionSubscription?.unsubscribe();
    this.legajo = null;
    this.history = null;
  }

  cargarLegajo(): void {
    this.loadSubscriptions.unsubscribe();
    this.loadSubscriptions = new Subscription();
    this.cargando = true;
    this.errorHttp = null;
    this.legajo = null;
    this.history = null;
    this.historyStatus = 'loading';

    this.loadSubscriptions.add(this.socioApiService.getLegajo(this.data.socioId, this.data.identitySource).subscribe({
      next: (res) => {
        this.legajo = res;
        this.cargando = false;
        this.loadSubscriptions.add(this.socioApiService.getPointsHistory(this.data.socioId, this.data.identitySource).subscribe({
          next: history => {
            this.history = history;
            this.historyStatus = 'ready';
          },
          error: (error: unknown) => {
            this.history = null;
            if ((error as { status?: number } | null)?.status === 404) {
              this.historyStatus = 'unavailable';
              return;
            }
            this.historyStatus = 'error';
            this.notifications.error('No se pudieron consultar los puntos y las resoluciones de este socio.');
          }
        }));
      },
      error: (err) => {
        this.cargando = false;
        this.historyStatus = 'error';
        if (err.status === 403) {
          this.errorHttp = 'No posee autorización para consultar este legajo.';
        } else if (err.status === 404) {
          this.errorHttp = 'El socio solicitado no fue encontrado en el padrón.';
        } else {
          this.errorHttp = 'Ocurrió un error al cargar la información del legajo. Verifique la conexión.';
        }
        this.notifications.error(this.errorHttp);
      }
    }));
  }

  cerrar(): void {
    this.dialogRef.close();
  }

  getEstadoClase(isEnabled: boolean): string {
    return isEnabled ? 'badge-mat-success' : 'badge-mat-danger';
  }
}
