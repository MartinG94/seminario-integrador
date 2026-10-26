import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { CommonModule } from '@angular/common';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

import { GestionarExpedientesComponent, InvolucradoJustificacion } from './gestionar-expedientes.component';
import { AuthService } from '../services/auth.service';
import { TribunalDataService, BoardResponseDTO, Expediente } from '../services/tribunal-data.service';
import {
  DecisionCausalDTO,
  DescargoDetalleDTO,
  ExpedienteApiService,
  HistorialT01DTO
} from '../services/expediente-api.service';
import { SocioApiService, SocioListItemDTO } from '../services/socio-api.service';

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
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'warning', 'info']);
    await TestBed.configureTestingModule({
      imports: [
        CommonModule,
        HttpClientTestingModule,
        FormsModule,
        RouterTestingModule,
        MatButtonModule,
        MatAutocompleteModule,
        MatFormFieldModule,
        MatInputModule,
        NoopAnimationsModule
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
          '7/2026 Urgente -1 pts Inasistencia a reunión institucional 07/10/2026 group 1'
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
        '18/2026 Normal -0.5 pts Inasistencia a reunión institucional 07/10/2026 group 1'
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

    it('carga justificaciones e involucrados al abrir el detalle', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      spyOn(api, 'obtenerDetalleExpediente').and.returnValue(of(detalle('justificando')));

      component.abrirDetalle({ ...expRevision, estado: 'justificando' } as Expediente);

      expect(api.obtenerDetalleExpediente).toHaveBeenCalledWith('12');
      expect(component.involucradosJustificacion.length).toBe(3);
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

    it('muestra la tabla de involucrados con el botón Ver Descargo para quienes tienen descargo', () => {
      abrirComo('TD');
      fixture.detectChanges();

      const tabla: HTMLElement = fixture.nativeElement.querySelector('.tabla-involucrados');
      expect(tabla).toBeTruthy();
      expect(tabla.textContent).toContain('Pérez');
      const botones = tabla.querySelectorAll('.btn-ver-descargo');
      expect(botones.length).toBe(2);
      expect(botones[0].textContent).toContain('Ver Descargo');
    });

    it('abre el modal de descargo al hacer clic en Ver Descargo y permite volver al detalle', () => {
      const router = TestBed.inject(Router);
      spyOn(router, 'navigate');
      abrirComo('TD');
      fixture.detectChanges();

      const btnVerDescargo = fixture.nativeElement.querySelector('.btn-ver-descargo') as HTMLButtonElement;
      expect(btnVerDescargo).toBeTruthy();
      btnVerDescargo.click();

      expect(router.navigate).not.toHaveBeenCalled();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.modalDescargoAbierto).toBeTrue();
      expect(component.involucradoSeleccionado).toBeTruthy();
      expect(component.involucradoSeleccionado?.socioId).toBe(3);

      component.volverADetalleDesdeDescargo();
      expect(component.modalDescargoAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
    });
  });

  describe('Evaluación de Descargo y Fijación de Puntaje Final (Modal 6 - SCRUM-51)', () => {
    let api: ExpedienteApiService;
    let filaPrueba: InvolucradoJustificacion;
    const expBase: Expediente = {
      id: '888',
      numero: 'EXP-0888/2026',
      socio: 'Diego Gabriel Sánchez',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia a reunión obligatoria',
      puntos: -3,
      estado: 'revision_resolucion',
      urgencia: 'normal',
      fecha: '2026-03-10'
    };

    beforeEach(() => {
      api = TestBed.inject(ExpedienteApiService);
      filaPrueba = {
        socioId: 10,
        legajo: '74907',
        nombre: 'Diego Gabriel',
        apellido: 'Sánchez',
        grupo: '59',
        descargo: {
          id: 5,
          tipo: 'T02_CERTIFICADO',
          leido: false,
          texto: 'Presento certificado médico...',
          evidencias: [{ id: 'ev-1', nombre_original: 'certificado.pdf' }]
        } as any
      };
      component.expedienteSeleccionado = { ...expBase, id: '888', numero: 'EXP-0888/2026', puntos: -3 };
      component.involucradosJustificacion = [filaPrueba];
    });

    it('genera el encabezado correcto con id de expediente, legajo y nombre completo', () => {
      component.involucradoSeleccionado = filaPrueba;
      const encabezado = component.getEncabezadoModalDescargo();
      expect(encabezado).toBe('Descargo exp 888 y 74907, Diego Gabriel Sánchez');
    });

    it('inicializa puntajeFinalInput con los puntos del expediente al abrir el descargo', () => {
      component.verDescargo(filaPrueba);
      expect(component.modalDescargoAbierto).toBeTrue();
      expect(component.involucradoSeleccionado).toBe(filaPrueba);
      expect(component.puntajeFinalInput).toBe(-3);
      expect(filaPrueba.descargo!.leido).toBeFalse();
    });

    it('valida la regla de fundamentación: obligatoria cuando puntaje_final < puntos_pedido', () => {
      component.verDescargo(filaPrueba);
      // Pedido es -3 (sanción).
      // Si puntajeFinalInput = -5 (agrava la sanción, < -3) -> obligatorio
      component.puntajeFinalInput = -5;
      expect(component.esFundamentoObligatorio()).toBeTrue();

      // Si puntajeFinalInput = -1 o 0 (reduce o anula la sanción, >= -3) -> opcional
      component.puntajeFinalInput = 0;
      expect(component.esFundamentoObligatorio()).toBeFalse();

      component.puntajeFinalInput = -3;
      expect(component.esFundamentoObligatorio()).toBeFalse();
    });

    it('no permite guardar si el fundamento es obligatorio y tiene menos de 10 caracteres', () => {
      component.verDescargo(filaPrueba);
      component.puntajeFinalInput = -5; // Menor que -3
      component.fundamentoPuntajeInput = 'corto';

      spyOn(api, 'registrarDecisionCausal');
      component.guardarYVolverDescargo();

      expect(api.registrarDecisionCausal).not.toHaveBeenCalled();
      expect(notifications.warning).toHaveBeenCalled();
      expect(filaPrueba.descargo!.leido).toBeFalse();
    });

    it('al presionar Guardar y Volver con datos válidos persiste, marca como Leído y regresa al detalle', () => {
      component.verDescargo(filaPrueba);
      component.puntajeFinalInput = 0; // A favor del socio, no exige fundamento
      spyOn(api, 'registrarDecisionCausal').and.returnValue(of({ id: 99, version: 1 } as any));

      component.guardarYVolverDescargo();

      expect(api.registrarDecisionCausal).toHaveBeenCalledWith('888', 5, jasmine.objectContaining({
        puntaje_final: 0
      }));
      expect(filaPrueba.descargo!.leido).toBeTrue();
      expect(filaPrueba.descargo!.puntaje_ratificado).toBe(0);
      expect(component.modalDescargoAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(notifications.success).toHaveBeenCalledWith('Evaluación del descargo guardada con éxito.');
    });

    it('al presionar Volver regresa al detalle sin marcar como Leído', () => {
      component.verDescargo(filaPrueba);
      expect(filaPrueba.descargo!.leido).toBeFalse();

      component.volverADetalleDesdeDescargo();

      expect(component.modalDescargoAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(filaPrueba.descargo!.leido).toBeFalse();
    });

    it('renderiza botones Guardar y Volver y Volver en el footer de Modal 6', () => {
      component.verDescargo(filaPrueba);
      fixture.detectChanges();

      const modalDescargo = fixture.nativeElement.querySelector('.modal-descargo-backdrop');
      expect(modalDescargo).toBeTruthy();

      const btnGuardar = modalDescargo.querySelector('.btn-guardar-volver');
      const btnVolver = modalDescargo.querySelector('.btn-volver');

      expect(btnGuardar).toBeTruthy();
      expect(btnVolver).toBeTruthy();
      expect(btnGuardar.textContent).toContain('Guardar y Volver');
      expect(btnVolver.textContent).toContain('Volver');
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

    it('debe mostrar los involucrados en el cuerpo del modal de detalle', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      const expDetalle: Expediente = {
        ...expMultiplesSocios,
        estado: 'revision_resolucion',
        razon: undefined
      };

      component.abrirDetalle(expDetalle);
      component.cargandoJustificaciones = false;
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelectorAll('.modal-backdrop-custom').length).toBe(1);
      expect(compiled.textContent).toContain('Motivo:');
      expect(compiled.textContent).toContain('Falta de informes');

      const tabla = compiled.querySelector('.tabla-involucrados');
      expect(tabla).toBeTruthy();
      expect(tabla?.textContent).toContain('Lucas Martín Guillén');
      expect(tabla?.textContent).toContain('Diego Gabriel Sánchez');
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

      // Cabecera: Exp: <n>/<YYYY> + título centrado
      const badgeExp = modal?.querySelector('.modal-badge-exp')?.textContent?.trim();
      expect(badgeExp).toBe('Exp: 419/2025');
      const title = modal?.querySelector('.modal-titulo-central h4')?.textContent?.trim();
      expect(title).toBe('Falta disciplinaria por inasistencias plenarias');

      // 1. Estado
      expect(modal?.textContent).toContain('Estado:');
      expect(modal?.textContent).toContain('En Revisión');

      // 2. Fecha de Solicitud (formato dd/MM/yyyy)
      expect(modal?.textContent).toContain('Fecha de Solicitud:');
      expect(modal?.textContent).toContain('15/10/2025');

      // 3. Motivo
      expect(modal?.textContent).toContain('Motivo:');
      expect(modal?.textContent).toContain('Inasistencia injustificada a reuniones plenarias consecutivas');

      // 4. Puntaje Solicitado
      expect(modal?.textContent).toContain('Puntaje Solicitado:');
      expect(modal?.textContent).toContain('-2');

      // 5. Reglamentación
      expect(modal?.textContent).toContain('Reglamentación:');
      expect(modal?.textContent).toContain('Reglamento de Faltas y Sanciones Internas');

      // 6. Solicitante
      expect(modal?.textContent).toContain('Solicitante:');
      expect(modal?.textContent).toContain('74907 - Gastiaburu, Lucas');

      // Control de Urgencia
      expect(modal?.textContent).toContain('Urgencia:');
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

    it('debe renderizar la tabla de involucrados y las acciones validadas en el pie del modal', () => {
      spyOn(authService, 'tieneRol').and.returnValue(true);
      component.abrirDetalle(expMock);
      component.cargandoJustificaciones = false;
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.tabla-involucrados')).toBeTruthy();
      expect(compiled.querySelector('.card-footer .btn-cerrar-modal')).toBeTruthy();
    });
  });
  describe('Apelación y adecuación del T01 (PB-02)', () => {
    let api: ExpedienteApiService;
    let socioApi: SocioApiService;
    const motivos = 'El debate acreditó que la falta fue compartida con un tercer socio.';

    const expediente = {
      id: '7',
      numero: 'EXP-0701/2026',
      socio: 'Ana Pérez',
      legajo: '78002',
      subcomision: 'Cómputos',
      motivo: 'Uso indebido del laboratorio',
      fechaCreacion: '2026-10-20',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -2
    } as Expediente;

    const historial = (cambios: Partial<HistorialT01DTO> = {}): HistorialT01DTO => ({
      es_t01: true,
      estado: 'revision_resolucion',
      plazo_dias_vigente: 5,
      puntos_vigentes: '-2.00',
      involucrados: [
        { id: 3, legajo: '78002', nombre: 'Ana Pérez (N° 78002)' },
        { id: 4, legajo: '78003', nombre: 'Bruno Díaz (N° 78003)' }
      ],
      original: {
        numero_t01: 'T01-2026-ABC',
        tipo_accion: 'SANCTION',
        emitido_at: '2026-10-15T10:00:00Z',
        solicitante: 'Carla Gómez (N° 78001)',
        snapshot: { puntos: '-2.00' }
      },
      periodos: [],
      apelaciones: [
        { socio_id: 3, socio: 'Ana Pérez (N° 78002)', numero: 1, texto: 'Primera versión de la apelación.', created_at: '2026-10-16T10:00:00Z' },
        { socio_id: 3, socio: 'Ana Pérez (N° 78002)', numero: 2, texto: 'No estuve presente en el laboratorio.', created_at: '2026-10-17T10:00:00Z' }
      ],
      adecuaciones: [],
      ...cambios
    });

    beforeEach(() => {
      api = TestBed.inject(ExpedienteApiService);
      socioApi = TestBed.inject(SocioApiService);
    });

    function abrirComo(rol: string, dto: HistorialT01DTO = historial(), estado = 'revision_resolucion'): void {
      spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes(rol as any));
      spyOn(api, 'obtenerDetalleExpediente').and.returnValue(of({ id: 7, numero: 'EXP-0701/2026', estado, socios: [], descargos: [] }));
      spyOn(api, 'obtenerHistorialT01').and.returnValue(of(dto));
      component.abrirDetalle({ ...expediente, estado } as Expediente);
      fixture.detectChanges();
    }

    it('muestra el T01 original y la última versión de cada apelación', () => {
      abrirComo('CD');
      expect(api.obtenerHistorialT01).toHaveBeenCalledWith('7');
      expect(component.historialT01?.original?.numero_t01).toBe('T01-2026-ABC');
      const apelacionesSocio3 = component.apelacionesDe(3);
      expect(apelacionesSocio3.length).toBe(2);
      expect(apelacionesSocio3[apelacionesSocio3.length - 1].texto).toBe('No estuve presente en el laboratorio.');
      expect(component.apelacionesDe(4).length).toBe(0);
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.panel-t01')).toBeNull();
      expect(component.puedeAdecuarT01).toBeFalse();
    });

    it('no muestra el panel en expedientes que no vienen de un T01', () => {
      abrirComo('TD', historial({ es_t01: false }));
      expect((fixture.nativeElement as HTMLElement).querySelector('.panel-t01')).toBeNull();
    });

    it('sólo el TD adecúa y sólo en "Justificaciones en revisión"', () => {
      abrirComo('TD', historial(), 'justificando');
      expect(component.puedeAdecuarT01).toBeFalse();
    });

    it('prepara el borrador con los puntos e involucrados vigentes', () => {
      abrirComo('TD');
      expect(component.puedeAdecuarT01).toBeTrue();
      expect(component.borradorAdecuacion.puntos).toBe(-2);
      expect(component.borradorAdecuacion.socios.map(s => s.id)).toEqual([3, 4]);
    });

    it('busca socios para agregar sin repetir involucrados', fakeAsync(() => {
      abrirComo('TD');
      spyOn(socioApi, 'searchSocios').and.returnValue(of({
        count: 2, next: null, previous: null,
        results: [
          { id: 4, legajo: '78003', first_name: 'Bruno', last_name: 'Díaz' } as SocioListItemDTO,
          { id: 9, legajo: '78004', first_name: 'Dario', last_name: 'Luna' } as SocioListItemDTO
        ]
      }));
      component.buscarSocioAdecuacion('lu');
      tick(300);
      expect(socioApi.searchSocios).not.toHaveBeenCalled();
      component.buscarSocioAdecuacion('luna');
      tick(300);
      expect(component.candidatosAdecuacion.map(s => s.id)).toEqual([9]);

      component.agregarSocioAdecuacion(component.candidatosAdecuacion[0]);
      component.quitarSocioAdecuacion(4);
      expect(component.borradorAdecuacion.socios.map(s => s.id)).toEqual([3, 9]);
    }));

    it('valida involucrados y motivos antes de enviar', () => {
      abrirComo('TD');
      spyOn(api, 'adecuarT01');
      component.borradorAdecuacion.socios = [];
      component.registrarAdecuacion();
      expect(notifications.error).toHaveBeenCalledWith('Debe quedar al menos un involucrado en el expediente.');

      component.borradorAdecuacion.socios = [{ id: 3, legajo: '78002', nombre: 'Ana' }];
      component.borradorAdecuacion.motivos = 'Breve';
      component.registrarAdecuacion();
      expect(notifications.error).toHaveBeenCalledWith('Indicá los motivos de la adecuación con al menos 20 caracteres.');
      expect(api.adecuarT01).not.toHaveBeenCalled();
    });

    it('registra la adecuación con nuevo plazo y actualiza el detalle', () => {
      abrirComo('TD');
      const actualizado = historial({ estado: 'justificando', puntos_vigentes: '-1.50' });
      spyOn(api, 'adecuarT01').and.returnValue(of(actualizado));
      component.borradorAdecuacion.puntos = -1.5;
      component.borradorAdecuacion.motivos = `  ${motivos}  `;
      component.borradorAdecuacion.reabrirPlazo = true;

      component.registrarAdecuacion();

      expect(api.adecuarT01).toHaveBeenCalledWith('7', {
        puntos: -1.5,
        socios: [3, 4],
        motivos,
        reabrir_plazo: true
      });
      expect(component.expedienteSeleccionado?.estado).toBe('justificando');
      expect(component.expedienteSeleccionado?.puntos).toBe(-1.5);
      expect(component.borradorAdecuacion.motivos).toBe('');
      expect(notifications.success).toHaveBeenCalledWith(
        'Adecuación registrada. Se abrió un nuevo plazo de apelación y se notificaron los motivos.'
      );
    });

    it('informa el rechazo del servidor', () => {
      abrirComo('TD');
      spyOn(api, 'adecuarT01').and.returnValue(throwError(() => ({ status: 400, error: { detail: 'Sin cambios.' } })));
      component.borradorAdecuacion.motivos = motivos;
      component.registrarAdecuacion();
      expect(notifications.error).toHaveBeenCalled();
      expect(component.adecuando).toBeFalse();
    });
  });

  describe('SCRUM-70 / PR #64: Modal de Detalle Rediseñado según boceto PO', () => {
    let api: ExpedienteApiService;
    let router: Router;

    const expBase: Expediente = {
      id: '201',
      numero: 'EXP-001/2026',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia no justificada a reunión plenaria',
      titulo: 'Inasistencia a plenaria',
      fechaCreacion: '2026-03-01',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -1.5,
      urgencia: 'urgente',
      cantidadSocios: 2,
      reglamentos_respaldantes: [
        'Reglamento de Faltas Internas Art. 4',
        'Reglamento General de Miembros'
      ],
      sociosInvolucrados: [
        { id: '10', legajo: '74907', nombre: 'Lucas Gastiaburu', grupo: '59' },
        { id: '11', legajo: '74908', nombre: 'Ana Gómez', grupo: '60' }
      ]
    };

    beforeEach(() => {
      api = TestBed.inject(ExpedienteApiService);
      router = TestBed.inject(Router);
      spyOn(authService, 'tieneRol').and.returnValue(true);
    });

    it('debe renderizar la cabecera con Exp: <n>/<YYYY>, título centrado y botón de cierre', () => {
      component.abrirDetalle(expBase);
      fixture.detectChanges();

      const modal = fixture.nativeElement.querySelector('.modal-backdrop-custom');
      expect(modal).toBeTruthy();

      const badgeExp = modal.querySelector('.modal-badge-exp');
      expect(badgeExp).toBeTruthy();
      expect(badgeExp.textContent.trim()).toBe('Exp: 1/2026');

      const titulo = modal.querySelector('.modal-titulo-central h4');
      expect(titulo).toBeTruthy();
      expect(titulo.textContent.trim()).toBe('Inasistencia a plenaria');

      const btnClose = modal.querySelector('.btn-close-modal');
      expect(btnClose).toBeTruthy();
      spyOn(component, 'cerrarModales');
      btnClose.click();
      expect(component.cerrarModales).toHaveBeenCalled();
    });

    it('debe renderizar metadatos, motivo en recuadro destacado y reglamentación con toggle', () => {
      component.abrirDetalle(expBase);
      fixture.detectChanges();

      const modal = fixture.nativeElement.querySelector('.modal-backdrop-custom');
      expect(modal.textContent).toContain('Estado:');
      expect(modal.textContent).toContain('En Revisión');
      expect(modal.textContent).toContain('Urgencia:');
      expect(modal.textContent).toContain('Urgente');
      expect(modal.textContent).toContain('Puntaje Solicitado:');
      expect(modal.textContent).toContain('-1.5');
      expect(modal.textContent).toContain('Fecha de Solicitud:');
      expect(modal.textContent).toContain('01/03/2026');
      expect(modal.textContent).toContain('Solicitante:');

      // Motivo destacado
      const motivoBox = modal.querySelector('.motivo-box');
      expect(motivoBox).toBeTruthy();
      expect(motivoBox.textContent).toContain('Inasistencia no justificada a reunión plenaria');

      // Reglamentación múltiple con toggle
      const toggleBtn = modal.querySelector('.toggle-reglamento-btn');
      expect(toggleBtn).toBeTruthy();
      expect(component.reglamentacionExpandida).toBeFalse();

      toggleBtn.click();
      fixture.detectChanges();
      expect(component.reglamentacionExpandida).toBeTrue();
      expect(modal.textContent).toContain('Reglamento General de Miembros');

      toggleBtn.click();
      fixture.detectChanges();
      expect(component.reglamentacionExpandida).toBeFalse();
    });

    it('debe mostrar tabla de involucrados con 6 columnas y formatear nombres y grupos', () => {
      spyOn(api, 'obtenerDetalleExpediente').and.returnValue(of({
        id: 201,
        numero: 'EXP-001/2026',
        estado: 'revision_resolucion',
        socios: [
          { id: 10, legajo: '74907', nombre: 'Lucas Gastiaburu', first_name: 'Lucas', last_name: 'Gastiaburu', grupo: '59' },
          { id: 11, legajo: '74908', nombre: 'Ana Gómez', first_name: 'Ana', last_name: 'Gómez', grupo: '60' }
        ],
        descargos: []
      }));

      component.abrirDetalle(expBase);
      fixture.detectChanges();

      const tabla = fixture.nativeElement.querySelector('.tabla-involucrados');
      expect(tabla).toBeTruthy();

      const ths = Array.from(tabla.querySelectorAll('thead th')).map((el: any) => el.textContent.trim());
      expect(ths).toContain('N° de Socio');
      expect(ths).toContain('Nombre Completo');
      expect(ths).toContain('Grupo');
      expect(ths).toContain('Estado de Descargo');
      expect(ths).toContain('Puntaje Final');

      const filas = tabla.querySelectorAll('tbody tr');
      expect(filas.length).toBe(2);

      const fila1 = component.involucradosJustificacion[0];
      expect(component.getNombreCompletoInvolucrado(fila1)).toBe('Lucas Gastiaburu');
      expect(component.formatGrupoInvolucrado(fila1.grupo)).toBe('59');
      expect(component.getEstadoDescargo(fila1)).toBe('Sin descargo');
      expect(component.getPuntajeFinalInvolucrado(fila1)).toBe(-1.5);
    });

    it('debe calcular correctamente Estado de Descargo (Leído, No Leído, Sin descargo) y Puntaje Final', () => {
      const filaSinDescargo: InvolucradoJustificacion = {
        socioId: 1,
        legajo: '1',
        nombre: 'Juan',
        apellido: 'Pérez',
        grupo: '59',
        descargo: null
      };
      expect(component.getEstadoDescargo(filaSinDescargo)).toBe('Sin descargo');

      const filaNoLeido: InvolucradoJustificacion = {
        socioId: 2,
        legajo: '2',
        nombre: 'Pedro',
        apellido: 'Gómez',
        grupo: '59',
        descargo: { id: 1, tipo: 'T02_CERTIFICADO', leido: false, puntaje_ratificado: null } as any
      };
      expect(component.getEstadoDescargo(filaNoLeido)).toBe('No Leído');

      const filaLeido: InvolucradoJustificacion = {
        socioId: 3,
        legajo: '3',
        nombre: 'María',
        apellido: 'López',
        grupo: '59',
        descargo: { id: 2, tipo: 'T02_CERTIFICADO', leido: true, puntaje_ratificado: 0 } as any
      };
      expect(component.getEstadoDescargo(filaLeido)).toBe('Leído');
      expect(component.getPuntajeFinalInvolucrado(filaLeido)).toBe(0);

      const filaRatificado: InvolucradoJustificacion = {
        socioId: 4,
        legajo: '4',
        nombre: 'Carlos',
        apellido: 'Ruiz',
        grupo: '59',
        descargo: { id: 3, tipo: 'T03_EXTRAORDINARIO', leido: true, puntaje_ratificado: -1.5 } as any
      };
      expect(component.getPuntajeFinalInvolucrado(filaRatificado)).toBe(-1.5);
    });

    it('debe controlar la visibilidad del botón Generar Resolución según el estado y si todos los descargos están leídos', () => {
      // Caso 1: Estado no es revision_resolucion ni espera_resolucion
      component.expedienteSeleccionado = { ...expBase, estado: 'justificando' };
      component.involucradosJustificacion = [];
      expect(component.puedeGenerarResolucion).toBeFalse();

      // Caso 2: Estado revision_resolucion pero hay un descargo No Leído
      component.expedienteSeleccionado = { ...expBase, estado: 'revision_resolucion' };
      component.involucradosJustificacion = [
        {
          socioId: 10,
          legajo: '74907',
          nombre: 'Lucas',
          apellido: 'Gastiaburu',
          grupo: '59',
          descargo: { id: 1, tipo: 'T02_CERTIFICADO', leido: false } as any
        }
      ];
      expect(component.todosLosDescargosVistos).toBeFalse();
      expect(component.puedeGenerarResolucion).toBeFalse();

      // Caso 3: Estado revision_resolucion y todos los descargos están en Leído (o sin descargo)
      component.involucradosJustificacion = [
        {
          socioId: 10,
          legajo: '74907',
          nombre: 'Lucas',
          apellido: 'Gastiaburu',
          grupo: '59',
          descargo: { id: 1, tipo: 'T02_CERTIFICADO', leido: true } as any
        },
        {
          socioId: 11,
          legajo: '74908',
          nombre: 'Ana',
          apellido: 'Gómez',
          grupo: '60',
          descargo: null
        }
      ];
      expect(component.todosLosDescargosVistos).toBeTrue();
      expect(component.puedeGenerarResolucion).toBeTrue();

      component.modalDetalleAbierto = true;
      fixture.detectChanges();
      const btnGenerar = fixture.nativeElement.querySelector('.btn-generar-resolucion');
      expect(btnGenerar).toBeTruthy();
      spyOn(component, 'abrirVotacion');
      btnGenerar.click();
      expect(component.abrirVotacion).toHaveBeenCalledWith(component.expedienteSeleccionado);
    });

    it('debe mostrar y accionar Firmar Resolución cuando el estado es pendiente_firma', () => {
      component.expedienteSeleccionado = { ...expBase, estado: 'pendiente_firma' };
      component.modalDetalleAbierto = true;
      fixture.detectChanges();

      expect(component.puedeFirmarResolucion).toBeTrue();
      const btnFirmar = fixture.nativeElement.querySelector('.btn-firmar-resolucion');
      expect(btnFirmar).toBeTruthy();
      spyOn(component, 'abrirFirma');
      btnFirmar.click();
      expect(component.abrirFirma).toHaveBeenCalledWith(component.expedienteSeleccionado);
    });

    it('debe mostrar Ver Resolución en emitido y pendiente_correos y abrir modalResolucionAbierto', () => {
      component.expedienteSeleccionado = { ...expBase, estado: 'emitido' };
      component.modalDetalleAbierto = true;
      fixture.detectChanges();

      expect(component.puedeVerResolucion).toBeTrue();
      const btnVer = fixture.nativeElement.querySelector('.btn-ver-resolucion');
      expect(btnVer).toBeTruthy();

      btnVer.click();
      fixture.detectChanges();

      expect(component.modalResolucionAbierto).toBeTrue();
      const modalResolucion = fixture.nativeElement.querySelector('.modal-resolucion-backdrop');
      expect(modalResolucion).toBeTruthy();
    });

    it('al hacer clic en Ver Descargo debe abrir el modal de descargo sin navegar y sin mutar localmente No Leído a Leído', () => {
      spyOn(router, 'navigate');
      const fila: InvolucradoJustificacion = {
        socioId: 10,
        legajo: '74907',
        nombre: 'Lucas',
        apellido: 'Gastiaburu',
        grupo: '59',
        descargo: { id: 1, tipo: 'T02_CERTIFICADO', leido: false } as any
      };
      component.expedienteSeleccionado = expBase;
      component.involucradosJustificacion = [fila];
      component.modalDetalleAbierto = true;
      fixture.detectChanges();

      const btnDescargo = fixture.nativeElement.querySelector('.btn-ver-descargo');
      expect(btnDescargo).toBeTruthy();

      btnDescargo.click();

      expect(router.navigate).not.toHaveBeenCalled();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.modalDescargoAbierto).toBeTrue();
      expect(component.involucradoSeleccionado).toBe(fila);
      // No debe haber mutado a true por el clic
      expect(fila.descargo!.leido).toBeFalse();

      component.volverADetalleDesdeDescargo();
      expect(component.modalDescargoAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
    });
  });

  describe('Filtros en una sola línea y Urgencia sin símbolos', () => {
    const expMock: Expediente = {
      id: '1',
      numero: 'EXP-001/2026',
      socio: 'Lucas Gastiaburu'
    } as any;
    it('debe tener opción "Todos" en los desplegables de estado y urgencia', () => {
      expect(component.estadosDisponibles[0].label).toBe('Todos');
      expect(component.urgenciasDisponibles[0].label).toBe('Todos');
    });

    it('debe inicializar filtroFechaDesde con el año en curso para optimizar el rendimiento inicial', () => {
      expect(component.filtroFechaDesde).toBe(`${new Date().getFullYear()}-01-01`);
    });

    it('en la vista de tabla, debe renderizar la urgencia en texto plano sin iconos ni caracteres extra', () => {
      component.vistaActual = 'tabla';
      fixture.detectChanges();

      const tabla = fixture.nativeElement.querySelector('.explorer-table-container');
      expect(tabla).toBeTruthy();
      const badgeUrgencia = tabla.querySelector('tbody td .badge-mat');
      if (badgeUrgencia) {
        expect(badgeUrgencia.querySelector('i')).toBeNull();
        const texto = badgeUrgencia.textContent.trim();
        expect(['Baja', 'Normal', 'Urgente']).toContain(texto);
      }
    });

    it('la barra de filtros debe contener el input de búsqueda sin etiqueta y los botones con flex-shrink-0', () => {
      const inputBusqueda = fixture.nativeElement.querySelector('#filtro-socio');
      expect(inputBusqueda).toBeTruthy();
      expect(inputBusqueda.getAttribute('placeholder')).toContain('Buscar por socio');

      const labelSocio = fixture.nativeElement.querySelector('label[for="filtro-socio"]');
      expect(labelSocio).toBeNull();

      const contenedorAcciones = fixture.nativeElement.querySelector('.filtro-acciones');
      expect(contenedorAcciones).toBeTruthy();
      expect(contenedorAcciones.classList.contains('flex-shrink-0')).toBeTrue();
    });
    it('debe navegar al visor de sustanciación al invocar abrirVisor', () => {
      const router = TestBed.inject(Router);
      const navigateSpy = spyOn(router, 'navigate');

      component.abrirVisor(expMock);
      expect(navigateSpy).toHaveBeenCalledWith(['/gestionar-expedientes', expMock.id, 'visor']);
    });

    it('debe renderizar el botón Sustanciar / Visor en el modal de detalle', () => {
      component.abrirDetalle(expMock);
      fixture.detectChanges();

      const compiled = fixture.nativeElement as HTMLElement;
      const btnVisor = compiled.querySelector('.modal-backdrop-custom .card-footer button[title="Sustanciar / Visor"]');
      expect(btnVisor).toBeTruthy();
    });

  });
});

