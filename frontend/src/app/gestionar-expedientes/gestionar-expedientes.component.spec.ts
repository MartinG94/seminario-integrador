import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { MatButtonModule } from '@angular/material/button';
import { of } from 'rxjs';

import { GestionarExpedientesComponent } from './gestionar-expedientes.component';
import { AuthService } from '../services/auth.service';
import { TribunalDataService, BoardResponseDTO } from '../services/tribunal-data.service';

describe('GestionarExpedientesComponent', () => {
  let component: GestionarExpedientesComponent;
  let fixture: ComponentFixture<GestionarExpedientesComponent>;
  let authService: AuthService;
  let dataService: TribunalDataService;
  let httpMock: HttpTestingController;

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
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        FormsModule,
        RouterTestingModule,
        MatButtonModule
      ],
      declarations: [GestionarExpedientesComponent],
      providers: [
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

  describe('Clasificador e indicador visual de urgencia (SCRUM-78)', () => {
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
    });
  });
});


