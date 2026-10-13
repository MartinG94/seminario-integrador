import { A11yModule } from '@angular/cdk/a11y';
import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { BehaviorSubject } from 'rxjs';
import { AuthService, PerfilSocio } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { TribunalDataService } from '../services/tribunal-data.service';
import { AppliedPointsHistoryComponent } from './applied-points-history/applied-points-history.component';
import { AppliedResolutionDialogComponent } from './applied-resolution-dialog/applied-resolution-dialog.component';
import { MisExpedientesComponent } from './mis-expedientes.component';

describe('Mis Expedientes — lectura propia del servidor (TS77.61/63)', () => {
  let fixture: ComponentFixture<MisExpedientesComponent>;
  let http: HttpTestingController;
  let profiles: BehaviorSubject<PerfilSocio | null>;
  let notifications: jasmine.SpyObj<NotificationService>;
  const profile: PerfilSocio = {
    legajo: '99077013', first_name: 'Socio', last_name: "D'Ensayo", email: 'demo@aveit.test',
    role: 'SOCIO', category: 'SENIOR', category_display: 'Senior', subcomision: 'Cómputos'
  };
  const member = {
    local_socio_id: 13, full_name: 'Socio D\'Ensayo', login_identifier: '99077013',
    institutional_number: 770013, academic_number: '99077013'
  };
  const caseResponse = {
    id: 773, numero: 'EXP-0003/2026', title: 'Ingreso fuera del horario acordado',
    motivo: 'El ingreso tardío al laboratorio interrumpió la actividad del equipo.\n\nSe registraron los hechos al finalizar la jornada.',
    socio_nombre: 'Primer involucrado distinto', socio_legajo: '99077001',
    subcomision: 'Cómputos', estado: 'creado', puntos: '-3.00', urgencia: 'urgente',
    urgencia_display: 'Urgente', created_at: '2026-10-12T12:00:00Z',
    plazo_inicio_at: null, plazo_limite_at: null, horas_restantes: 0,
    descargo_presentado: false, descargo_tipo: null, descargo_causal: null,
    descargo_archivo: null, descargo_texto: null, descargo_presentado_at: null,
    creator: { ...member, local_socio_id: 5, full_name: 'Elena Estrella Demo',
      login_identifier: '99077005', institutional_number: 770005, academic_number: '99077005' },
    involved_members: [
      { ...member, local_socio_id: 1, full_name: 'Ámbar Faro Demo', login_identifier: '99077001',
        institutional_number: 770001, academic_number: '99077001' }, member
    ], historial: []
  };

  beforeEach(async () => {
    profiles = new BehaviorSubject<PerfilSocio | null>(null);
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'registerDialogContainer']);
    notifications.registerDialogContainer.and.returnValue(() => undefined);
    await TestBed.configureTestingModule({
      imports: [A11yModule, CommonModule, FormsModule, HttpClientTestingModule, MatDialogModule, MatButtonModule, NoopAnimationsModule],
      declarations: [MisExpedientesComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [TribunalDataService,
        { provide: AuthService, useValue: { perfil$: profiles.asObservable(), getPerfil: () => profiles.value } },
        { provide: NotificationService, useValue: notifications }]
    }).compileComponents();
    http = TestBed.inject(HttpTestingController);
    fixture = TestBed.createComponent(MisExpedientesComponent);
    fixture.detectChanges();
  });

  afterEach(() => { fixture.destroy(); http.verify(); });

  function startOwnRead() {
    profiles.next(profile);
    http.expectOne('/api/v1/socios/me/points-history/').flush({ points_balance: 0, entries: [] });
    return http.expectOne('/api/v1/expedientes/mis-expedientes/');
  }

  it('conserva una causa donde el socio es involucrado secundario, sin filtrar nombres ni visitar el tablero', () => {
    startOwnRead().flush([caseResponse]);
    fixture.detectChanges();
    expect(fixture.componentInstance.misExpedientes.map(item => item.id)).toEqual(['773']);
    expect(fixture.componentInstance.misExpedientes[0].puntos).toBe(-3);
    expect(fixture.nativeElement.textContent).toContain('EXP-0003/2026');
  });

  it('una respuesta propia vacía no recupera casos simulados de la colección global', () => {
    startOwnRead().flush([]);
    fixture.detectChanges();
    expect(fixture.componentInstance.misExpedientes).toEqual([]);
    expect(fixture.nativeElement.textContent).not.toContain('EXP-001/2026');
    http.expectNone('/api/v1/expedientes/board/');
  });

  it('cancelar sesión descarta la lectura pendiente y los detalles propios anteriores', () => {
    const request = startOwnRead();
    profiles.next(null);
    fixture.detectChanges();
    expect(request.cancelled).toBeTrue();
    expect(fixture.componentInstance.misExpedientes).toEqual([]);
    expect(fixture.componentInstance.modalDetalleAbierto).toBeFalse();
  });

  it('detalle presenta creador confirmado, título, motivo completo y todos los involucrados por separado', () => {
    startOwnRead().flush([caseResponse]);
    fixture.componentInstance.abrirModalDetalle(fixture.componentInstance.misExpedientes[0]);
    fixture.detectChanges();
    const dialog: HTMLElement = fixture.nativeElement.querySelector('[data-testid="own-case-detail"]');
    expect(dialog.querySelector('[data-testid="case-creator"]')?.textContent).toContain('Elena Estrella Demo');
    expect(dialog.querySelector('[data-testid="case-creator"]')?.textContent).not.toContain('Primer involucrado');
    expect(dialog.textContent).toContain(caseResponse.title);
    expect(dialog.textContent).toContain(caseResponse.motivo);
    expect(getComputedStyle(dialog.querySelector('.case-reason')!).whiteSpace).toBe('pre-wrap');
    expect(dialog.querySelector('[data-testid="case-involved-members"]')?.textContent).toContain('Ámbar Faro Demo');
    expect(dialog.querySelector('[data-testid="case-involved-members"]')?.textContent).toContain("Socio D'Ensayo");
    expect(dialog.querySelector('[data-testid="case-involved-members"]')?.textContent).toContain('770013');
  });

  function openDefense(edit = false): void {
    startOwnRead().flush([{ ...caseResponse, estado: 'justificando',
      plazo_limite_at: '2099-10-12T12:00:00Z', descargo_presentado: edit,
      descargo_tipo: edit ? 'T03_EXTRAORDINARIO' : null,
      descargo_texto: edit ? 'Texto anterior' : null,
      descargo_presentado_at: edit ? '2026-10-12T12:00:00Z' : null }]);
    const component = fixture.componentInstance;
    if (edit) component.abrirModalEditarDescargo(component.misExpedientes[0]);
    else component.abrirModalDescargo(component.misExpedientes[0]);
    component.tipoDescargo = 'T03_EXTRAORDINARIO';
    component.relatoTexto = 'Una emergencia familiar impidió mi participación.';
  }

  [201, 200].forEach(status => {
    it(`persiste ${status === 201 ? 'presentación' : 'corrección'} mediante POST ${status} y refresca la lista confirmada`, () => {
      openDefense(status === 200);
      fixture.componentInstance.enviarDescargo();
      const request = http.expectOne('/api/v1/expedientes/773/descargo/');
      expect(request.request.method).toBe('POST');
      expect(request.request.body).toEqual({ tipo: 'T03_EXTRAORDINARIO', texto: 'Una emergencia familiar impidió mi participación.' });
      request.flush({ detail: 'Descargo registrado.', expediente_id: 773,
        descargo_presentado_at: '2026-10-12T12:00:00Z' }, { status, statusText: 'OK' });
      http.expectOne('/api/v1/expedientes/mis-expedientes/').flush([{ ...caseResponse, estado: 'justificando' }]);
      expect(fixture.componentInstance.modalAbierto).toBeFalse();
      expect(fixture.componentInstance.misExpedientes[0].estado).toBe('justificando');
      expect(notifications.success).toHaveBeenCalled();
      expect(fixture.componentInstance.saldoNeto).toBe(0);
    });
  });

  [403, 409].forEach(status => {
    it(`conserva el descargo para corregir al recibir ${status}, sin éxito simulado`, () => {
      openDefense();
      fixture.componentInstance.enviarDescargo();
      http.expectOne('/api/v1/expedientes/773/descargo/').flush({ detail: 'No se puede presentar este descargo.' }, { status, statusText: 'Conflict' });
      expect(fixture.componentInstance.modalAbierto).toBeTrue();
      expect(fixture.componentInstance.relatoTexto).toContain('emergencia familiar');
      expect(notifications.error).toHaveBeenCalledWith('No se puede presentar este descargo.');
      expect(notifications.success).not.toHaveBeenCalled();
      http.expectNone('/api/v1/expedientes/mis-expedientes/');
    });
  });

  it('cancelar sesión cancela el POST pendiente y borra el formulario anterior', () => {
    openDefense();
    fixture.componentInstance.enviarDescargo();
    const request = http.expectOne('/api/v1/expedientes/773/descargo/');
    profiles.next(null);
    expect(request.cancelled).toBeTrue();
    expect(fixture.componentInstance.modalAbierto).toBeFalse();
    expect(fixture.componentInstance.relatoTexto).toBe('');
    expect(notifications.success).not.toHaveBeenCalled();
  });

  it('expone modales accesibles, cierra con Escape y mantiene los avisos en el descargo activo', fakeAsync(() => {
    openDefense();
    fixture.detectChanges();
    tick();
    const dialog: HTMLElement = fixture.nativeElement.querySelector('[aria-labelledby="own-defense-title"]');
    expect(dialog?.getAttribute('role')).toBe('dialog');
    expect(dialog?.getAttribute('aria-modal')).toBe('true');
    expect(notifications.registerDialogContainer).toHaveBeenCalledWith(dialog);
    dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    expect(fixture.componentInstance.modalAbierto).toBeFalse();
    fixture.destroy();
    flush();
  }));

  it('T02 envía solamente la referencia del comprobante y bloquea un segundo envío pendiente', () => {
    openDefense();
    const component = fixture.componentInstance;
    component.tipoDescargo = 'T02_CERTIFICADO';
    component.nombreArchivo = 'constancia.pdf';
    component.enviarDescargo();
    component.enviarDescargo();
    const request = http.expectOne('/api/v1/expedientes/773/descargo/');
    expect(request.request.body).toEqual({ tipo: 'T02_CERTIFICADO',
      causal: 'Examen Académico Universitario en UTN FRC', archivo: 'constancia.pdf',
      texto: 'Una emergencia familiar impidió mi participación.' });
    expect(request.request.body instanceof FormData).toBeFalse();
    fixture.destroy();
    expect(request.cancelled).toBeTrue();
  });

  it('muestra los expedientes propios aunque no exista vínculo institucional para puntos', () => {
    profiles.next(profile);
    http.expectOne('/api/v1/socios/me/points-history/').flush({ detail: 'Sin vínculo institucional.' }, { status: 404, statusText: 'Not Found' });
    http.expectOne('/api/v1/expedientes/mis-expedientes/').flush([caseResponse]);
    fixture.detectChanges();
    expect(fixture.componentInstance.misExpedientes.length).toBe(1);
    expect(fixture.componentInstance.saldoNeto).toBeNull();
    expect(fixture.componentInstance.pointsBalanceStatus).toBe('unavailable');
    expect(notifications.error).not.toHaveBeenCalled();
  });

  it('recupera la lectura propia por API al reintentar sin consultar datos simulados', () => {
    startOwnRead().flush({}, { status: 503, statusText: 'Unavailable' });
    expect(fixture.componentInstance.ownCasesStatus).toBe('error');
    fixture.componentInstance.reloadOwnCases();
    http.expectOne('/api/v1/expedientes/mis-expedientes/').flush([caseResponse]);
    expect(fixture.componentInstance.ownCasesStatus).toBe('ready');
    expect(fixture.componentInstance.misExpedientes[0].id).toBe('773');
  });

  it('permite corregir un descargo propio del servidor y no ofrece eliminación simulada', () => {
    openDefense(true);
    const component = fixture.componentInstance;
    component.cerrarModal();
    component.abrirModalDetalle(component.misExpedientes[0]);
    fixture.detectChanges();
    const dialog: HTMLElement = fixture.nativeElement.querySelector('[data-testid="own-case-detail"]');
    expect(dialog.textContent).toContain('Editar Justificativo');
    expect(dialog.textContent).not.toContain('Eliminar Justificativo');
  });

  it('conserva el historial de auditoría recibido del servidor sin inferir operaciones', () => {
    startOwnRead().flush([{ ...caseResponse, historial: [{ estado_anterior: 'creado', estado_nuevo: 'justificando',
      actor: '770005', fecha_hora: '2026-10-12T12:10:00Z', motivo: 'Notificación registrada.' }] }]);
    fixture.componentInstance.abrirModalDetalle(fixture.componentInstance.misExpedientes[0]);
    fixture.detectChanges();
    const dialog: HTMLElement = fixture.nativeElement.querySelector('[data-testid="own-case-detail"]');
    expect(dialog.textContent).toContain('Notificación registrada.');
    expect(dialog.textContent).toContain('770005');
    expect(dialog.textContent).not.toContain('Sin operaciones registradas');
  });

  it('no afirma auditoría vacía cuando la respuesta no trae historial', () => {
    const { historial, ...withoutHistory } = caseResponse;
    startOwnRead().flush([withoutHistory]);
    fixture.componentInstance.abrirModalDetalle(fixture.componentInstance.misExpedientes[0]);
    fixture.detectChanges();
    const dialog: HTMLElement = fixture.nativeElement.querySelector('[data-testid="own-case-detail"]');
    expect(dialog.textContent).toContain('Historial no disponible.');
    expect(dialog.textContent).not.toContain('Sin operaciones registradas');
  });

  it('el listado muestra Título y conserva el relato completo para el detalle', () => {
    startOwnRead().flush([caseResponse]);
    fixture.detectChanges();
    const table: HTMLTableElement = fixture.nativeElement.querySelector('.table-mat');
    expect(table.querySelector('thead')?.textContent).toContain('Título');
    expect(table.querySelector('tbody')?.textContent).toContain(caseResponse.title);
    expect(table.querySelector('tbody')?.textContent).not.toContain(caseResponse.motivo);
  });

  it('ordena por el título visible, usando motivo cuando falta título', () => {
    startOwnRead().flush([
      { ...caseResponse, id: 773, title: 'Zeta', motivo: 'Alfa relato' },
      { ...caseResponse, id: 774, title: '', motivo: 'Beta sin título' },
      { ...caseResponse, id: 775, title: 'Alfa', motivo: 'Zeta relato' }
    ]);
    fixture.detectChanges();
    const header: HTMLElement | undefined = Array.from(fixture.nativeElement.querySelectorAll('th') as NodeListOf<HTMLElement>)
      .find(item => item.textContent?.includes('Título'));
    expect(header).toBeTruthy();
    header?.click();
    fixture.detectChanges();
    expect(fixture.componentInstance.expedientesOrdenados.map(item => item.id)).toEqual(['775', '774', '773']);
    expect(fixture.nativeElement.querySelector('.table-mat tbody')?.textContent).toContain('Beta sin título');
    header?.click();
    expect(fixture.componentInstance.expedientesOrdenados.map(item => item.id)).toEqual(['773', '774', '775']);
  });

  it('la acción de presentación se llama Descargo conforme al PO', () => {
    openDefense();
    const component = fixture.componentInstance;
    component.cerrarModal();
    component.abrirModalDetalle(component.misExpedientes[0]);
    fixture.detectChanges();
    const button: HTMLButtonElement = fixture.nativeElement.querySelector('[data-testid="own-case-detail"] .card-footer .btn-primary');
    expect(button?.textContent?.replace('add_circle', '').trim()).toBe('Descargo');
  });
});
