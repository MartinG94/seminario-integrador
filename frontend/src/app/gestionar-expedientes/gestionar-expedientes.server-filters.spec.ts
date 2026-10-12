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
      { key: 'creado', label: 'Expediente Creado', cases },
      { key: 'justificando', label: 'En período de justificaciones', cases: [] },
      { key: 'revision_resolucion', label: 'En Revisión', cases: [] },
      { key: 'pendiente_firma', label: 'Pendiente de Firma', cases: [] },
      { key: 'pendiente_correos', label: 'Pendiente de correos', cases: [] },
      { key: 'emitido', label: 'Expedientes ya emitidos', cases: [] }
    ] };
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
