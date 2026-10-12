import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, Subject, throwError } from 'rxjs';
import { MatDialogModule } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { SocioApiService, SocioLegajoDTO, OwnPointsHistoryDTO } from '../../services/socio-api.service';
import { AuthService } from '../../services/auth.service';
import { AppliedPointsHistoryComponent } from '../../mis-expedientes/applied-points-history/applied-points-history.component';
import { AppliedResolutionDialogComponent } from '../../mis-expedientes/applied-resolution-dialog/applied-resolution-dialog.component';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog.component';
import { NotificationService } from '../../services/notification.service';

describe('SocioLegajoDialogComponent', () => {
  let component: SocioLegajoDialogComponent;
  let fixture: ComponentFixture<SocioLegajoDialogComponent>;
  let socioApiServiceSpy: jasmine.SpyObj<SocioApiService>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<SocioLegajoDialogComponent>>;
  let notifications: jasmine.SpyObj<NotificationService>;

  const mockLegajo: SocioLegajoDTO = {
    id: 1,
    legajo: '74907',
    first_name: 'Lucas',
    last_name: 'Gastiaburu',
    email: '74907@aveit.test',
    role: 'SOCIO',
    category: 'SENIOR',
    category_display: 'Senior',
    subcomision: 'Cómputos',
    social_year: 4,
    is_enabled: true,
    points_balance: 3.5
  };

  const mockHistory: OwnPointsHistoryDTO = {
    points_balance: 3.5, entries: [{
      movement_id: 17, applied_points: 3.5,
      historical_case: { id: 101, number: 'HIST-101', recorded_at: null, state: 'emitido' },
      resolution: { id: 201, text: 'VISTO\nCONSIDERANDO\nSE RESUELVE', regulations: ['Art. 93'] },
      managed_case: null
    }]
  };

  beforeEach(async () => {
    socioApiServiceSpy = jasmine.createSpyObj('SocioApiService', ['getLegajo', 'getPointsHistory']);
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);
    notifications = jasmine.createSpyObj('NotificationService', ['error']);

    socioApiServiceSpy.getLegajo.and.returnValue(of(mockLegajo));
    socioApiServiceSpy.getPointsHistory.and.returnValue(of(mockHistory));

    await TestBed.configureTestingModule({
      imports: [CommonModule, MatDialogModule, NoopAnimationsModule],
      declarations: [SocioLegajoDialogComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [
        { provide: AuthService, useValue: { perfil$: of(null) } },
        { provide: NotificationService, useValue: notifications },
        { provide: SocioApiService, useValue: socioApiServiceSpy },
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: { socioId: 1, nombreSocio: 'Lucas Gastiaburu' } }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SocioLegajoDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe cargar los datos del legajo al inicializar (CA2)', () => {
    expect(socioApiServiceSpy.getLegajo).toHaveBeenCalledWith(1, undefined);
    expect(component.cargando).toBeFalse();
    expect(component.legajo).toEqual(mockLegajo);
    expect(component.errorHttp).toBeNull();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('74907');
    expect(compiled.textContent).toContain('Gastiaburu');
    expect(compiled.textContent).toContain('Cómputos');
    expect(compiled.textContent).toContain('Saldo de Puntos');
    expect(compiled.textContent).toContain('3.5 pts');
  });

  it('debe manejar error 403 Forbidden cuando un socio intenta ver un legajo ajeno (CA4)', () => {
    socioApiServiceSpy.getLegajo.and.returnValue(
      throwError(() => ({ status: 403, error: { detail: 'Forbidden' } }))
    );

    component.cargarLegajo();
    fixture.detectChanges();

    expect(component.cargando).toBeFalse();
    expect(notifications.error).toHaveBeenCalledOnceWith('No posee autorización para consultar este legajo.');
    expect(fixture.nativeElement.textContent).not.toContain('No posee autorización');
    expect(fixture.nativeElement.querySelector('[role="alert"]')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Reintentar');
    expect(component.legajo).toBeNull();
  });

  it('usa el saldo fresco de la API aunque el snapshot del ranking sea diferente (TS77.51)', () => {
    component.data.saldo = -7.5;
    fixture.detectChanges();
    expect(component.saldoPuntos).toBe(3.5);
    expect(fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]').textContent).toContain('+3.5 pts');
  });

  [undefined, null, Number.NaN, Number.POSITIVE_INFINITY].forEach(points => {
    it(`ignora saldo legado ${String(points)} y usa el historial confirmado sin snapshot (TS77.58)`, () => {
      component.data.saldo = 99;
      socioApiServiceSpy.getLegajo.and.returnValue(of<SocioLegajoDTO>({ ...mockLegajo, points_balance: points }));
      component.cargarLegajo();
      fixture.detectChanges();
      expect(component.saldoPuntos).toBe(3.5);
      const balance: HTMLElement = fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]');
      expect(balance.textContent).toContain('3.5 pts');
      expect(balance.textContent).not.toContain('99');
      expect(balance.textContent).not.toMatch(/\b0\s*pts\b/);
    });
  });

  it('muestra cero sólo cuando la API lo confirma (TS77.51)', () => {
    component.data.saldo = -7.5;
    socioApiServiceSpy.getLegajo.and.returnValue(of<SocioLegajoDTO>({ ...mockLegajo, points_balance: 0 }));
    socioApiServiceSpy.getPointsHistory.and.returnValue(of({ points_balance: 0, entries: [] }));
    component.cargarLegajo();
    fixture.detectChanges();
    expect(component.saldoPuntos).toBe(0);
    expect(fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]').textContent).toContain('0 pts');
  });

  it('durante una nueva lectura oculta el saldo anterior y al finalizar muestra el nuevo (TS77.51)', () => {
    const response = new Subject<SocioLegajoDTO>();
    socioApiServiceSpy.getLegajo.and.returnValue(response);
    component.cargarLegajo();
    fixture.detectChanges();
    expect(component.saldoPuntos).toBeNull();
    expect(fixture.nativeElement.querySelector('.state-loading')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]')).toBeNull();
    socioApiServiceSpy.getPointsHistory.and.returnValue(of({
      points_balance: -2, entries: [{ ...mockHistory.entries[0], applied_points: -2 }]
    }));
    response.next({ ...mockLegajo, points_balance: -2 });
    response.complete();
    fixture.detectChanges();
    expect(component.saldoPuntos).toBe(-2);
    expect(fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]').textContent).toContain('-2 pts');
  });

  it('confirma saldo y resoluciones juntos aunque el legajo y el ranking tengan otro saldo (TS77.58)', () => {
    component.data.saldo = 99;
    socioApiServiceSpy.getLegajo.and.returnValue(of({ ...mockLegajo, points_balance: -7.5 }));
    socioApiServiceSpy.getPointsHistory.and.returnValue(of({
      points_balance: 2, entries: [{ ...mockHistory.entries[0], applied_points: 2 }]
    }));
    component.cargarLegajo();
    fixture.detectChanges();
    expect(socioApiServiceSpy.getPointsHistory).toHaveBeenCalledWith(1, undefined);
    expect(component.saldoPuntos).toBe(2);
    expect(fixture.nativeElement.textContent).toContain('HIST-101');
    expect(fixture.nativeElement.textContent).not.toContain('-7.5 pts');
  });

  it('conserva la ficha pero desconoce el saldo ante falla del historial, sin fallback legado ni cero (TS77.58)', () => {
    component.data.saldo = 99;
    socioApiServiceSpy.getPointsHistory.and.returnValue(throwError(() => ({ status: 503 })));
    component.cargarLegajo();
    fixture.detectChanges();
    expect(component.legajo).toEqual(mockLegajo);
    expect(component.saldoPuntos).toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="legajo-points-balance"]').textContent).toContain('No disponible');
    expect(fixture.nativeElement.querySelector('[data-testid="applied-resolutions"]')).toBeNull();
    expect(notifications.error).toHaveBeenCalledWith('No se pudieron consultar los puntos y las resoluciones de este socio.');
  });

  it('debe cerrar el modal al invocar cerrar()', () => {
    component.cerrar();
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('mantiene la fuente institucional en la consulta y en su reintento', () => {
    component.data = { socioId: 1, identitySource: 'institutional' };
    socioApiServiceSpy.getLegajo.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargarLegajo();
    socioApiServiceSpy.getLegajo.and.returnValue(of(mockLegajo));
    component.cargarLegajo();

    expect(socioApiServiceSpy.getLegajo.calls.mostRecent().args)
      .toEqual([1, 'institutional']);
    expect(component.legajo).toEqual(mockLegajo);
    expect(component.errorHttp).toBeNull();
  });

  it('muestra Exviajero sin año ficticio y preserva la vigencia de su cuenta', () => {
    const exTraveler: SocioLegajoDTO = {
      ...mockLegajo, category: 'EX_TRAVELER', category_display: 'Exviajero',
      social_year: null, role: 'SOCIO', is_enabled: true
    };
    socioApiServiceSpy.getLegajo.and.returnValue(of(exTraveler));
    component.cargarLegajo();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const yearItem = Array.from(compiled.querySelectorAll('.data-item'))
      .find(item => item.querySelector('.data-label')?.textContent === 'Año Social');
    expect(yearItem).toBeUndefined();
    expect(compiled.textContent).toContain('Exviajero');
    expect(compiled.textContent).not.toContain('º Año');
    expect(compiled.textContent).toContain('Habilitado');
    expect(component.legajo?.social_year).toBeNull();
  });

  it('muestra Sin clasificación para año desconocido sin inventar Junior ni cero', () => {
    const unknown: SocioLegajoDTO = {
      ...mockLegajo, category: 'UNKNOWN', category_display: 'Sin clasificación', social_year: null
    };
    socioApiServiceSpy.getLegajo.and.returnValue(of(unknown));
    component.cargarLegajo();
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Sin clasificación');
    expect(compiled.textContent).not.toContain('º Año');
    expect(compiled.textContent).not.toContain('Junior');
    expect(component.legajo?.social_year).toBeNull();
  });

  it('indica Sin legajo cuando la persona institucional no tiene legajo real', () => {
    socioApiServiceSpy.getLegajo.and.returnValue(of<SocioLegajoDTO>({ ...mockLegajo, legajo: null }));
    component.cargarLegajo();
    fixture.detectChanges();
    const badge: HTMLElement = fixture.nativeElement.querySelector('.socio-legajo-badge');
    expect(badge.textContent).toContain('Legajo:');
    expect(badge.textContent).toContain('Sin legajo');
    expect(component.legajo?.legajo).toBeNull();
  });

  [1, 2, 3, 6].forEach(year => {
    it(`muestra el año social ${year} con su categoría vigente`, () => {
      const category = year <= 2 ? 'JUNIOR' : 'SENIOR';
      socioApiServiceSpy.getLegajo.and.returnValue(of<SocioLegajoDTO>({
        ...mockLegajo, social_year: year, category,
        category_display: year <= 2 ? 'Junior' : 'Senior'
      }));
      component.cargarLegajo();
      fixture.detectChanges();
      expect((fixture.nativeElement as HTMLElement).textContent).toContain(`${year}º Año`);
    });
  });

  [0, 7].forEach(year => {
    it(`evita mostrar el año ${year} de un DTO fuera de escala`, () => {
      socioApiServiceSpy.getLegajo.and.returnValue(of<SocioLegajoDTO>({
        ...mockLegajo, social_year: year, category: 'UNKNOWN', category_display: 'Sin clasificación'
      }));
      component.cargarLegajo();
      fixture.detectChanges();
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.textContent).toContain('Sin clasificación');
      expect(compiled.textContent).not.toContain(`${year}º Año`);
    });
  });

  it('oculta la ficha anterior si una nueva consulta falla', () => {
    socioApiServiceSpy.getLegajo.and.returnValue(throwError(() => ({ status: 404 })));
    component.cargarLegajo();
    fixture.detectChanges();
    expect(component.legajo).toBeNull();
    expect(fixture.nativeElement.querySelector('.dialog-content')).toBeNull();
    expect(notifications.error).toHaveBeenCalledOnceWith('El socio solicitado no fue encontrado en el padrón.');
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('no fue encontrado');
    expect(fixture.nativeElement.querySelector('[role="alert"]')).toBeNull();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Reintentar');
  });
});
