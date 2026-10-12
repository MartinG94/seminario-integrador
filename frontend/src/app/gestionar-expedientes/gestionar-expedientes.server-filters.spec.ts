import { A11yModule } from '@angular/cdk/a11y';
import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { BoardCaseDTO, BoardResponseDTO, TribunalDataService } from '../services/tribunal-data.service';
import { GestionarExpedientesComponent } from './gestionar-expedientes.component';

describe('SCRUM-77 filtros del tablero confirmados por servidor', () => {
  let fixture: ComponentFixture<GestionarExpedientesComponent>;
  let http: HttpTestingController;
  let notifications: jasmine.SpyObj<NotificationService>;
  const multiCase: BoardCaseDTO = {
    id: 773, numero: 'EXP-0003/2026', socio: 6, socio_nombre: 'Ámbar Faro Demo',
    socio_legajo: '99077001', subcomision: 'Cómputos', estado: 'creado',
    estado_display: 'Expediente Creado', urgencia: 'urgente', puntos: -3,
    motivo: 'SCRUM-77 [cause.created.urgent.multi]', created_at: '2026-10-12T12:00:00Z',
    plazo_limite_at: null, transiciones_permitidas: [], cantidad_socios: 2
  };
  const primaryCase: BoardCaseDTO = {
    ...multiCase, id: 775, numero: 'EXP-0005/2026', socio: 11,
    socio_nombre: 'Malena Marea Demo', socio_legajo: '99077013',
    motivo: 'SCRUM-77 [t01.authority.issued]', cantidad_socios: 1
  };

  function board(cases: BoardCaseDTO[]): BoardResponseDTO {
    return { columns: [
      { key: 'creado', label: 'Expediente Creado', cases: cases.filter(item => item.estado === 'creado') },
      { key: 'justificando', label: 'En período de justificaciones', cases: cases.filter(item => item.estado === 'justificando') },
      { key: 'revision_resolucion', label: 'En Revisión', cases: cases.filter(item => item.estado === 'revision_resolucion') },
      { key: 'espera_resolucion', label: 'Pendiente de Firma', cases: cases.filter(item => item.estado === 'espera_resolucion') },
      { key: 'pendiente_correos', label: 'Pendiente de correos', cases: cases.filter(item => item.estado === 'pendiente_correos') },
      { key: 'emitido', label: 'Expedientes ya emitidos', cases: cases.filter(item => item.estado === 'emitido') }
    ] };
  }

  const stateDistribution = [
    { state: 'creado', label: 'Creados', count: 4 },
    { state: 'justificando', label: 'Justificando', count: 2 },
    { state: 'revision_resolucion', label: 'En Revisión', count: 3 },
    { state: 'espera_resolucion', label: 'Pendiente de Firma', count: 1 },
    { state: 'pendiente_correos', label: 'Pendiente de Envío', count: 2 },
    { state: 'emitido', label: 'Emitidos', count: 4 }
  ] as const;

  function allStateCases(): BoardCaseDTO[] {
    let id = 800;
    return stateDistribution.flatMap(({ state, label, count }) => Array.from({ length: count }, (): BoardCaseDTO => ({
      ...multiCase, id: id++, estado: state, estado_display: label, numero: `EXP-${id}/2026`,
      motivo: `Caso ${state}`, transiciones_permitidas: []
    })));
  }

  function loadAllStates(): void {
    fixture.componentInstance.cargarDatosTablero();
    http.expectOne('/api/v1/expedientes/board/').flush(board(allStateCases()));
    fixture.detectChanges();
  }

  beforeEach(async () => {
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'registerDialogContainer']);
    notifications.registerDialogContainer.and.returnValue(() => undefined);
    await TestBed.configureTestingModule({
      declarations: [GestionarExpedientesComponent],
      imports: [CommonModule, FormsModule, MatButtonModule, NoopAnimationsModule, A11yModule, HttpClientTestingModule],
      providers: [
        TribunalDataService,
        { provide: NotificationService, useValue: notifications },
        { provide: AuthService, useValue: { perfil$: of(null), tieneRol: () => false } }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(GestionarExpedientesComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne('/api/v1/expedientes/board/').flush(board([multiCase, primaryCase]));
    fixture.detectChanges();
    await fixture.whenStable();
  });

  afterEach(() => http.verify());

  it('el lector conserva todas las claves de estado recibidas del servidor (TS77.56)', () => {
    loadAllStates();
    stateDistribution.forEach(({ state, count }) => {
      expect(fixture.componentInstance.expedientes.filter(item => item.estado === state).length).toBe(count);
    });
    expect(fixture.componentInstance.expedientes.length).toBe(16);
  });

  it('el DOM muestra seis columnas con los mismos conteos 4/2/3/1/2/4 del servidor (TS77.56)', () => {
    loadAllStates();
    const columns: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.kanban-col-mat'));
    expect(columns.length).toBe(6);
    stateDistribution.forEach(({ label, count }, index) => {
      expect(columns[index].getAttribute('aria-label')).toBe(label);
      expect(columns[index].querySelector('.col-count')?.textContent.trim()).toBe(String(count));
      expect(columns[index].querySelectorAll('.kanban-card-mat').length).toBe(count);
    });
    expect(fixture.nativeElement.querySelectorAll('.kanban-card-mat').length).toBe(16);
  });

  stateDistribution.forEach(({ state, label, count }) => {
    it(`filtra ${state} sin fusionar estados ni reclasificar por firmas simuladas (TS77.56)`, () => {
      const component = fixture.componentInstance;
      component.filtroEstado = state;
      component.cargarDatosTablero();
      http.expectOne(request => request.url === '/api/v1/expedientes/board/' && request.params.get('estado') === state)
        .flush(board(allStateCases().filter(item => item.estado === state)));
      fixture.detectChanges();
      expect(component.columnasKanbanVisibles.map(item => item.estado)).toEqual([state]);
      expect(component.expedientesFiltrados.length).toBe(count);
      expect(component.getExpedientesPorEstado(state).length).toBe(count);
      const column: HTMLElement = fixture.nativeElement.querySelector('.kanban-col-mat');
      expect(column.getAttribute('aria-label')).toBe(label);
      expect(column.querySelectorAll('.kanban-card-mat').length).toBe(count);
    });
  });

  it('lista y detalle distinguen revisión, firma y envío con las mismas claves del tablero (TS77.56)', () => {
    loadAllStates();
    const component = fixture.componentInstance;
    component.vistaActual = 'tabla';
    fixture.detectChanges();
    const rows: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('tbody tr'));
    expect(rows.length).toBe(16);
    stateDistribution.forEach(({ state, label, count }) => {
      expect(rows.filter(row => row.querySelector('td:nth-child(7) .badge-mat')?.textContent.trim() === label).length).toBe(count);
      expect(component.getEstadoLabel(state)).toBe(label);
    });
    const waiting = component.expedientes.find(item => item.estado === 'espera_resolucion')!;
    component.abrirDetalle(waiting);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[role="dialog"]')?.textContent).toContain('Pendiente de Firma');
  });

  async function searchByKeyboard(term: string): Promise<void> {
    const input = fixture.nativeElement.querySelector('#filtro-socio') as HTMLInputElement;
    input.value = term;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    fixture.detectChanges();
    await fixture.whenStable();
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', bubbles: true }));
  }

  it('conserva la causa multisocio devuelta al buscar un involucrado secundario', async () => {
    await searchByKeyboard('99077013');
    const request = http.expectOne(req => req.url === '/api/v1/expedientes/board/' && req.params.get('socio') === '99077013');
    request.flush(board([multiCase, primaryCase]));
    fixture.detectChanges();
    expect(fixture.componentInstance.expedientesFiltrados.map(item => item.id)).toEqual(['773', '775']);
    expect(fixture.nativeElement.querySelectorAll('.kanban-card-mat').length).toBe(2);
  });

  it('respeta una búsqueda vacía del servidor sin recuperar la colección anterior', async () => {
    await searchByKeyboard('sin coincidencias');
    http.expectOne(req => req.url === '/api/v1/expedientes/board/' && req.params.get('socio') === 'sin coincidencias')
      .flush(board([]));
    fixture.detectChanges();
    expect(fixture.componentInstance.expedientes).toEqual([]);
    expect(fixture.componentInstance.expedientesFiltrados).toEqual([]);
    expect(fixture.nativeElement.querySelectorAll('.kanban-card-mat').length).toBe(0);
  });

  it('notifica un fallo de búsqueda y recupera los involucrados secundarios al reintentar', async () => {
    await searchByKeyboard('99077013');
    http.expectOne(req => req.url === '/api/v1/expedientes/board/' && req.params.get('socio') === '99077013')
      .flush({ detail: 'Traceback interno' }, { status: 500, statusText: 'Server Error' });
    fixture.detectChanges();

    expect(notifications.error).toHaveBeenCalledOnceWith('No se pudo cargar el tablero. Intentá nuevamente.');
    expect(fixture.nativeElement.textContent).not.toContain('No se pudo cargar el tablero');
    expect(fixture.nativeElement.textContent).not.toContain('Traceback');
    const retry = fixture.nativeElement.querySelector('[aria-label="Reintentar carga del tablero"]') as HTMLButtonElement;
    expect(retry).toBeTruthy();
    retry.click();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[aria-label="Reintentar carga del tablero"]')).toBeNull();

    http.expectOne(req => req.url === '/api/v1/expedientes/board/' && req.params.get('socio') === '99077013')
      .flush(board([multiCase, primaryCase]));
    fixture.detectChanges();
    expect(fixture.componentInstance.expedientesFiltrados.map(item => item.id)).toEqual(['773', '775']);
    expect(fixture.nativeElement.querySelectorAll('.kanban-card-mat').length).toBe(2);
  });
});
