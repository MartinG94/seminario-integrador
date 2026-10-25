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
import {
  ComposicionTribunalDTO,
  DecisionCausalDTO,
  DescargoDetalleDTO,
  ExpedienteApiService
} from '../services/expediente-api.service';

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
      decisiones_causal: undefined
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
        'Pendiente de evaluación', 'Extraordinaria (T03)', 'Sin justificación'
      ]);
    });

    it('sólo permite evaluar las justificaciones T02', () => {
      abrirComo('TD');
      const [t02, t03, sinDescargo] = component.involucradosJustificacion;

      expect(component.esEvaluable(t02)).toBeTrue();
      expect(component.esEvaluable(t03)).toBeFalse();
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

    it('muestra la tabla de involucrados con el botón Evaluar justificación sólo en T02', () => {
      abrirComo('TD');
      fixture.detectChanges();

      const tabla: HTMLElement = fixture.nativeElement.querySelector('[aria-labelledby="titulo-involucrados-justificacion"]');
      expect(tabla).toBeTruthy();
      expect(tabla.textContent).toContain('Pérez');
      const botones = tabla.querySelectorAll('.btn-evaluar-justificacion');
      expect(botones.length).toBe(1);
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
      // "Emitir Resolución" espera los responsables calculados (inhibición, S4-04).
      spyOn(TestBed.inject(ExpedienteApiService), 'obtenerComposicionTribunal').and.returnValue(of({
        estampada: false,
        estampada_at: null,
        asientos: [],
        apartados: [],
        requiere_ad_hoc: false,
        motivos_ad_hoc: [],
        observaciones: [],
        resolucion_asamblea: null,
        puede_registrar_asamblea: false,
        usuario: { esta_involucrado: false }
      }));
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
  describe('Tribunal de la causa: inhibición, suplencia y Asamblea (S4-04)', () => {
    let api: ExpedienteApiService;

    const expediente = {
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

    const composicion = (cambios: Partial<ComposicionTribunalDTO> = {}): ComposicionTribunalDTO => ({
      estampada: false,
      estampada_at: null,
      asientos: [
        { anio_social: 4, socio_id: 1, nro_socio: 81004, nombre: 'Giuliano Toselli', grupo: 'G57', condicion: 'TITULAR', firma: '81004 - Giuliano Toselli - G57', reemplaza_a: '' },
        { anio_social: 5, socio_id: 4, nro_socio: 82005, nombre: 'Abril Gusella', grupo: 'G58', condicion: 'SUPLENTE', firma: '82005 - Abril Gusella - G58 (Sup.)', reemplaza_a: 'Catalina Cerda (N° 81005)' },
        { anio_social: 6, socio_id: 5, nro_socio: 81006, nombre: 'Candela Moreno', grupo: 'G59', condicion: 'TITULAR', firma: '81006 - Candela Moreno - G59', reemplaza_a: '' }
      ],
      apartados: [
        { socio_id: 3, nro_socio: 81005, nombre: 'Catalina Cerda', anio_social: 5, condicion: 'TITULAR' }
      ],
      requiere_ad_hoc: false,
      motivos_ad_hoc: [],
      observaciones: [],
      resolucion_asamblea: null,
      puede_registrar_asamblea: false,
      usuario: { esta_involucrado: false },
      ...cambios
    });

    const casoCritico = (cambios: Partial<ComposicionTribunalDTO> = {}) => composicion({
      requiere_ad_hoc: true,
      motivos_ad_hoc: ['El titular y el suplente del 5.º año están involucrados en la causa (Art. 95 del Estatuto).'],
      ...cambios
    });

    beforeEach(() => {
      api = TestBed.inject(ExpedienteApiService);
      spyOn(api, 'obtenerDetalleExpediente').and.returnValue(
        of({ id: 12, numero: 'EXP-0012/2026', estado: 'revision_resolucion', socios: [], descargos: [] })
      );
    });

    function abrirComo(rol: string, dto: ComposicionTribunalDTO = composicion()): void {
      spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes(rol as any));
      spyOn(api, 'obtenerComposicionTribunal').and.returnValue(of(dto));
      component.abrirDetalle(expediente);
      fixture.detectChanges();
    }

    const compiled = (): HTMLElement => fixture.nativeElement as HTMLElement;

    it('muestra los tres responsables con pie de firma y los apartados', () => {
      abrirComo('TD');

      expect(api.obtenerComposicionTribunal).toHaveBeenCalledWith('12');
      const responsables = Array.from(compiled().querySelectorAll('.responsable-tribunal')).map(el => el.textContent || '');
      expect(responsables.length).toBe(3);
      expect(responsables[1]).toContain('82005 - Abril Gusella - G58 (Sup.)');
      expect(responsables[1]).toContain('Reemplaza a Catalina Cerda (N° 81005)');
      expect(compiled().querySelector('.apartado-tribunal')?.textContent).toContain('81005 - Catalina Cerda');
    });

    it('no ofrece trámites manuales de apartamiento, ad hoc ni constitución', () => {
      abrirComo('TD');
      expect(compiled().querySelector('.btn-apartarme')).toBeNull();
      expect(compiled().querySelector('.designacion-ad-hoc')).toBeNull();
      expect(compiled().querySelector('.btn-constituir')).toBeNull();
    });

    it('un socio sin rol de autoridad no consulta la composición', () => {
      spyOn(authService, 'tieneRol').and.returnValue(false);
      spyOn(api, 'obtenerComposicionTribunal');
      component.abrirDetalle(expediente);
      expect(api.obtenerComposicionTribunal).not.toHaveBeenCalled();
    });

    it('avisa si no se pudo cargar la composición', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      spyOn(api, 'obtenerComposicionTribunal').and.returnValue(throwError(() => ({ status: 500 })));
      component.abrirDetalle(expediente);
      expect(notifications.error).toHaveBeenCalled();
      expect(component.composicion).toBeNull();
    });

    describe('inhibición de involucrados (Art. 95 y Art. 24 RPD)', () => {
      it('muestra el banner y oculta decisión de justificativos y transición', () => {
        abrirComo('TD', composicion({ usuario: { esta_involucrado: true } }));

        const banner = compiled().querySelector('.banner-involucrado');
        expect(banner?.textContent).toContain('Participación restringida');
        expect(banner?.textContent).toContain('Tu lugar lo ocupa automáticamente tu suplente');
        expect(component.puedeEvaluarJustificaciones).toBeFalse();
        expect(component.puedeResolverExpedienteSeleccionado).toBeFalse();
        const footer = compiled().querySelector('.card-footer')?.textContent || '';
        expect(footer).not.toContain('Emitir Resolución');
      });

      it('un vocal no involucrado puede evaluar y resolver', () => {
        abrirComo('TD');
        expect(compiled().querySelector('.banner-involucrado')).toBeNull();
        expect(component.puedeEvaluarJustificaciones).toBeTrue();
        expect(component.puedeResolverExpedienteSeleccionado).toBeTrue();
        expect(compiled().querySelector('.card-footer')?.textContent).toContain('Emitir Resolución');
      });
    });

    describe('Tribunal Ad-Hoc / Asamblea (Art. 95)', () => {
      it('inmoviliza la resolución ordinaria y muestra el aviso', () => {
        abrirComo('TD', casoCritico());
        expect(compiled().querySelector('.aviso-ad-hoc')?.textContent).toContain('Tribunal Ad-Hoc');
        expect(compiled().querySelector('.lista-responsables')).toBeNull();
        expect(component.puedeResolverExpedienteSeleccionado).toBeFalse();
        expect(component.puedeRegistrarAsamblea).toBeFalse();
      });

      it('CD sube el acta y el expediente se emite', () => {
        abrirComo('CD', casoCritico({ puede_registrar_asamblea: true }));
        const emitida = casoCritico({
          resolucion_asamblea: { acta_nombre: 'acta.pdf', registrada_at: '2026-10-23T12:00:00Z', registrada_por_legajo: '77010' }
        });
        spyOn(api, 'registrarResolucionAsamblea').and.returnValue(of(emitida));
        const acta = new File(['%PDF-1.4'], 'acta.pdf', { type: 'application/pdf' });

        component.seleccionarActaAsamblea({ target: { files: [acta] } } as unknown as Event);
        fixture.detectChanges();
        (compiled().querySelector('.btn-registrar-asamblea') as HTMLButtonElement).click();
        fixture.detectChanges();

        expect(api.registrarResolucionAsamblea).toHaveBeenCalledWith('12', acta);
        expect(notifications.success).toHaveBeenCalledWith('Resolución por Asamblea registrada. El expediente fue emitido.');
        expect(compiled().querySelector('.resolucion-asamblea')?.textContent).toContain('77010');
        expect(compiled().querySelector('.registrar-asamblea')).toBeNull();
      });

      it('exige el acta antes de enviar', () => {
        abrirComo('CD', casoCritico({ puede_registrar_asamblea: true }));
        spyOn(api, 'registrarResolucionAsamblea');
        component.registrarResolucionAsamblea();
        expect(api.registrarResolucionAsamblea).not.toHaveBeenCalled();
        expect(notifications.error).toHaveBeenCalledWith('Adjuntá el acta de la Asamblea Extraordinaria en PDF.');
      });

      it('informa el rechazo del servidor', () => {
        abrirComo('CD', casoCritico({ puede_registrar_asamblea: true }));
        spyOn(api, 'registrarResolucionAsamblea').and.returnValue(
          throwError(() => ({ status: 409, error: { detail: 'La causa no requiere intervención de Asamblea.' } }))
        );
        component.actaAsamblea = new File(['%PDF-1.4'], 'acta.pdf', { type: 'application/pdf' });
        component.registrarResolucionAsamblea();
        expect(notifications.error).toHaveBeenCalled();
        expect(component.procesandoComposicion).toBeFalse();
      });
    });

    it('muestra los responsables estampados en la resolución', () => {
      abrirComo('TD', composicion({ estampada: true, estampada_at: '2026-10-22T12:00:00Z', apartados: [] }));
      expect(compiled().querySelector('.estado-composicion')?.textContent).toContain('Estampado en la resolución');
      expect(compiled().querySelectorAll('.responsable-tribunal').length).toBe(3);
    });
  });
});
