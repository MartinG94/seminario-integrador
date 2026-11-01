import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { MatButtonModule } from '@angular/material/button';
import { of, Subject, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

import { GestionarExpedientesComponent } from './gestionar-expedientes.component';
import { AuthService } from '../services/auth.service';
import { TribunalDataService, BoardResponseDTO, Expediente } from '../services/tribunal-data.service';
import {
  AntecedenteT03DTO,
  DecisionCausalDTO,
  DescargoDetalleDTO,
  ExpedienteApiService,
  ValoracionT03DTO
} from '../services/expediente-api.service';
import { ValoracionT03PanelComponent } from './valoracion-t03-panel/valoracion-t03-panel.component';

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
      declarations: [GestionarExpedientesComponent, ValoracionT03PanelComponent],
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
        urgencia: 'urgente', cantidadSocios: 1,
        firmas: { juecesFirmantes: ['Juez 1', 'Juez 2', 'Juez 3'] },
        ...overrides
      };
      component.expedientes = [expediente];
      fixture.detectChanges();
      return expediente;
    }

    it('muestra únicamente ID, urgencia, puntos, motivo, fecha y cantidad de involucrados en las seis etapas', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      for (const column of component.columnasKanban) {
        renderCase({ estado: column.estado });
        const cards: HTMLElement[] = Array.from(fixture.nativeElement.querySelectorAll('.kanban-card-mat'));
        expect(cards.length).toBe(1);
        const card = cards[0];
        expect(card.innerText.replace(/\s+/g, ' ').trim()).toBe(
          '007/2026 Urgente -1 pts Inasistencia a reunión institucional 07/10/2026 group 1'
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
        '018/2026 Normal -0.5 pts Inasistencia a reunión institucional 07/10/2026 group 1'
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
  describe('Evaluación de justificaciones T02 (S4-02)', () => {
    let api: ExpedienteApiService;
    const fundamento = 'El certificado no acredita la fecha de la reunión.';

    const expRevision = {
      id: '12',
      numero: 'EXP-0012/2026',
      socio: 'Ana Pérez',
      legajo: '76001',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia',
      fechaCreacion: '2026-10-01',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -1
    } as Expediente;

    const descargoT02 = (): DescargoDetalleDTO => ({
      id: 5,
      socio_id: 3,
      socio_legajo: '76001',
      socio_nombre: 'Ana Pérez',
      socio_first_name: 'Ana',
      socio_last_name: 'Pérez',
      tipo: 'T02_CERTIFICADO',
      causal: 'Enfermedad certificada',
      texto: 'Adjunto certificado.',
      presentado_at: '2026-10-05T10:00:00Z',
      evidencias: [{ id: 'ev-1', nombre_original: 'certificado.pdf' } as any],
      regla_sugerida: 'ACCEPTED',
      decisiones_causal: []
    });

    const descargoT03 = (): DescargoDetalleDTO => ({
      ...descargoT02(),
      id: 6,
      socio_id: 4,
      socio_legajo: '76002',
      tipo: 'T03_EXTRAORDINARIO',
      causal: '',
      evidencias: [],
      regla_sugerida: undefined,
      decisiones_causal: undefined,
      valoraciones_t03: []
    });

    const detalle = (estado = 'revision_resolucion') => ({
      id: 12,
      numero: 'EXP-0012/2026',
      estado,
      socios: [
        { id: 3, legajo: '76001', nombre: 'Ana Pérez', first_name: 'Ana', last_name: 'Pérez', grupo: '59' },
        { id: 4, legajo: '76002', nombre: 'Bruno Díaz', first_name: 'Bruno', last_name: 'Díaz', grupo: '60' },
        { id: 7, legajo: '76003', nombre: 'Carla Gómez', first_name: 'Carla', last_name: 'Gómez', grupo: '61' }
      ],
      descargos: [descargoT02(), descargoT03()]
    });

    const decisionRegistrada = {
      id: 1, version: 1, decision: 'REJECTED', decision_display: 'Rechazada'
    } as DecisionCausalDTO;

    beforeEach(() => {
      api = TestBed.inject(ExpedienteApiService);
    });

    function abrirComo(rol: string, estado = 'revision_resolucion'): void {
      spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes(rol as any));
      spyOn(api, 'obtenerDetalleExpediente').and.returnValue(of(detalle(estado)));
      component.abrirDetalle({ ...expRevision, estado } as Expediente);
    }

    function filaT02() {
      return component.involucradosJustificacion.find(f => f.descargo?.id === 5)!;
    }

    function evaluarT02() {
      abrirComo('TD');
      const fila = filaT02();
      component.seleccionarInvolucrado(fila);
      return fila;
    }

    it('lista una fila por involucrado con su estado de justificación', () => {
      abrirComo('TD');

      expect(api.obtenerDetalleExpediente).toHaveBeenCalledWith('12');
      const filas = component.involucradosJustificacion;
      expect(filas.map(f => f.legajo)).toEqual(['76001', '76002', '76003']);
      expect(filas.map(f => [f.nombre, f.apellido, f.grupo])).toEqual([
        ['Ana', 'Pérez', '59'], ['Bruno', 'Díaz', '60'], ['Carla', 'Gómez', '61']
      ]);
      expect(filas.map(f => component.estadoJustificacion(f))).toEqual([
        'Pendiente de evaluación', 'Pendiente de valoración', 'Sin justificación'
      ]);
    });

    it('permite evaluar los T02 y valorar los T03, pero no a quien no presentó justificación', () => {
      abrirComo('TD');
      const [t02, t03, sinDescargo] = component.involucradosJustificacion;

      expect(component.esEvaluable(t02)).toBeTrue();
      expect(component.esEvaluable(t03)).toBeTrue();
      expect(component.esEvaluable(sinDescargo)).toBeFalse();
    });

    it('no carga justificaciones antes de la etapa de revisión', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      spyOn(api, 'obtenerDetalleExpediente');

      component.abrirDetalle({ ...expRevision, estado: 'justificando' } as Expediente);

      expect(api.obtenerDetalleExpediente).not.toHaveBeenCalled();
      expect(component.involucradosJustificacion).toEqual([]);
    });

    it('permite a la Comisión Directiva consultar después de emitida la resolución, sin registrar', () => {
      abrirComo('CD', 'emitido');

      expect(api.obtenerDetalleExpediente).toHaveBeenCalledWith('12');
      expect(component.puedeConsultarJustificaciones).toBeTrue();
      expect(component.puedeEvaluarJustificaciones).toBeFalse();
    });

    it('el Tribunal no puede registrar decisiones una vez emitida la resolución', () => {
      abrirComo('TD', 'emitido');

      expect(component.puedeConsultarJustificaciones).toBeTrue();
      expect(component.puedeEvaluarJustificaciones).toBeFalse();
    });

    it('navega del listado al panel del involucrado y vuelve', () => {
      const fila = evaluarT02();
      expect(component.involucradoSeleccionado).toBe(fila);

      component.volverAListadoInvolucrados();

      expect(component.involucradoSeleccionado).toBeNull();
      expect(component.modalDetalleAbierto).toBeTrue();
    });

    it('exige fundamento al desaprobar y no llama a la API sin él', () => {
      evaluarT02();
      spyOn(api, 'registrarDecisionCausal');
      component.borradorCausal.decision = 'REJECTED';

      expect(component.requiereFundamento()).toBeTrue();
      component.registrarDecisionCausal();

      expect(api.registrarDecisionCausal).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledWith('Escribí un fundamento de al menos 20 caracteres.');
    });

    it('exige fundamento al apartarse de la sugerencia del sistema', () => {
      const fila = evaluarT02();
      fila.descargo!.regla_sugerida = 'REJECTED';
      component.borradorCausal.decision = 'ACCEPTED';

      expect(component.requiereFundamento()).toBeTrue();
    });

    it('aprueba siguiendo la sugerencia sin fundamento', () => {
      evaluarT02();
      component.borradorCausal.decision = 'ACCEPTED';

      expect(component.requiereFundamento()).toBeFalse();
    });

    it('exige elegir aprobar o desaprobar', () => {
      evaluarT02();
      spyOn(api, 'registrarDecisionCausal');

      component.registrarDecisionCausal();

      expect(api.registrarDecisionCausal).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledWith('Elegí si aprobás o desaprobás la justificación.');
    });

    it('registra la decisión valorando los comprobantes vigentes y actualiza el estado', () => {
      const fila = evaluarT02();
      spyOn(api, 'registrarDecisionCausal').and.returnValue(of(decisionRegistrada));
      component.borradorCausal.decision = 'REJECTED';
      component.borradorCausal.fundamento = `  ${fundamento}  `;

      component.registrarDecisionCausal();

      expect(api.registrarDecisionCausal).toHaveBeenCalledWith('12', 5, {
        decision: 'REJECTED',
        fundamento,
        evidencia_ids: ['ev-1']
      });
      expect(fila.descargo!.decisiones_causal?.[0]).toBe(decisionRegistrada);
      expect(component.estadoJustificacion(fila)).toBe('Desaprobada');
      expect(component.borradorCausal.decision).toBe('');
      expect(notifications.success).toHaveBeenCalledWith('Decisión registrada (versión 1).');
    });

    it('informa el error del servidor mediante el servicio de notificaciones', () => {
      evaluarT02();
      spyOn(api, 'registrarDecisionCausal').and.returnValue(
        throwError(() => ({ status: 409, error: { detail: 'El expediente no admite decisiones.' } }))
      );
      component.borradorCausal.decision = 'ACCEPTED';

      component.registrarDecisionCausal();

      expect(notifications.error).toHaveBeenCalledWith('El expediente no admite decisiones.');
      expect(component.registrandoCausal).toBeFalse();
    });

    it('abre el comprobante con la descarga segura de evidencias', () => {
      evaluarT02();
      const ventana = { location: { href: '' }, close: jasmine.createSpy('close') };
      spyOn(window, 'open').and.returnValue(ventana as any);
      spyOn(URL, 'createObjectURL').and.returnValue('blob:comprobante');
      spyOn(api, 'descargarEvidencia').and.returnValue(of(new Blob(['%PDF'])));

      component.verComprobante({ id: 'ev-1', nombre_original: 'certificado.pdf' } as any);

      expect(api.descargarEvidencia).toHaveBeenCalledWith('12', 'ev-1');
      expect(ventana.location.href).toBe('blob:comprobante');
    });

    it('cierra la ventana y avisa si no se puede abrir el comprobante', () => {
      evaluarT02();
      const ventana = { location: { href: '' }, close: jasmine.createSpy('close') };
      spyOn(window, 'open').and.returnValue(ventana as any);
      spyOn(api, 'descargarEvidencia').and.returnValue(throwError(() => ({ status: 403 })));

      component.verComprobante({ id: 'ev-1', nombre_original: 'certificado.pdf' } as any);

      expect(ventana.close).toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledWith('No se pudo abrir el comprobante.');
    });

    it('muestra la tabla de involucrados con la acción de cada justificación presentada', () => {
      abrirComo('TD');
      fixture.detectChanges();

      const tabla: HTMLElement = fixture.nativeElement.querySelector('[aria-labelledby="titulo-involucrados-justificacion"]');
      expect(tabla).toBeTruthy();
      expect(tabla.textContent).toContain('Pérez');
      const botones = tabla.querySelectorAll('.btn-evaluar-justificacion');
      expect(botones.length).toBe(2);
      expect(botones[1].textContent).toContain('Valorar T03');
      expect(botones[0].textContent).toContain('Evaluar justificación');
      expect(botones[0].querySelector('.material-icons')?.textContent).toContain('gavel');
    });

    it('renderiza el panel de evaluación accesible del involucrado', () => {
      abrirComo('TD');
      fixture.detectChanges();
      (fixture.nativeElement.querySelector('.btn-evaluar-justificacion') as HTMLButtonElement).click();
      component.borradorCausal.decision = 'REJECTED';
      component.borradorCausal.fundamento = 'Hola';
      fixture.detectChanges();

      const panel: HTMLElement = fixture.nativeElement.querySelector('[aria-labelledby="titulo-evaluar-justificacion"]');
      expect(panel).toBeTruthy();
      expect(panel.textContent).toContain('76001');
      expect(panel.textContent).toContain('Enfermedad certificada');
      expect(panel.textContent).toContain('Adjunto certificado.');
      expect(panel.querySelector('.btn-ver-comprobante')?.textContent).toContain('VER COMPROBANTE');
      expect(panel.querySelector('.btn-aprobar-causal')?.textContent).toContain('APROBAR');
      expect(panel.querySelector('.btn-desaprobar-causal')?.textContent).toContain('DESAPROBAR');
      expect(panel.querySelector('input[type="checkbox"]')).toBeNull();

      const textarea = panel.querySelector('textarea') as HTMLTextAreaElement;
      expect(textarea.getAttribute('aria-required')).toBe('true');
      const ayuda = panel.querySelector('#' + textarea.getAttribute('aria-describedby')!.split(' ')[0]);
      expect(ayuda?.textContent).toContain('mínimo 20 caracteres');
      expect(panel.querySelector('.contador-fundamento')?.textContent).toContain('4 / 5000');
    });

    describe('Valoración T03 en la sala (S4-03)', () => {
      const valoracion = (overrides: Partial<ValoracionT03DTO> = {}): ValoracionT03DTO => ({
        id: 1,
        descargo: 6,
        version: 1,
        resultado: 'ACCEPTED',
        resultado_display: 'Aprobada',
        fundamento,
        antecedentes: [],
        autor: 'miembro.td',
        autor_legajo: '408917',
        autor_rol: 'TD',
        autor_condicion: 'TITULAR',
        autor_condicion_display: 'Miembro Titular',
        created_at: '2026-10-20T15:30:00Z',
        ...overrides
      });

      const antecedente: AntecedenteT03DTO = {
        id: 7,
        numero: 'EXP-0007/2026',
        fecha_emision: '2026-09-15T12:00:00Z',
        motivo: 'Inasistencia a la reunión plenaria',
        reglamento_invocado: 'Art. 86 del Reglamento Interno'
      };

      const payload = { resultado: 'ACCEPTED' as const, fundamento, antecedente_ids: [7] };

      function abrirConT03(valoraciones: ValoracionT03DTO[] = [], rol = 'TD', estado = 'revision_resolucion') {
        const base = detalle(estado);
        base.descargos[1].valoraciones_t03 = valoraciones;
        spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes(rol as any));
        spyOn(api, 'obtenerDetalleExpediente').and.returnValue(of(base));
        component.abrirDetalle({ ...expRevision, estado } as Expediente);
        return component.involucradosJustificacion.find(f => f.descargo?.id === 6)!;
      }

      function valorarT03(valoraciones: ValoracionT03DTO[] = []) {
        const fila = abrirConT03(valoraciones);
        component.seleccionarInvolucrado(fila);
        return fila;
      }

      it('permite valorar un T03 vigente', () => {
        expect(component.esEvaluable(abrirConT03())).toBeTrue();
      });

      it('muestra el T03 sin valorar como pendiente de valoración', () => {
        expect(component.estadoJustificacion(abrirConT03())).toBe('Pendiente de valoración');
      });

      it('muestra el resultado de la versión vigente del T03', () => {
        const fila = abrirConT03([
          valoracion({ id: 2, version: 2, resultado: 'REJECTED', resultado_display: 'Desaprobada' }),
          valoracion()
        ]);

        expect(component.estadoJustificacion(fila)).toBe('Desaprobada');
      });

      it('no revela la valoración a la autoridad imputada, que no la recibe del servidor', () => {
        const fila = abrirConT03();
        delete fila.descargo?.valoraciones_t03;

        expect(component.estadoJustificacion(fila)).toBe('Extraordinaria (T03)');
        expect(component.esEvaluable(fila)).toBeFalse();
      });

      it('ofrece la acción de valorar el T03 y conserva la de evaluar el T02', () => {
        abrirConT03();
        fixture.detectChanges();

        const acciones = Array.from<HTMLElement>(fixture.nativeElement.querySelectorAll('.btn-evaluar-justificacion'));
        expect(acciones.map(accion => accion.textContent)).toEqual([
          jasmine.stringContaining('Evaluar justificación'),
          jasmine.stringContaining('Valorar T03')
        ]);
      });

      it('muestra el panel de valoración sólo para el T03', () => {
        valorarT03();
        fixture.detectChanges();

        expect(fixture.nativeElement.querySelector('app-valoracion-t03-panel')).toBeTruthy();
        expect(fixture.nativeElement.querySelector('.btn-aprobar-causal')).toBeNull();
        expect(fixture.nativeElement.textContent).not.toContain('Sugerencia del sistema');
      });

      it('no muestra el panel de valoración para el T02', () => {
        evaluarT02();
        fixture.detectChanges();

        expect(fixture.nativeElement.querySelector('app-valoracion-t03-panel')).toBeNull();
        expect(fixture.nativeElement.querySelector('.btn-aprobar-causal')).toBeTruthy();
      });

      it('muestra el historial en sólo lectura a la Comisión Directiva', () => {
        component.seleccionarInvolucrado(abrirConT03([valoracion()], 'CD', 'emitido'));
        fixture.detectChanges();

        expect(fixture.nativeElement.querySelector('.historial-t03')).toBeTruthy();
        expect(fixture.nativeElement.querySelector('.btn-registrar-valoracion')).toBeNull();
      });

      it('agrega el antecedente encontrado', () => {
        spyOn(api, 'buscarAntecedente').and.returnValue(of(antecedente));
        valorarT03();

        component.buscarAntecedenteT03('7/2026');

        expect(api.buscarAntecedente).toHaveBeenCalledOnceWith('7/2026');
        expect(component.antecedentesT03).toEqual([antecedente]);
      });

      it('no vincula dos veces el mismo antecedente aunque se escriba distinto', () => {
        spyOn(api, 'buscarAntecedente').and.returnValue(of(antecedente));
        valorarT03();
        component.buscarAntecedenteT03('7/2026');

        component.buscarAntecedenteT03('EXP-0007/2026');

        expect(component.antecedentesT03.length).toBe(1);
        expect(notifications.error).toHaveBeenCalledOnceWith('Ese antecedente ya está vinculado.');
      });

      it('notifica el error cuando el antecedente no existe', () => {
        const detail = 'No existe un expediente emitido con ese número.';
        spyOn(api, 'buscarAntecedente').and.returnValue(throwError(() => ({ status: 404, error: { detail } })));
        valorarT03();

        component.buscarAntecedenteT03('999/2026');

        expect(component.antecedentesT03).toEqual([]);
        expect(notifications.error).toHaveBeenCalledOnceWith(detail);
      });

      it('quita un antecedente de la valoración', () => {
        valorarT03();
        component.antecedentesT03 = [antecedente];

        component.quitarAntecedenteT03(7);

        expect(component.antecedentesT03).toEqual([]);
      });

      it('registra la valoración, suma la versión al historial y limpia los antecedentes', () => {
        const nueva = valoracion({ id: 2, version: 2 });
        spyOn(api, 'registrarValoracionT03').and.returnValue(of(nueva));
        const anterior = valoracion();
        const fila = valorarT03([anterior]);
        component.antecedentesT03 = [antecedente];

        component.registrarValoracionT03(payload);

        expect(api.registrarValoracionT03).toHaveBeenCalledOnceWith('12', 6, payload);
        expect(fila.descargo?.valoraciones_t03).toEqual([nueva, anterior]);
        expect(component.antecedentesT03).toEqual([]);
        expect(component.registrandoValoracion).toBeFalse();
        expect(notifications.success).toHaveBeenCalledOnceWith('Valoración registrada (versión 2).');
      });

      it('conserva el borrador si el registro falla', () => {
        const detail = 'No podés valorar: sos parte interesada en esta causa.';
        spyOn(api, 'registrarValoracionT03').and.returnValue(throwError(() => ({ status: 403, error: { detail } })));
        const fila = valorarT03();
        component.antecedentesT03 = [antecedente];

        component.registrarValoracionT03(payload);

        expect(fila.descargo?.valoraciones_t03).toEqual([]);
        expect(component.antecedentesT03).toEqual([antecedente]);
        expect(component.registrandoValoracion).toBeFalse();
        expect(notifications.error).toHaveBeenCalledOnceWith(detail);
      });

      describe('respuestas tardías de la búsqueda de antecedentes', () => {
        let respuesta: Subject<AntecedenteT03DTO>;

        beforeEach(() => {
          respuesta = new Subject<AntecedenteT03DTO>();
          spyOn(api, 'buscarAntecedente').and.returnValue(respuesta);
        });

        it('no la suma al borrador de otro involucrado', () => {
          valorarT03();
          component.buscarAntecedenteT03('7/2026');

          component.seleccionarInvolucrado(filaT02());
          respuesta.next(antecedente);

          expect(component.antecedentesT03).toEqual([]);
        });

        it('no la suma después de volver al listado', () => {
          valorarT03();
          component.buscarAntecedenteT03('7/2026');

          component.volverAListadoInvolucrados();
          respuesta.next(antecedente);

          expect(component.antecedentesT03).toEqual([]);
        });

        it('no la suma después de cerrar el expediente', () => {
          valorarT03();
          component.buscarAntecedenteT03('7/2026');

          component.cerrarModales();
          respuesta.next(antecedente);

          expect(component.antecedentesT03).toEqual([]);
        });

        it('no la suma al borrador que sigue a un registro', () => {
          spyOn(api, 'registrarValoracionT03').and.returnValue(of(valoracion()));
          valorarT03();
          component.buscarAntecedenteT03('7/2026');

          component.registrarValoracionT03(payload);
          respuesta.next(antecedente);

          expect(component.antecedentesT03).toEqual([]);
        });

        it('no notifica el error de una búsqueda descartada', () => {
          valorarT03();
          component.buscarAntecedenteT03('999/2026');

          component.volverAListadoInvolucrados();
          respuesta.error({ status: 404, error: { detail: 'No existe.' } });

          expect(notifications.error).not.toHaveBeenCalled();
        });

        it('cancela la búsqueda en curso al destruir la sala', () => {
          valorarT03();
          component.buscarAntecedenteT03('7/2026');

          component.ngOnDestroy();

          expect(respuesta.observers.length).toBe(0);
        });

        it('conserva dos búsquedas seguidas del mismo borrador', () => {
          const segunda = new Subject<AntecedenteT03DTO>();
          (api.buscarAntecedente as jasmine.Spy).and.returnValues(respuesta, segunda);
          const otroAntecedente = { ...antecedente, id: 8, numero: 'EXP-0008/2026' };
          valorarT03();
          component.buscarAntecedenteT03('7/2026');
          component.buscarAntecedenteT03('8/2026');

          segunda.next(otroAntecedente);
          respuesta.next(antecedente);

          expect(component.antecedentesT03.map(a => a.id)).toEqual([8, 7]);
        });
      });

      it('descarta los antecedentes al volver al listado', () => {
        valorarT03();
        component.antecedentesT03 = [antecedente];

        component.volverAListadoInvolucrados();

        expect(component.antecedentesT03).toEqual([]);
      });

      it('indica en el buscador que se puede buscar por número y motivo', () => {
        fixture.detectChanges();

        const buscador: HTMLInputElement = fixture.nativeElement.querySelector('input[placeholder*="Buscar por"]');
        expect(buscador.placeholder).toContain('número');
        expect(buscador.placeholder).toContain('motivo');
      });
    });

    it('muestra el panel en sólo lectura a la Comisión Directiva', () => {
      abrirComo('CD', 'emitido');
      component.seleccionarInvolucrado(filaT02());
      fixture.detectChanges();

      const panel: HTMLElement = fixture.nativeElement.querySelector('[aria-labelledby="titulo-evaluar-justificacion"]');
      expect(panel.querySelector('.btn-ver-comprobante')).toBeTruthy();
      expect(panel.querySelector('.btn-aprobar-causal')).toBeNull();
      expect(panel.querySelector('textarea')).toBeNull();
    });
  });

  describe('S3-08: Visualización de socios involucrados', () => {
    const expUnicoSocio: Expediente = {
      id: '1',
      numero: 'EXP-001/2026',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia',
      titulo: 'Inasistencia a asamblea',
      creador: 'Gastiaburu, Lucas (74907)',
      fechaCreacion: '2026-03-01',
      estado: 'creado',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -1,
      cantidadSocios: 1,
      sociosInvolucrados: [
        { id: '1', legajo: '74907', nombre: 'Lucas Gastiaburu' }
      ]
    };

    const expMultiplesSocios: Expediente = {
      id: '2',
      numero: 'EXP-002/2026',
      socio: 'Lucas Martín Guillén',
      legajo: '85194',
      subcomision: 'Cómputos',
      motivo: 'Falta de informes',
      titulo: 'Falta de informes cuatrimestrales',
      creador: 'Guillén, Lucas Martín (85194)',
      fechaCreacion: '2026-03-02',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -1.5,
      cantidadSocios: 2,
      sociosInvolucrados: [
        { id: '2', legajo: '85194', nombre: 'Lucas Martín Guillén', grupo: '59', estado: 'Activo' },
        { id: '3', legajo: '87414', nombre: 'Diego Gabriel Sánchez', grupo: '59', estado: 'Pasivo' }
      ]
    };

    it('abrirModalSocios debe abrir el modal y seleccionar el expediente deteniendo propagación', () => {
      const dummyEvent = new MouseEvent('click');
      spyOn(dummyEvent, 'stopPropagation');

      component.abrirModalSocios(expMultiplesSocios, dummyEvent);

      expect(component.modalSociosAbierto).toBeTrue();
      expect(component.expedienteSeleccionado).toEqual(expMultiplesSocios);
      expect(dummyEvent.stopPropagation).toHaveBeenCalled();
    });

    it('cerrarModales debe cerrar modalSociosAbierto y reiniciar expedienteSeleccionado', () => {
      component.abrirModalSocios(expMultiplesSocios);
      expect(component.modalSociosAbierto).toBeTrue();

      component.cerrarModales();

      expect(component.modalSociosAbierto).toBeFalse();
      expect(component.expedienteSeleccionado).toBeNull();
    });

    it('las tarjetas kanban no muestran botones en el pie manteniendo simplicidad visual', () => {
      component.expedientes = [expMultiplesSocios];
      component.vistaActual = 'kanban';
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const kanbanButtons = compiled.querySelectorAll('.card-bottom button');
      expect(kanbanButtons.length).toBe(0);
    });

    it('debe mostrar columna Involucrados en la tabla y Grupo/Estado en el modal al hacer clic', () => {
      component.expedientes = [expMultiplesSocios];
      component.vistaActual = 'tabla';
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('table thead')?.textContent).toContain('Involucrados');
      const tableButton = compiled.querySelector('table tbody tr button[title="Ver Involucrados"]') as HTMLButtonElement;
      expect(tableButton).toBeTruthy();

      tableButton.click();
      fixture.detectChanges();

      expect(component.modalSociosAbierto).toBeTrue();
      expect(component.expedienteSeleccionado?.numero).toBe('EXP-002/2026');
      expect(component.expedienteSeleccionado?.sociosInvolucrados?.length).toBe(2);

      // Verificar contenido del modal renderizado incluyendo Grupo (solo número) y Estado
      const modal = compiled.querySelector('.modal-backdrop-custom');
      expect(modal).toBeTruthy();
      expect(modal?.textContent).toContain('Socios Involucrados');
      expect(modal?.textContent).toContain('85194');
      expect(modal?.textContent).toContain('Lucas Martín Guillén');
      expect(modal?.textContent).toContain('87414');
      expect(modal?.textContent).toContain('Diego Gabriel Sánchez');
      expect(modal?.textContent).toContain('59');
      expect(modal?.textContent).toContain('Activo');
      expect(modal?.textContent).toContain('Pasivo');
    });

    it('debe mostrar acciones Emitir Resolución y Firmar Resolución según permisos y estado', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      const expRevision: Expediente = { ...expMultiplesSocios, estado: 'revision_resolucion' };
      const expFirma: Expediente = { ...expMultiplesSocios, id: '3', estado: 'pendiente_correos' };
      component.expedientes = [expRevision, expFirma];
      component.vistaActual = 'tabla';
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const btnEmitir = compiled.querySelector('table tbody tr button[title="Emitir Resolución"]') as HTMLButtonElement;
      const btnFirmar = compiled.querySelectorAll('table tbody tr')[1].querySelector('button[title="Firmar Resolución"]') as HTMLButtonElement;

      expect(btnEmitir).toBeTruthy();
      expect(btnFirmar).toBeTruthy();
    });

    it('debe permitir navegar a Socios Involucrados desde el detalle y volver sin perder el contexto', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      const expDetalle: Expediente = {
        ...expMultiplesSocios,
        estado: 'revision_resolucion',
        razon: undefined
      };

      component.abrirDetalle(expDetalle);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelectorAll('.modal-backdrop-custom').length).toBe(1);
      expect(compiled.textContent).toContain('Motivo:');
      expect(compiled.textContent).toContain('Falta de informes');

      // Al abrir Socios Involucrados desde el footer del detalle, se cierra el modal de detalle evitando superposición
      const btnVerInvolucrados = compiled.querySelector('.modal-backdrop-custom .card-footer button[title="Ver Involucrados"]') as HTMLButtonElement;
      expect(btnVerInvolucrados).toBeTruthy();
      btnVerInvolucrados.click();
      fixture.detectChanges();

      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.modalSociosAbierto).toBeTrue();
      expect(compiled.querySelectorAll('.modal-backdrop-custom').length).toBe(1);

      // Al hacer clic en Volver, regresa al modal de detalle del expediente sin cerrar todo
      const btnVolver = compiled.querySelector('.modal-backdrop-custom button[aria-label="Volver al detalle"]') as HTMLButtonElement;
      expect(btnVolver).toBeTruthy();
      btnVolver.click();
      fixture.detectChanges();

      expect(component.modalSociosAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.expedienteSeleccionado).toEqual(expDetalle);
      expect(compiled.textContent).toContain('Motivo:');
    });
  });

  describe('S3-10: Detalle de expediente según formato canónico del Tribunal (SCRUM-81)', () => {
    const expMock: Expediente = {
      id: '419',
      numero: 'EXP-419/2025',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia reiterada a reuniones plenarias de comisión sin aviso previo formal',
      titulo: 'Falta disciplinaria por inasistencias plenarias',
      razon: 'Inasistencia injustificada a reuniones plenarias consecutivas',
      creador: 'Gastiaburu, Lucas (74907)',
      solicitante: 'Comisión Directiva',
      reglamento_asociado: 'Reglamento de Faltas y Sanciones Internas',
      fechaCreacion: '2025-10-15',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -2,
      urgencia: 'urgente',
      cantidadSocios: 1,
      sociosInvolucrados: [
        { id: '1', legajo: '74907', nombre: 'Lucas Gastiaburu', grupo: '10', estado: 'No justificado' }
      ]
    };

    it('debe renderizar exactamente los siete campos canónicos de metadatos en Modal 1', () => {
      component.abrirDetalle(expMock);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const modal = compiled.querySelector('.modal-backdrop-custom');
      expect(modal).toBeTruthy();

      // Cabecera: solo título identificador sin subtítulo duplicado
      const title = modal?.querySelector('.card-header .card-title')?.textContent?.trim();
      expect(title).toBe('Expediente 419/2025');
      expect(modal?.querySelector('.card-header .card-category')).toBeNull();

      // 1. Estado de expediente
      expect(modal?.textContent).toContain('Estado de expediente:');
      expect(modal?.textContent).toContain('En Revisión');

      // 2. Fecha de Solicitud (formato dd/MM/yyyy)
      expect(modal?.textContent).toContain('Fecha de Solicitud:');
      expect(modal?.textContent).toContain('15/10/2025');

      // 3. Título
      expect(modal?.textContent).toContain('Título:');
      expect(modal?.textContent).toContain('Falta disciplinaria por inasistencias plenarias');

      // 4. Motivo
      expect(modal?.textContent).toContain('Motivo:');
      expect(modal?.textContent).toContain('Inasistencia injustificada a reuniones plenarias consecutivas');

      // 5. Sanción solicitada
      expect(modal?.textContent).toContain('Sanción solicitada:');
      expect(modal?.textContent).toContain('-2 pts');

      // 6. Reglamento
      expect(modal?.textContent).toContain('Reglamento:');
      expect(modal?.textContent).toContain('Reglamento de Faltas y Sanciones Internas');

      // 7. Solicitante
      expect(modal?.textContent).toContain('Solicitante:');
      expect(modal?.textContent).toContain('74907 - Gastiaburu, Lucas');

      // Control de Urgencia debajo de los metadatos
      expect(modal?.textContent).toContain('Nivel de Urgencia:');
    });

    it('debe usar fallback canónico de reglamento sin citas de artículos', () => {
      const expSinReglamento: Expediente = {
        ...expMock,
        reglamento_asociado: undefined,
        reglamentoAsociado: undefined
      };
      expect(component.getReglamentoAsociado(expSinReglamento)).toBe('Reglamento Procesal Disciplinario 2026');
      expect(component.getReglamentoAsociado(null)).toBe('Reglamento Procesal Disciplinario 2026');
    });

    it('formatSolicitante debe formatear legajo - nombre o fallback', () => {
      expect(component.formatSolicitante(expMock)).toBe('74907 - Gastiaburu, Lucas');
      expect(component.formatSolicitante({ ...expMock, creador: 'Comisión Directiva' })).toBe('Comisión Directiva');
      expect(component.formatSolicitante({ ...expMock, creador: '', solicitante: '' })).toBe('Comisión Directiva');
      expect(component.formatSolicitante(null)).toBe('Comisión Directiva');
    });

    it('no debe renderizar las secciones pospuestas ni tabla embebida de involucrados en Modal 1', () => {
      component.abrirDetalle(expMock);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.card-responsable')).toBeNull();
      expect(compiled.querySelector('.reglamentos-list')).toBeNull();
      expect(compiled.querySelector('.card-body table')).toBeNull();
      expect(compiled.textContent).not.toContain('Responsables del tribunal');
      expect(compiled.textContent).not.toContain('Reglamentos respaldantes');
    });

    it('debe conservar las acciones existentes en el pie del modal', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      component.abrirDetalle(expMock);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const btnInvolucrados = compiled.querySelector('.modal-backdrop-custom .card-footer button[title="Ver Involucrados"]');
      const btnEmitir = compiled.querySelector('.modal-backdrop-custom .card-footer button[title="Emitir Resolución"]');
      const btnCerrar = compiled.querySelector('.modal-backdrop-custom .card-footer button.btn-default');

      expect(btnInvolucrados).toBeTruthy();
      expect(btnEmitir).toBeTruthy();
      expect(btnCerrar).toBeTruthy();
    });
  });
});


