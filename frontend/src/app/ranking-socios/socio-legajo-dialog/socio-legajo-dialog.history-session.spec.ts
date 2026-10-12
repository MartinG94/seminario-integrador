import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BehaviorSubject } from 'rxjs';
import { AuthService, PerfilSocio } from '../../services/auth.service';
import { NotificationService } from '../../services/notification.service';
import { AppliedPointsHistoryComponent } from '../../mis-expedientes/applied-points-history/applied-points-history.component';
import { AppliedResolutionDialogComponent } from '../../mis-expedientes/applied-resolution-dialog/applied-resolution-dialog.component';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog.component';

describe('Ficha institucional — cancelación de historial por sesión (TS77.58)', () => {
  let fixture: ComponentFixture<SocioLegajoDialogComponent>;
  let http: HttpTestingController;
  let profiles: BehaviorSubject<PerfilSocio | null>;
  let close: jasmine.Spy;
  const metadata = {
    id: 1, legajo: '99077001', first_name: 'Ámbar', last_name: 'Faro Demo', email: 'demo@aveit.test',
    role: 'SOCIO', category: 'EX_TRAVELER', category_display: 'Exviajero', subcomision: 'Cómputos',
    social_year: null, is_enabled: true, points_balance: 99
  };
  const history = {
    points_balance: 2, entries: [{
      movement_id: 17, applied_points: 2,
      historical_case: { id: 101, number: 'HIST-101', recorded_at: null, state: 'emitido' },
      resolution: { id: 201, text: 'RESOLUCIÓN DE LA SESIÓN ANTERIOR', regulations: ['Art. 93'] },
      managed_case: null
    }]
  };

  beforeEach(async () => {
    profiles = new BehaviorSubject<PerfilSocio | null>(null);
    close = jasmine.createSpy('close');
    await TestBed.configureTestingModule({
      imports: [CommonModule, HttpClientTestingModule, MatDialogModule, NoopAnimationsModule],
      declarations: [SocioLegajoDialogComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [
        { provide: AuthService, useValue: { perfil$: profiles.asObservable() } },
        { provide: NotificationService, useValue: { error: jasmine.createSpy('error') } },
        { provide: MAT_DIALOG_DATA, useValue: { socioId: 1, identitySource: 'institutional' } },
        { provide: MatDialogRef, useValue: { close } }
      ]
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(SocioLegajoDialogComponent);
    fixture.detectChanges();
  });

  afterEach(() => { fixture.destroy(); http.verify(); });

  it('cancela metadata anterior al reintentar y también al salir de sesión', () => {
    const previous = http.expectOne(r => r.url.endsWith('/socios/1/legajo/'));
    fixture.componentInstance.cargarLegajo();
    const current = http.expectOne(r => r.url.endsWith('/socios/1/legajo/'));
    expect(previous.cancelled).toBeTrue();
    profiles.next(null);
    expect(current.cancelled).toBeTrue();
    expect(close).toHaveBeenCalledOnceWith();
    expect(fixture.componentInstance.legajo).toBeNull();
  });

  it('cancela historial pendiente y no conserva el saldo del legajo tras salir', () => {
    http.expectOne(r => r.url.endsWith('/socios/1/legajo/')).flush(metadata);
    const request = http.expectOne(r => r.url.endsWith('/socios/1/points-history/'));
    expect(request.request.params.get('identity_source')).toBe('institutional');
    profiles.next(null);
    fixture.detectChanges();
    expect(request.cancelled).toBeTrue();
    expect(fixture.componentInstance.history).toBeNull();
    expect(fixture.componentInstance.saldoPuntos).toBeNull();
    expect(fixture.nativeElement.textContent).not.toContain('99 pts');
  });

  it('retira datos confirmados y cierra el detalle anidado de la sesión anterior', fakeAsync(() => {
    http.expectOne(r => r.url.endsWith('/socios/1/legajo/')).flush(metadata);
    http.expectOne(r => r.url.endsWith('/socios/1/points-history/')).flush(history);
    fixture.detectChanges();
    expect(fixture.componentInstance.saldoPuntos).toBe(2);
    (fixture.nativeElement.querySelector('[data-testid="open-applied-resolution"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    tick();
    expect(document.querySelector('[role="dialog"]')?.textContent).toContain('RESOLUCIÓN DE LA SESIÓN ANTERIOR');
    profiles.next(null);
    fixture.detectChanges();
    tick();
    expect(document.querySelector('[role="dialog"]')).toBeNull();
    expect(fixture.componentInstance.appliedEntries).toEqual([]);
    expect(document.body.textContent).not.toContain('RESOLUCIÓN DE LA SESIÓN ANTERIOR');
    fixture.destroy();
    flush();
  }));
});
