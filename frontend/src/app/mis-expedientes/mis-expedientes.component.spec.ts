import { CommonModule } from '@angular/common';
import { A11yModule } from '@angular/cdk/a11y';
import { HttpClientTestingModule, HttpTestingController, TestRequest } from '@angular/common/http/testing';
import { async, ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { MisExpedientesComponent } from './mis-expedientes.component';
import { NotificationService } from '../services/notification.service';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';
import { AuthService, PerfilSocio } from '../services/auth.service';
import { BehaviorSubject } from 'rxjs';
import { environment } from '../../environments/environment';
import { AppliedResolutionDialogComponent } from './applied-resolution-dialog/applied-resolution-dialog.component';
import { AppliedPointsHistoryComponent } from './applied-points-history/applied-points-history.component';

describe('MisExpedientesComponent', () => {
  let component: MisExpedientesComponent;
  let fixture: ComponentFixture<MisExpedientesComponent>;
  let notifications: jasmine.SpyObj<NotificationService>;

  beforeEach(async(() => {
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'registerDialogContainer']);
    notifications.registerDialogContainer.and.returnValue(() => undefined);
    TestBed.configureTestingModule({
      imports: [A11yModule, HttpClientTestingModule, FormsModule, MatDialogModule, MatButtonModule, NoopAnimationsModule],
      declarations: [MisExpedientesComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [TribunalDataService, { provide: NotificationService, useValue: notifications }]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MisExpedientesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('conserva las etiquetas de revisión, firma y envío sin deducir el estado desde descargos (TS77.56)', () => {
    expect(component.getEstadoLabel('revision_resolucion')).toBe('En Revisión');
    expect(component.getEstadoLabel('espera_resolucion')).toBe('Pendiente de Firma');
    expect(component.getEstadoLabel('pendiente_correos')).toBe('Pendiente de Envío');
    expect(component.getEstadoBadgeClass('espera_resolucion')).toBe('badge-mat-primary');
    expect(component.getEstadoBadgeClass('pendiente_correos')).toBe('badge-mat-rose');
  });

  it('un plazo vencido no cambia la etiqueta de un expediente que sigue justificando en servidor (TS77.56)', () => {
    const pending: Expediente = {
      id: 'pending', numero: 'EXP-2026-123', tipo: 'falta', socio: 'Socio', legajo: '123',
      subcomision: 'Cómputos', motivo: 'Causa', fechaCreacion: '2026-01-01',
      estado: 'justificando', horasRestantes: 0, puntos: -1, plazoLimiteAt: '2026-01-10T12:00:00Z'
    };
    expect(component.getEstadoLabel('justificando', pending)).toBe('Justificando · Plazo vencido');
  });

  it('notifica validaciones de T02/T03 sin enviar un descargo inválido', () => {
    const submit = spyOn(TestBed.inject(TribunalDataService), 'enviarDescargo');
    component.expedienteSeleccionado = { id: 'test' } as Expediente;
    component.tipoDescargo = 'T02_CERTIFICADO';
    component.nombreArchivo = '';
    component.enviarDescargo();
    expect(notifications.error).toHaveBeenCalledWith('Es obligatorio adjuntar el comprobante o constancia digital (PDF, JPG o PNG).');
    component.tipoDescargo = 'T03_EXTRAORDINARIO';
    component.relatoTexto = '';
    component.enviarDescargo();
    expect(notifications.error).toHaveBeenCalledWith('Por favor expone detalladamente los hechos y motivos extraordinarios.');
    expect(submit).not.toHaveBeenCalled();
  });

  describe('Coloreado de Puntos Totales', () => {
    it('retorna clase verde para puntos >= 0', () => {
      expect(component.getColorClasePuntos(10)).toBe('puntos-verde');
      expect(component.getColorClasePuntos(0)).toBe('puntos-verde');
      expect(component.getHeaderClassPuntos(0)).toBe('card-header-success');
    });

    it('retorna clase gris para puntos < 0 y >= -7', () => {
      expect(component.getColorClasePuntos(-1)).toBe('puntos-gris');
      expect(component.getColorClasePuntos(-7)).toBe('puntos-gris');
      expect(component.getHeaderClassPuntos(-5)).toBe('card-header-secondary');
    });

    it('retorna clase amarillo para puntos < -7 y >= -9', () => {
      expect(component.getColorClasePuntos(-7.5)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-8)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-9)).toBe('puntos-amarillo');
      expect(component.getHeaderClassPuntos(-8)).toBe('card-header-warning');
    });

    it('retorna clase rojo para puntos < -9', () => {
      expect(component.getColorClasePuntos(-9.5)).toBe('puntos-rojo');
      expect(component.getColorClasePuntos(-15)).toBe('puntos-rojo');
      expect(component.getHeaderClassPuntos(-10)).toBe('card-header-danger');
    });
  });

  describe('Ordenamiento de tabla', () => {
    const mockExpedientes: Expediente[] = [
      {
        id: '1',
        numero: 'EXP-2026-002',
        tipo: 'falta',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Falta a reunión',
        subcomision: 'Deportes',
        puntos: -2,
        estado: 'creado',
        fechaCreacion: '2026-03-01',
        horasRestantes: 72
      },
      {
        id: '2',
        numero: 'EXP-2026-001',
        tipo: 'merito',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Reconocimiento',
        subcomision: 'Cultura',
        puntos: 5,
        estado: 'emitido',
        fechaCreacion: '2026-02-15',
        horasRestantes: 0
      }
    ];

    beforeEach(() => {
      component.misExpedientes = [...mockExpedientes];
    });

    it('ordena ascendentemente por defecto', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-001');
      expect(ordenados[1].numero).toBe('EXP-2026-002');
    });

    it('invierte orden al hacer click en la misma columna', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      component.cambiarOrden('numero');
      expect(component.ordenAscendente).toBeFalse();
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-002');
      expect(ordenados[1].numero).toBe('EXP-2026-001');
    });

    it('cambia columna y reinicia orden a ascendente', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = false;
      component.cambiarOrden('motivo');
      expect(component.columnaOrden).toBe('motivo');
      expect(component.ordenAscendente).toBeTrue();
    });
  });

  describe('Temporizador Dinámico y Plazo Preclusivo (S3-02 / CA3)', () => {
    const expEnPlazo: Expediente = {
      id: 'EXP-01',
      numero: 'EXP-001/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-08',
      horasRestantes: 48,
      plazoInicioAt: '2026-10-08T18:00:00-03:00',
      plazoLimiteAt: '2026-10-15T18:00:00-03:00',
      descargoPresentado: false
    };

    it('formatea la fecha y hora exacta del vencimiento (getDeadlineLabel)', () => {
      const label = component.getDeadlineLabel(expEnPlazo);
      expect(label).toContain('Vence:');
      expect(label).toContain('15/10/2026');
      expect(label).toContain('18:00 hs');
    });

    it('calcula el countdown dinámico restante cuando está en plazo (getCountdownLabel)', () => {
      // Fijamos ahoraMs a 2 días y 4 horas antes del vencimiento
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const countdown = component.getCountdownLabel(expEnPlazo);
      expect(countdown).toBe('2d 04h 15m restantes');
      expect(component.esPlazoVencido(expEnPlazo)).toBeFalse();
    });

    it('detecta plazo vencido y muestra "Plazo expirado" al superar el límite', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs + 1000; // 1 segundo después

      expect(component.esPlazoVencido(expEnPlazo)).toBeTrue();
      expect(component.getCountdownLabel(expEnPlazo)).toBe('Plazo expirado');
    });

    it('formatea countdown compacto para el badge (getCompactCountdownLabel)', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const compact = component.getCompactCountdownLabel(expEnPlazo);
      expect(compact).toBe('2d 04h');
      expect(component.getEstadoLabel('justificando', expEnPlazo)).toBe('Justificando · 2d 04h');
    });

    it('abre y cierra el modal de detalle del expediente', () => {
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();

      component.abrirModalDetalle(expEnPlazo);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.expedienteDetalle).toBe(expEnPlazo);

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();
    });

    it('limpia el timer subscription en ngOnDestroy para evitar memory leaks', () => {
      component.ngOnDestroy();
      expect((component as any).tickerSub).toBeNull();
    });
  });

  describe('Gestión de Justificativos y Auditoría en Modal Detalle', () => {
    const expConDescargo: Expediente = {
      id: 'EXP-99',
      numero: 'EXP-099/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'revision_resolucion',
      fechaCreacion: '2026-10-01',
      horasRestantes: 0,
      descargoPresentado: true,
      descargo: {
        tipo: 'T02_CERTIFICADO',
        causal: 'Examen Académico Universitario en UTN FRC',
        archivo: 'comprobante.pdf',
        texto: 'Certificado de examen rendido',
        fecha: '2026-10-01'
      },
      logsDescargo: [
        {
          operacion: 'CREACION',
          accionLabel: 'Añadir Justificativo',
          usuario: 'Lucas Gastiaburu (Legajo 74907)',
          timestamp: '01/10/2026 10:00 hs',
          detalle: 'Modalidad T02 (Certificado)'
        }
      ]
    };

    it('abre el modal de añadir justificativo en modo creación', () => {
      const expSinDescargo: Expediente = { ...expConDescargo, descargo: undefined, logsDescargo: [] };
      component.abrirModalDescargo(expSinDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeFalse();
      expect(component.expedienteSeleccionado).toBe(expSinDescargo);
      expect(component.nombreArchivo).toBe('');
    });

    it('abre el modal de editar justificativo precargando los datos existentes', () => {
      component.abrirModalEditarDescargo(expConDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeTrue();
      expect(component.tipoDescargo).toBe('T02_CERTIFICADO');
      expect(component.causalSeleccionada).toBe('Examen Académico Universitario en UTN FRC');
      expect(component.nombreArchivo).toBe('comprobante.pdf');
      expect(component.relatoTexto).toBe('Certificado de examen rendido');
    });

    it('elimina el justificativo al confirmar en el diálogo', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(dataSpy).toHaveBeenCalledWith('EXP-99', jasmine.objectContaining({ nombre: jasmine.any(String) }));
    });

    it('no elimina el justificativo si el usuario cancela la confirmación', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(dataSpy).not.toHaveBeenCalled();
    });

    it('asigna clases badge adecuadas a cada tipo de operación', () => {
      expect(component.getBadgeClaseOperacion('CREACION')).toBe('badge-success');
      expect(component.getBadgeClaseOperacion('EDICION')).toBe('badge-info');
      expect(component.getBadgeClaseOperacion('ELIMINACION')).toBe('badge-danger');
    });
  });

  describe('Bloqueo de scroll al abrir modales', () => {
    const mockExpediente: Expediente = {
      id: 'EXP-101',
      numero: 'EXP-2026-101',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-01',
      horasRestantes: 72
    };

    afterEach(() => {
      document.body.classList.remove('modal-open');
      document.body.style.removeProperty('overflow');
      document.documentElement.style.removeProperty('overflow');
    });

    it('bloquea el scroll del fondo al abrir el modal de detalle y lo restaura al cerrar', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.documentElement.style.overflow).toBe('hidden');

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
      expect(document.documentElement.style.overflow).toBe('');
    });

    it('bloquea el scroll al abrir el modal de justificación T02/T03 y lo restaura al cerrar', () => {
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });

    it('mantiene el bloqueo de scroll activo si el modal de detalle sigue abierto al cerrar el de justificación', () => {
      component.abrirModalDetalle(mockExpediente);
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      // Cerrar solo el de justificación
      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.body.classList.contains('modal-open')).toBeTrue();

      // Cerrar finalmente el de detalle
      component.cerrarModalDetalle();
      expect(document.body.style.overflow).toBe('');
      expect(document.body.classList.contains('modal-open')).toBeFalse();
    });

    it('limpia las clases y estilos de scroll al destruir el componente', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.ngOnDestroy();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });
  });
});

