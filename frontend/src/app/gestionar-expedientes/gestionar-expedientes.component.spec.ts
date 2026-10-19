import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { MatButtonModule } from '@angular/material/button';
import { of, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

import { GestionarExpedientesComponent } from './gestionar-expedientes.component';
import { AuthService } from '../services/auth.service';
import { TribunalDataService, BoardResponseDTO, Expediente } from '../services/tribunal-data.service';

describe('GestionarExpedientesComponent', () => {
  let component: GestionarExpedientesComponent;
  let fixture: ComponentFixture<GestionarExpedientesComponent>;
  let authService: AuthService;
  let dataService: TribunalDataService;
  let httpMock: HttpTestingController;
  let notifications: jasmine.SpyObj<NotificationService>;

  const mockBoardResponse: BoardResponseDTO = {
    columns: [
      { key: 'creado', label: 'Expediente Creado', cases: [] },
      { key: 'justificando', label: 'En período de justificaciones', cases: [] },
      { key: 'revision_resolucion', label: 'Justificaciones en revisión', cases: [] },
      { key: 'espera_resolucion', label: 'Espera de resolución', cases: [] },
      { key: 'pendiente_correos', label: 'Pendiente de correos', cases: [] },
      { key: 'emitido', label: 'Expedientes ya emitidos', cases: [] }
    ]
  };

  beforeEach(async () => {
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success']);
    await TestBed.configureTestingModule({
      imports: [
        CommonModule,
        HttpClientTestingModule,
        FormsModule,
        RouterTestingModule,
        MatButtonModule
      ],
      declarations: [GestionarExpedientesComponent],
      providers: [
        { provide: NotificationService, useValue: notifications },
        TribunalDataService,
        AuthService
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(GestionarExpedientesComponent);
    component = fixture.componentInstance;
    authService = TestBed.inject(AuthService);
    dataService = TestBed.inject(TribunalDataService);
    httpMock = TestBed.inject(HttpTestingController);

    // Mockear la respuesta inicial del tablero
    spyOn(dataService, 'obtenerTablero').and.returnValue(of(mockBoardResponse));

    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe configurar las seis columnas canónicas del ciclo de vida ordenadas correctamente', () => {
    expect(component.columnasKanban.length).toBe(6);
    const estados = component.columnasKanban.map(c => c.estado);
    expect(estados).toEqual([
      'creado',
      'justificando',
      'revision_resolucion',
      'pendiente_firma',
      'pendiente_correos',
      'emitido'
    ]);
  });

  it('debe permitir colapsar y expandir columnas en el tablero Kanban', () => {
    expect(component.isColumnaColapsada('emitido')).toBeFalse();
    component.toggleColapsar('emitido');
    expect(component.isColumnaColapsada('emitido')).toBeTrue();
    component.toggleColapsar('emitido');
    expect(component.isColumnaColapsada('emitido')).toBeFalse();
  });

  it('columnasKanbanVisibles debe mostrar únicamente la columna filtrada si filtroEstado está activo', () => {
    component.filtroEstado = 'justificando';
    expect(component.columnasKanbanVisibles.length).toBe(1);
    expect(component.columnasKanbanVisibles[0].estado).toBe('justificando');
  });

  it('puedeVotarOFirmar debe ser true para miembros del Tribunal (TD) o ADMIN', () => {
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('TD'));
    expect(component.puedeVotarOFirmar).toBeTrue();
  });

  it('puedeVotarOFirmar debe ser false para CD u otros roles que solo tienen permisos de supervisión', () => {
    spyOn(authService, 'tieneRol').and.callFake((...roles) => !roles.includes('TD') && !roles.includes('ADMIN'));
    expect(component.puedeVotarOFirmar).toBeFalse();
  });

  it('cargarDatosTablero debe llamar a obtenerTablero con los filtros ingresados (CA2)', () => {
    component.filtroSocio = '74907';
    component.filtroEstado = 'creado';
    component.filtroFechaDesde = '2026-01-01';
    component.filtroFechaHasta = '2026-03-31';

    component.cargarDatosTablero();

    expect(dataService.obtenerTablero).toHaveBeenCalledWith({
      socio: '74907',
      estado: 'creado',
      fecha_desde: '2026-01-01',
      fecha_hasta: '2026-03-31'
    });
  });

  it('transicionarEstado debe invocar transicionarExpediente del servicio (CA3 y CA4)', () => {
    const expMock = {
      id: '1',
      numero: 'EXP-001',
      socio: 'Lucas G',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Falta',
      fechaCreacion: '2026-03-01',
      estado: 'creado' as const,
      horasRestantes: 0,
      tipo: 'falta' as const,
      puntos: -1,
      transicionesPermitidas: ['justificando' as const]
    };

    spyOn(dataService, 'transicionarExpediente').and.returnValue(of({ detail: 'Ok' }));
    spyOn(component, 'cargarDatosTablero');

    component.transicionarEstado(expMock, 'justificando');

    expect(dataService.transicionarExpediente).toHaveBeenCalledWith('1', 'justificando');
    expect(component.cargarDatosTablero).toHaveBeenCalled();
  });

  it('onTableKeyDown debe navegar entre filas con ArrowDown y ArrowUp sin hacer scroll', () => {
    const expMock = {
      id: '1',
      numero: 'EXP-001',
      socio: 'Lucas G',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Falta',
      fechaCreacion: '2026-03-01',
      estado: 'creado' as const,
      horasRestantes: 0,
      tipo: 'falta' as const,
      puntos: -1
    };

    const dummyNextTr = document.createElement('tr');
    spyOn(dummyNextTr, 'focus');

    const dummyCurrentTr = document.createElement('tr');
    const parentTable = document.createElement('table');
    const tbody = document.createElement('tbody');
    tbody.appendChild(dummyCurrentTr);
    tbody.appendChild(dummyNextTr);
    parentTable.appendChild(tbody);

    const eventDown = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    spyOn(eventDown, 'preventDefault');

    // Simular event target
    Object.defineProperty(eventDown, 'target', { value: dummyCurrentTr });

    component.onTableKeyDown(eventDown, expMock);

    expect(eventDown.preventDefault).toHaveBeenCalled();
    expect(dummyNextTr.focus).toHaveBeenCalled();
  });

  it('onKanbanCardKeyDown debe navegar con ArrowDown y ArrowRight en el tablero kanban', () => {
    const expMock = {
      id: '1',
      numero: 'EXP-001',
      socio: 'Lucas G',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Falta',
      fechaCreacion: '2026-03-01',
      estado: 'creado' as const,
      horasRestantes: 0,
      tipo: 'falta' as const,
      puntos: -1
    };

    const col1 = document.createElement('div');
    col1.className = 'kanban-col-mat';
    const card1 = document.createElement('div');
    card1.className = 'kanban-card-mat';
    const card2 = document.createElement('div');
    card2.className = 'kanban-card-mat';
    col1.appendChild(card1);
    col1.appendChild(card2);
    spyOn(card2, 'focus');

    const eventDown = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    spyOn(eventDown, 'preventDefault');
    Object.defineProperty(eventDown, 'target', { value: card1 });

    component.onKanbanCardKeyDown(eventDown, expMock);

    expect(eventDown.preventDefault).toHaveBeenCalled();
    expect(card2.focus).toHaveBeenCalled();
  });

  describe('Tarjetas Kanban simplificadas (observaciones PO PR #50)', () => {
    function renderCase(overrides: Partial<Expediente> = {}): Expediente {
      const expediente: Expediente = {
        id: 'case-1', numero: 'EXP-0007/2026', socio: 'Socio secundario',
        legajo: '74907', subcomision: 'Subcomisión secundaria',
        motivo: 'Inasistencia a reunión institucional', fechaCreacion: '2026-10-07',
        estado: 'creado', horasRestantes: 24, tipo: 'falta', puntos: -1,
        urgencia: 'urgente', cantidadSocios: 3,
        firmas: { juecesFirmantes: ['Juez 1', 'Juez 2', 'Juez 3'] },
        ...overrides
      };
      component.expedientes = [expediente];
      fixture.detectChanges();
      return expediente;
    }

    it('muestra únicamente ID, urgencia, puntos, motivo y fecha en las seis etapas', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      for (const column of component.columnasKanban) {
        renderCase({ estado: column.estado });
        const cards: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.kanban-card-mat'));
        expect(cards.length).toBe(1);
        const card = cards[0];
        expect(card.innerText.replace(/\s+/g, ' ').trim()).toBe(
          '007/2026 Urgente -1 pts Inasistencia a reunión institucional 07/10/2026'
        );
        expect(card.querySelector('button, .card-subcomm, .timer-badge')).toBeNull();
      }
    });

    it('conserva el número canónico y mantiene ID y puntos sin quiebres', () => {
      const expediente = renderCase({ numero: 'EXP-1234/2026', puntos: 2, urgencia: 'baja' });
      const id: HTMLElement | null = fixture.nativeElement.querySelector('.card-id');
      const points: HTMLElement | null = fixture.nativeElement.querySelector('.card-points');
      expect(id?.textContent?.trim()).toBe('1234/2026');
      expect(points?.textContent?.trim()).toBe('+2 pts');
      if (id && points) {
        expect(getComputedStyle(id).whiteSpace).toBe('nowrap');
        expect(getComputedStyle(points).whiteSpace).toBe('nowrap');
      }
      expect(expediente.numero).toBe('EXP-1234/2026');
    });

    it('mantiene el signo de puntos fraccionarios y Normal para registros anteriores', () => {
      renderCase({ numero: '018/2026', puntos: -0.5, urgencia: undefined });
      const card: HTMLElement = fixture.nativeElement.querySelector('.kanban-card-mat');
      expect(card.innerText.replace(/\s+/g, ' ').trim()).toBe(
        '018/2026 Normal -0.5 pts Inasistencia a reunión institucional 07/10/2026'
      );
    });

    it('mantiene legible el máximo de puntos sin desbordar ni superponer los datos de cabecera', () => {
      fixture.nativeElement.style.width = '375px';
      renderCase({ numero: 'EXP-1234/2026', puntos: 99999999.99 });
      const card: HTMLElement = fixture.nativeElement.querySelector('.kanban-card-mat');
      const header: HTMLElement = card.querySelector('.card-top')!;
      expect(card.scrollWidth).toBeLessThanOrEqual(card.clientWidth);
      expect(header.scrollWidth).toBeLessThanOrEqual(header.clientWidth);
      expect(card.querySelector('.card-points')?.textContent?.trim()).toBe('+99999999.99 pts');
      const bounds = Array.from(header.children).map(element => element.getBoundingClientRect());
      for (let index = 0; index < bounds.length; index++) {
        for (const other of bounds.slice(index + 1)) {
          const current = bounds[index];
          const overlap = Math.min(current.right, other.right) > Math.max(current.left, other.left) &&
            Math.min(current.bottom, other.bottom) > Math.max(current.top, other.top);
          expect(overlap).toBeFalse();
        }
      }
    });

    it('permite abrir el detalle mediante clic, Enter y espacio', () => {
      const expediente = renderCase();
      const card: HTMLElement = fixture.nativeElement.querySelector('.kanban-card-mat');
      spyOn(component, 'abrirDetalle');
      expect(card.tabIndex).toBe(0);
      card.click();
      card.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
      card.dispatchEvent(new KeyboardEvent('keydown', { key: ' ', bubbles: true }));
      expect(component.abrirDetalle).toHaveBeenCalledTimes(3);
      expect(component.abrirDetalle).toHaveBeenCalledWith(expediente);
    });
  });

  describe('Clasificador e indicador visual de urgencia (SCRUM-78)', () => {
    it('notifica un fallo de urgencia como error y conserva su valor anterior', () => {
      component.expedienteSeleccionado = { id: '1', urgencia: 'normal' } as Expediente;
      spyOn(dataService, 'actualizarUrgencia').and.returnValue(
        throwError(() => ({ status: 500, error: { detail: 'Traceback database' } })));
      component.cambiarUrgenciaExpediente('urgente');
      expect(notifications.error).toHaveBeenCalledOnceWith('No se pudo actualizar la urgencia.');
      expect(notifications.success).not.toHaveBeenCalled();
      expect(component.expedienteSeleccionado.urgencia).toBe('normal');
    });

    it('notifica fallos de transición sin insertarlos como mensajes de éxito', () => {
      spyOn(dataService, 'transicionarExpediente').and.returnValue(
        throwError(() => ({ status: 400, error: { to_status: ['Transición no permitida.'] } })));
      component.transicionarEstado({ id: '1', numero: '001/2026' } as Expediente, 'justificando');
      fixture.detectChanges();
      expect(notifications.error).toHaveBeenCalledOnceWith('Transición no permitida.');
      expect(notifications.success).not.toHaveBeenCalled();
      expect(fixture.nativeElement.textContent).not.toContain('Transición no permitida.');
    });

    it('notifica un fallo de tablero y ofrece reintentar su carga', () => {
      (dataService.obtenerTablero as jasmine.Spy).and.returnValue(throwError(() => ({ status: 500 })));
      component.cargarDatosTablero();
      fixture.detectChanges();
      expect(notifications.error).toHaveBeenCalledWith('No se pudo cargar el tablero. Intentá nuevamente.');
      const retry = fixture.nativeElement.querySelector('[aria-label="Reintentar carga del tablero"]') as HTMLButtonElement;
      expect(retry).toBeTruthy();
      (dataService.obtenerTablero as jasmine.Spy).and.returnValue(of(mockBoardResponse));
      retry.click();
      fixture.detectChanges();
      expect(fixture.nativeElement.querySelector('[aria-label="Reintentar carga del tablero"]')).toBeNull();
    });
    it('debe mapear correctamente etiquetas, clases e iconos de urgencia', () => {
      expect(component.getUrgenciaLabel('baja')).toBe('Baja');
      expect(component.getUrgenciaLabel('normal')).toBe('Normal');
      expect(component.getUrgenciaLabel('urgente')).toBe('Urgente');
      expect(component.getUrgenciaLabel(undefined)).toBe('Normal');

      expect(component.getUrgenciaBadgeClass('urgente')).toBe('badge-mat-danger');

      expect(component.getUrgenciaBadgeClass('normal')).toBe('badge-mat-info');
      expect(component.getUrgenciaBadgeClass('baja')).toBe('badge-mat-success');

      expect(component.getUrgenciaIcon('urgente')).toBe('priority_high');
      expect(component.getUrgenciaIcon('normal')).toBe('horizontal_rule');
      expect(component.getUrgenciaIcon('baja')).toBe('arrow_downward');
    });

    it('cargarDatosTablero debe incluir el filtro de urgencia si está seleccionado', () => {
      component.filtroUrgencia = 'urgente';
      component.cargarDatosTablero();

      expect(dataService.obtenerTablero).toHaveBeenCalledWith(jasmine.objectContaining({
        urgencia: 'urgente'
      }));
    });

    it('cambiarUrgenciaExpediente debe actualizar la urgencia vía TribunalDataService', () => {
      const expMock: any = {
        id: '1',
        numero: 'EXP-001',
        socio: 'Lucas G',
        legajo: '74907',
        subcomision: 'Cómputos',
        motivo: 'Falta',
        fechaCreacion: '2026-03-01',
        estado: 'creado',
        horasRestantes: 0,
        tipo: 'falta',
        puntos: -1,
        urgencia: 'normal'
      };

      spyOn(dataService, 'actualizarUrgencia').and.returnValue(of({ id: 1, urgencia: 'urgente', urgencia_display: 'Urgente' } as any));

      component.expedienteSeleccionado = expMock;
      component.cambiarUrgenciaExpediente('urgente');

      expect(dataService.actualizarUrgencia).toHaveBeenCalledWith('1', 'urgente');
      expect(expMock.urgencia).toBe('urgente');
      expect(notifications.success).toHaveBeenCalledWith('Urgencia actualizada a "Urgente" exitosamente.');
    });
  });

  describe('S3-10: Formato canónico del Tribunal en el detalle del expediente', () => {
    const mockExpedienteS310: Expediente = {
      id: '419',
      numero: 'EXP-419/2025',
      titulo: 'Inasistencia no informada a asamblea general ordinaria',
      solicitante: 'Comisión Directiva',
      creador: 'Comisión Directiva',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia injustificada a la asamblea convocada con carácter obligatorio.\nSe adjuntan registros de firmas y libro de actas.',
      fechaCreacion: '2025-11-20',
      estado: 'justificando',
      horasRestantes: 72,
      tipo: 'falta',
      puntos: -1.0,
      reglamentoAsociado: 'Reglamento Procesal Disciplinario 2026 (Art. 12)',
      reglamentosRespaldantes: [
        'Estatuto Social AVEIT (Reforma 2026)',
        'Reglamento Procesal Disciplinario 2026',
        'Reglamento Interno de Disciplina'
      ],
      responsablesTribunal: [
        { identificador: 'Responsable 1', legajo: '11239', nombre: 'Giuliano Toselli', grupo: 'G57' },
        { identificador: 'Responsable 2', legajo: '11737', nombre: 'Catalina Cerda Gallego', grupo: 'G58' },
        { identificador: 'Responsable 3', legajo: '11735', nombre: 'Candela Moreno Migliore', grupo: 'G59' }
      ],
      sociosInvolucrados: [
        { legajo: '74907', nombre: 'Lucas', apellido: 'Gastiaburu', grupo: 'G58', estado_justificacion: 'En plazo' }
      ]
    };

    it('getResponsablesTribunal debe retornar los 3 responsables canónicos del TD', () => {
      const responsables = component.getResponsablesTribunal(mockExpedienteS310);
      expect(responsables.length).toBe(3);
      expect(responsables[0]).toEqual({
        identificador: 'Responsable 1',
        legajo: '11239',
        nombre: 'Giuliano Toselli',
        grupo: 'G57'
      });
      expect(responsables[1].identificador).toBe('Responsable 2');
      expect(responsables[2].identificador).toBe('Responsable 3');
    });

    it('getResponsablesTribunal debe retornar el fallback canónico si el expediente no los tiene explícitos', () => {
      const expSinResp: any = { ...mockExpedienteS310, responsablesTribunal: undefined, responsables: undefined };
      const responsables = component.getResponsablesTribunal(expSinResp);
      expect(responsables.length).toBe(3);
      expect(responsables[0].nombre).toBe('Giuliano Toselli');
    });

    it('getReglamentosRespaldantes debe retornar los reglamentos oficiales con denominación completa', () => {
      const reglamentos = component.getReglamentosRespaldantes(mockExpedienteS310);
      expect(reglamentos).toContain('Estatuto Social AVEIT (Reforma 2026)');
      expect(reglamentos).toContain('Reglamento Procesal Disciplinario 2026');
      expect(reglamentos).toContain('Reglamento Interno de Disciplina');
    });

    it('getInvolucrados debe devolver los socios involucrados y su estado de justificación', () => {
      const involucrados = component.getInvolucrados(mockExpedienteS310);
      expect(involucrados.length).toBe(1);
      expect(involucrados[0].legajo).toBe('74907');
      expect(involucrados[0].nombre).toBe('Lucas');
      expect(involucrados[0].apellido).toBe('Gastiaburu');
      expect(involucrados[0].grupo).toBe('G58');
      expect(involucrados[0].estado_justificacion).toBe('En plazo');
    });

    it('formatSancionSolicitada debe formatear puntos con signo y unidad', () => {
      expect(component.formatSancionSolicitada(-1.5)).toBe('-1.5 pts');
      expect(component.formatSancionSolicitada(2.0)).toBe('+2 pts');
      expect(component.formatSancionSolicitada(0)).toBe('0 pts');
    });

    it('formatFechaSolicitud debe formatear fechas ISO en DD/MM/YYYY', () => {
      expect(component.formatFechaSolicitud('2026-03-01')).toBe('01/03/2026');
      expect(component.formatFechaSolicitud('2025-11-20T14:30:00Z')).toBe('20/11/2025');
    });

    it('getEstadoJustificacionBadgeClass debe devolver la clase correcta según el estado', () => {
      expect(component.getEstadoJustificacionBadgeClass('Justificado')).toBe('badge-mat-success');
      expect(component.getEstadoJustificacionBadgeClass('En plazo')).toBe('badge-mat-warning');
      expect(component.getEstadoJustificacionBadgeClass('No justificado')).toBe('badge-mat-danger');
    });

    it('debe renderizar en el DOM las 4 secciones canónicas al abrir el modal de detalle', () => {
      component.abrirDetalle(mockExpedienteS310);
      fixture.detectChanges();

      const modalElement = fixture.nativeElement.querySelector('.modal-dialog-tribunal');
      expect(modalElement).toBeTruthy();

      // Sección 1: Cabecera
      const headerTitle = modalElement.querySelector('.card-header h4');
      expect(headerTitle.textContent).toContain('Expediente 419/2025');
      const descripcion = modalElement.querySelector('.descripcion-causa');
      expect(descripcion.textContent).toContain('Inasistencia injustificada');

      // Sección 2: Responsables
      const cardsResponsables = modalElement.querySelectorAll('.card-responsable');
      expect(cardsResponsables.length).toBe(3);
      expect(cardsResponsables[0].textContent).toContain('Responsable 1');
      expect(cardsResponsables[0].textContent).toContain('Giuliano Toselli');
      expect(cardsResponsables[0].textContent).toContain('G57');

      // Sección 3: Reglamentos
      const itemsReglamentos = modalElement.querySelectorAll('.reglamento-item');
      expect(itemsReglamentos.length).toBe(3);
      expect(itemsReglamentos[0].textContent).toContain('Estatuto Social AVEIT');

      // Sección 4: Involucrados
      const tablaInvolucrados = modalElement.querySelector('.table-involucrados');
      expect(tablaInvolucrados).toBeTruthy();
      const ths = tablaInvolucrados.querySelectorAll('thead th');
      expect(ths[0].textContent).toContain('N.º de Socio');
      expect(ths[1].textContent).toContain('N.º de Grupo');
      expect(ths[2].textContent).toContain('Nombre');
      expect(ths[3].textContent).toContain('Apellido');
      expect(ths[4].textContent).toContain('Estado de Justificación');

      const filas = tablaInvolucrados.querySelectorAll('tbody tr');
      expect(filas.length).toBe(1);
      expect(filas[0].textContent).toContain('74907');
      expect(filas[0].textContent).toContain('G58');
      expect(filas[0].textContent).toContain('Lucas');
      expect(filas[0].textContent).toContain('Gastiaburu');
      expect(filas[0].textContent).toContain('En plazo');
    });
  });
});