describe('MisExpedientesComponent — saldo propio confirmado (TS77.49)', () => {
  const balanceUrl = `${environment.apiUrl}/socios/me/points-history/`;
  function historyResponse(points: number) {
    return {
      points_balance: points,
      entries: points === 0 ? [] : [{
        movement_id: 17, applied_points: points,
        historical_case: { id: 101, number: 'HIST-101', recorded_at: null, state: 'emitido' as const },
        resolution: { id: 201, text: 'RESOLUCIÓN 201\nVISTO\nCONSIDERANDO\nSE RESUELVE', regulations: ['Art. 93'] },
        managed_case: null
      }]
    };
  }
  const profile: PerfilSocio = {
    legajo: '99077001', first_name: 'Ámbar', last_name: 'Faro Demo',
    email: 'demo@aveit.test', role: 'SOCIO', category: 'EX_TRAVELER',
    category_display: 'Exviajero', subcomision: 'Cómputos'
  };
  let fixture: ComponentFixture<MisExpedientesComponent>;
  let component: MisExpedientesComponent;
  let profiles: BehaviorSubject<PerfilSocio | null>;
  let cases: BehaviorSubject<Expediente[]>;
  let mockBalances: BehaviorSubject<readonly { nombre: string; saldo: number }[]>;
  let http: HttpTestingController;
  let notifications: jasmine.SpyObj<NotificationService>;

  beforeEach(async(() => {
    profiles = new BehaviorSubject<PerfilSocio | null>(null);
    cases = new BehaviorSubject<Expediente[]>([]);
    mockBalances = new BehaviorSubject([{ nombre: 'Ámbar Faro Demo', saldo: 99 }]);
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'registerDialogContainer']);
    notifications.registerDialogContainer.and.returnValue(() => undefined);
    TestBed.configureTestingModule({
      imports: [A11yModule, CommonModule, HttpClientTestingModule, FormsModule, MatDialogModule, MatButtonModule, NoopAnimationsModule],
      declarations: [MisExpedientesComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [
        { provide: AuthService, useValue: { perfil$: profiles.asObservable(), getPerfil: () => profiles.value } },
        { provide: TribunalDataService, useValue: { socios$: mockBalances.asObservable(), expedientes$: cases.asObservable(), getOwnCases: () => cases.asObservable() } },
        { provide: NotificationService, useValue: notifications }
      ]
    }).compileComponents();
  }));

  beforeEach(() => {
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(MisExpedientesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
    http.verify();
  });

  function currentRequest(): TestRequest {
    return http.expectOne(balanceUrl);
  }

  function balanceWidget(): HTMLElement {
    return fixture.nativeElement.querySelector('[data-testid="points-balance"]') as HTMLElement;
  }

  it('saldo y resolución histórica provienen de una sola consulta sin crear una causa operativa (TS77.58)', () => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    fixture.detectChanges();
    const table: HTMLElement = fixture.nativeElement.querySelector('[data-testid="applied-resolutions"]');
    expect(table.textContent).toContain('HIST-101');
    expect(table.textContent).toContain('Emitida');
    expect(table.textContent.replace(/\s+/g, ' ')).toContain('+2 pts');
    expect(component.misExpedientes.length).toBe(0);
    expect(component.saldoNeto).toBe(2);
    http.expectNone(`${environment.apiUrl}/socios/me/points-balance/`);
  });

  it('saldo cero compensado mantiene ambas resoluciones +3/-3 visibles (TS77.58)', () => {
    const positive = historyResponse(3).entries[0];
    const negative = { ...historyResponse(-3).entries[0], movement_id: 18,
      resolution: { id: 202, text: 'Resolución sancionatoria', regulations: ['Art. 93'] } };
    profiles.next(profile);
    currentRequest().flush({ points_balance: 0, entries: [positive, negative] });
    fixture.detectChanges();
    const rows = fixture.nativeElement.querySelectorAll('[data-testid="applied-resolutions"] tbody tr');
    expect(rows.length).toBe(2);
    expect(fixture.nativeElement.textContent).not.toContain('No hay movimientos');
    expect(component.saldoNeto).toBe(0);
  });

  it('un cero confirmado sin movimientos muestra el estado vacío explícito (TS77.58)', () => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(0));
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('No hay movimientos de puntos aplicados.');
    expect(fixture.nativeElement.querySelector('[data-testid="applied-resolutions"]')).toBeNull();
  });

  it('muestra la causa operativa sólo cuando llega el vínculo acreditado (TS77.58)', () => {
    const response = historyResponse(2);
    const entry = { ...response.entries[0], managed_case: { id: 801, number: 'EXP-0012/2026', state: 'emitido' as const } };
    profiles.next(profile);
    currentRequest().flush({ points_balance: 2, entries: [entry] });
    fixture.detectChanges();
    const table: HTMLElement = fixture.nativeElement.querySelector('[data-testid="applied-resolutions"]');
    expect(table.textContent).toContain('EXP-0012/2026');
    expect(table.textContent).toContain('HIST-101');
  });

  it('al cambiar de sesión retira inmediatamente las resoluciones anteriores (TS77.58)', () => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    fixture.detectChanges();
    profiles.next({ ...profile, first_name: 'Otra persona' });
    const request = currentRequest();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('HIST-101');
    expect(fixture.nativeElement.textContent).not.toContain('Resolución #201');
    request.flush(historyResponse(0));
  });

  it('abre el texto formal completo en un diálogo accesible, enfoca Cerrar y restaura el foco con Escape (TS77.58)', fakeAsync(() => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    fixture.detectChanges();
    const trigger: HTMLButtonElement = fixture.nativeElement.querySelector('[data-testid="open-applied-resolution"]');
    trigger.focus();
    trigger.click();
    fixture.detectChanges();
    tick();
    const dialog: HTMLElement = document.querySelector('[role="dialog"]');
    expect(dialog.getAttribute('aria-labelledby')).toBe('applied-resolution-title');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.textContent).toContain('VISTO');
    expect(dialog.textContent).toContain('CONSIDERANDO');
    expect(dialog.textContent).toContain('SE RESUELVE');
    expect(dialog.textContent).toContain('Art. 93');
    expect((document.activeElement as HTMLElement).classList.contains('resolution-close')).toBeTrue();
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', keyCode: 27, bubbles: true }));
    tick();
    expect(document.querySelector('[role="dialog"]')).toBeNull();
    expect(document.activeElement).toBe(trigger);
    fixture.destroy();
    flush();
  }));

  it('cambiar sesión cierra el detalle y borra todo texto de la resolución anterior (TS77.58)', fakeAsync(() => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    fixture.detectChanges();
    (fixture.nativeElement.querySelector('[data-testid="open-applied-resolution"]') as HTMLButtonElement).click();
    fixture.detectChanges();
    tick();
    profiles.next({ ...profile, first_name: 'Otra persona' });
    const request = currentRequest();
    fixture.detectChanges();
    tick();
    expect(document.querySelector('[role="dialog"]')).toBeNull();
    expect(document.body.textContent).not.toContain('RESOLUCIÓN 201');
    request.flush(historyResponse(0));
    fixture.destroy();
    flush();
  }));

  it('sin perfil no consulta ni inventa un saldo cero', () => {
    http.expectNone(balanceUrl);
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).toContain('Iniciá sesión');
    expect(balanceWidget().textContent).not.toMatch(/\b0\s*pts\b/);
  });

  it('muestra carga mientras el servidor confirma el saldo', () => {
    profiles.next(profile);
    const request = currentRequest();
    fixture.detectChanges();
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).toContain('Cargando');
    expect(balanceWidget().getAttribute('aria-busy')).toBe('true');
    request.flush(historyResponse(2));
  });

  it('muestra +2 del servidor aunque el mock tenga 99 y las causas pendientes sumen -6', () => {
    cases.next([-1, -3, -2].map((points, index): Expediente => ({
      id: String(index), numero: `EXP-${index}/2026`, socio: 'Ámbar Faro Demo',
      legajo: '99077001', motivo: 'Causa pendiente', subcomision: 'Cómputos',
      puntos: points, tipo: 'falta', estado: 'creado', fechaCreacion: '2026-10-12', horasRestantes: 0
    })));
    profiles.next(profile);
    const request = currentRequest();
    expect(request.request.method).toBe('GET');
    expect(request.request.params.keys()).toEqual([]);
    request.flush(historyResponse(2));
    mockBalances.next([{ nombre: 'Ámbar Faro Demo', saldo: -99 }]);
    fixture.detectChanges();
    expect(component.saldoNeto).toBe(2);
    expect(component.misExpedientes.reduce((sum, item) => sum + item.puntos, 0)).toBe(-6);
    expect(balanceWidget().textContent.replace(/\s+/g, ' ')).toContain('+2 pts');
    expect(balanceWidget().getAttribute('aria-busy')).toBe('false');
    expect(balanceWidget().classList.contains('puntos-verde')).toBeTrue();
  });

  [-10, 0].forEach(points => {
    it(`presenta el saldo ${points} sólo después de confirmarlo en servidor`, () => {
      profiles.next(profile);
      currentRequest().flush(historyResponse(points));
      fixture.detectChanges();
      expect(component.saldoNeto).toBe(points);
      expect(balanceWidget().textContent.replace(/\s+/g, ' ')).toContain(`${points} pts`);
      expect(balanceWidget().textContent).not.toContain('No disponible');
    });
  });

  [0, 403, 503].forEach(status => {
    it(`distingue el error HTTP ${status} de cero y usa la notificación central`, () => {
      profiles.next(profile);
      const request = currentRequest();
      if (status === 0) {
        request.error(new ProgressEvent('error'));
      } else {
        request.flush({ detail: 'No divulgar detalles internos.' }, { status, statusText: 'Error' });
      }
      fixture.detectChanges();
      expect(component.saldoNeto).toBeNull();
      expect(balanceWidget().textContent).toContain('No disponible');
      expect(balanceWidget().textContent).not.toMatch(/\b0\s*pts\b/);
      expect(notifications.error).toHaveBeenCalledWith('No se pudieron consultar tus puntos y resoluciones. Volvé a intentarlo más tarde.');
    });
  });

  it('una identidad institucional no acreditada mantiene puntos no disponibles sin aviso de autenticación (TS77.61)', () => {
    profiles.next(profile);
    currentRequest().flush({}, { status: 404, statusText: 'Not Found' });
    fixture.detectChanges();
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).toContain('No disponible');
    expect(fixture.nativeElement.textContent).toContain('No hay un vínculo institucional confirmado');
    expect(notifications.error).not.toHaveBeenCalled();
  });

  const invalidResponses: readonly unknown[] = [
    {}, null, { points_balance: null }, { points_balance: '2' },
    { points_balance: Number.NaN }, { points_balance: Number.POSITIVE_INFINITY }
  ];
  invalidResponses.forEach((response, index) => {
    it(`una respuesta HTTP 200 malformada ${index} no confirma el saldo (TS77.51)`, () => {
      profiles.next(profile);
      currentRequest().flush(response);
      fixture.detectChanges();
      expect(component.saldoNeto).toBeNull();
      expect(balanceWidget().textContent).toContain('No disponible');
      expect(balanceWidget().textContent).not.toMatch(/\b0\s*pts\b/);
      expect(notifications.error).toHaveBeenCalledOnceWith('No se pudieron consultar tus puntos y resoluciones. Volvé a intentarlo más tarde.');
    });
  });

  it('cancela la lectura anterior cuando cambia la sesión y no admite su respuesta tardía', () => {
    profiles.next(profile);
    const previous = currentRequest();
    profiles.next({ ...profile, legajo: '99077009', first_name: 'Irina', last_name: 'Isla Demo' });
    const current = currentRequest();
    expect(previous.cancelled).toBeTrue();
    expect(() => previous.flush(historyResponse(2))).toThrowError(/cancelled/);
    expect(component.saldoNeto).toBeNull();
    current.flush(historyResponse(-2));
    fixture.detectChanges();
    expect(component.saldoNeto).toBe(-2);
    expect(balanceWidget().textContent.replace(/\s+/g, ' ')).toContain('-2 pts');
    expect(notifications.error).not.toHaveBeenCalled();
  });

  it('limpia el saldo confirmado antes de leer el de una nueva sesión', () => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    profiles.next({ ...profile, first_name: 'Otra persona' });
    const request = currentRequest();
    fixture.detectChanges();
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).toContain('Cargando');
    expect(balanceWidget().textContent).not.toContain('+2');
    request.flush(historyResponse(0));
  });

  it('al salir cancela la lectura y mantiene el saldo sin confirmar', () => {
    profiles.next(profile);
    const request = currentRequest();
    profiles.next(null);
    fixture.detectChanges();
    expect(request.cancelled).toBeTrue();
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).toContain('Iniciá sesión');
    http.expectNone(balanceUrl);
    expect(notifications.error).not.toHaveBeenCalled();
  });

  it('al salir borra también un saldo ya confirmado', () => {
    profiles.next(profile);
    currentRequest().flush(historyResponse(2));
    profiles.next(null);
    fixture.detectChanges();
    expect(component.saldoNeto).toBeNull();
    expect(balanceWidget().textContent).not.toContain('+2');
  });

  it('la destrucción cancela HTTP y descarta cambios posteriores de perfil', () => {
    profiles.next(profile);
    const request = currentRequest();
    fixture.destroy();
    expect(request.cancelled).toBeTrue();
    profiles.next({ ...profile, first_name: 'Otra persona' });
    http.expectNone(balanceUrl);
    expect(notifications.error).not.toHaveBeenCalled();
  });

  it('una falla no termina la escucha de una sesión posterior', () => {
    profiles.next(profile);
    currentRequest().flush({}, { status: 503, statusText: 'Unavailable' });
    profiles.next({ ...profile, last_name: "D'Angelo" });
    const request = currentRequest();
    request.flush(historyResponse(1));
    fixture.detectChanges();
    expect(component.saldoNeto).toBe(1);
    expect(balanceWidget().textContent.replace(/\s+/g, ' ')).toContain('+1 pts');
  });
});
