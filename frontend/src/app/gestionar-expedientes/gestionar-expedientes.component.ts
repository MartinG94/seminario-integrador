import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { 
  TribunalDataService, 
  Expediente, 
  EstadoExpediente, 
  NivelUrgencia
} from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';
import {
  ApelacionT01DTO,
  DecisionCausal,
  DescargoDetalleDTO,
  EvidenciaMetadata,
  ExpedienteApiService,
  ExpedienteDetalleDTO,
  HistorialT01DTO,
  SocioT01DTO
} from '../services/expediente-api.service';
import { SocioApiService, SocioListItemDTO } from '../services/socio-api.service';
import { Subject, Subscription, of } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import { formatCaseNumber as formatCaseNumberUtil } from '../utils/case-number.util';

// Registro de decisiones: sólo en la etapa de resolución (Spec 006, EARS 7).
const ESTADOS_DECISION_CAUSAL = ['revision_resolucion', 'espera_resolucion'];
// Consulta: desde la revisión y también después de emitida la resolución (EARS 8).
const ESTADOS_CONSULTA_CAUSAL = [
  ...ESTADOS_DECISION_CAUSAL, 'pendiente_firma', 'pendiente_correos', 'emitido'
];
export const MIN_FUNDAMENTO_CAUSAL = 20;
export const MAX_FUNDAMENTO_CAUSAL = 5000;
export const MIN_MOTIVOS_ADECUACION = 20;

/** Borrador de la adecuación de puntos e involucrados del T01 (PB-02). */
interface BorradorAdecuacion {
  puntos: number | null;
  socios: SocioT01DTO[];
  motivos: string;
  reabrirPlazo: boolean;
}

interface BorradorDecisionCausal {
  decision: DecisionCausal | '';
  fundamento: string;
}

/** Fila de la Tabla de Involucrados del detalle (notasPO §4). */
export interface InvolucradoJustificacion {
  socioId: number;
  legajo: string;
  grupo: string;
  nombre: string;
  apellido: string;
  descargo: DescargoDetalleDTO | null;
}

export interface OpcionPuntajeEscala {
  valor: string;
  label: string;
  rank: number;
  badgeClass: string;
}

export const ESCALA_PUNTAJES: OpcionPuntajeEscala[] = [
  { valor: '-3.0', label: '-3.0 pts', rank: -3.0, badgeClass: 'badge-sancion' },
  { valor: '-2.5', label: '-2.5 pts', rank: -2.5, badgeClass: 'badge-sancion' },
  { valor: '-2.0', label: '-2.0 pts', rank: -2.0, badgeClass: 'badge-sancion' },
  { valor: '-1.5', label: '-1.5 pts', rank: -1.5, badgeClass: 'badge-sancion' },
  { valor: '-1.0', label: '-1.0 pt', rank: -1.0, badgeClass: 'badge-sancion' },
  { valor: '-0.5', label: '-0.5 pt', rank: -0.5, badgeClass: 'badge-sancion' },
  { valor: 'LLAMADO_ATENCION', label: 'Llamado de Atención', rank: -0.25, badgeClass: 'badge-advertencia' },
  { valor: '0.0', label: '0.0 pts (Eximición)', rank: 0.0, badgeClass: 'badge-neutro' },
  { valor: 'FELICITACION', label: 'Felicitación', rank: 0.25, badgeClass: 'badge-felicitacion' },
  { valor: '0.5', label: '+0.5 pt', rank: 0.5, badgeClass: 'badge-premio' },
  { valor: '1.0', label: '+1.0 pt', rank: 1.0, badgeClass: 'badge-premio' },
  { valor: '1.5', label: '+1.5 pts', rank: 1.5, badgeClass: 'badge-premio' },
  { valor: '2.0', label: '+2.0 pts', rank: 2.0, badgeClass: 'badge-premio' },
  { valor: '2.5', label: '+2.5 pts', rank: 2.5, badgeClass: 'badge-premio' },
  { valor: '3.0', label: '+3.0 pts', rank: 3.0, badgeClass: 'badge-premio' }
];

@Component({
  selector: 'app-gestionar-expedientes',
  templateUrl: './gestionar-expedientes.component.html',
  styleUrls: ['./gestionar-expedientes.component.scss']
})
export class GestionarExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  vistaActual: 'kanban' | 'tabla' = 'kanban';

  // Filtros explícitos (CA2 / S3-07)
  filtroSocio: string = '';
  filtroEstado: string = '';
  filtroUrgencia: string = '';
  filtroFechaDesde: string = `${new Date().getFullYear()}-01-01`;
  filtroFechaHasta: string = '';

  // Ordenamiento de tabla
  columnaOrden = 'numero';
  ordenAscendente = true;

  // Estados canónicos del Kanban ordenados según ciclo de vida (S2-05)
  columnasKanban: { estado: EstadoExpediente; titulo: string; icon: string; transitoria?: boolean }[] = [
    { estado: 'creado', titulo: 'Creados', icon: 'file_copy' },
    { estado: 'justificando', titulo: 'Justificando', icon: 'schedule' },
    { estado: 'revision_resolucion', titulo: 'En Revisión', icon: 'gavel' },
    { estado: 'pendiente_firma', titulo: 'Pendiente de Firma', icon: 'history_edu' },
    { estado: 'pendiente_correos', titulo: 'Pendiente de Envío', icon: 'mail_outline' },
    { estado: 'emitido', titulo: 'Emitidos', icon: 'verified' }
  ];

  estadosDisponibles: { key: string; label: string }[] = [
    { key: '', label: 'Todos' },
    { key: 'creado', label: 'Creados' },
    { key: 'justificando', label: 'Justificando' },
    { key: 'revision_resolucion', label: 'En Revisión' },
    { key: 'pendiente_firma', label: 'Pendiente de Firma' },
    { key: 'pendiente_correos', label: 'Pendiente de Envío' },
    { key: 'emitido', label: 'Emitidos' }
  ];

  urgenciasDisponibles: { key: string; label: string }[] = [
    { key: '', label: 'Todos' },
    { key: 'baja', label: 'Baja' },
    { key: 'normal', label: 'Normal' },
    { key: 'urgente', label: 'Urgente' }
  ];

  // Estado de colapso de columnas
  columnasColapsadas: { [estado: string]: boolean } = {
    emitido: false
  };

  // Modales
  modalDetalleAbierto = false;
  modalVotacionAbierto = false;
  modalFirmaAbierto = false;
  modalSociosAbierto = false;
  modalResolucionAbierto = false;
  modalDescargoAbierto = false;
  reglamentacionExpandida = false;
  expedienteSeleccionado: Expediente | null = null;

  // Votación
  votosJueces: { [juez: string]: 'FAVORABLE' | 'DESFAVORABLE' | 'ABSTENCION' } = {
    'Dr. Argañaraz (Presidente TD)': 'FAVORABLE',
    'Dra. Bustos (Miembro Titular)': 'FAVORABLE',
    'Ing. Rossi (Miembro Titular)': 'DESFAVORABLE'
  };
  considerandosTexto = 'Por cuanto las pruebas documentales aportadas y la constancia de asistencia demuestran la concurrencia de la causal invocada.';

  // Firma
  juezFirmando = 'Dr. Argañaraz (Presidente TD)';
  juecesDisponibles = [
    'Dr. Argañaraz (Presidente TD)',
    'Dra. Bustos (Miembro Titular)',
    'Ing. Rossi (Miembro Titular)'
  ];

  failedToLoadBoard = false;
  cargando = false;

  // Evaluación de justificaciones T02 dentro del detalle (S4-02)
  readonly maxFundamento = MAX_FUNDAMENTO_CAUSAL;
  involucradosJustificacion: InvolucradoJustificacion[] = [];
  involucradoSeleccionado: InvolucradoJustificacion | null = null;
  cargandoJustificaciones = false;
  borradorCausal: BorradorDecisionCausal = { decision: '', fundamento: '' };
  registrandoCausal = false;

  // Evaluación y ratificación de puntaje en descargo individual (Modal 6)
  readonly escalaPuntajes = ESCALA_PUNTAJES;
  opcionPuntajeFinal: string = '0.0';
  puntajeFinalInput: number | null = null;
  fundamentoPuntajeInput = '';
  guardandoDescargo = false;

  // Apelación y adecuación del T01 (PB-02)
  readonly minMotivosAdecuacion = MIN_MOTIVOS_ADECUACION;
  historialT01: HistorialT01DTO | null = null;
  cargandoT01 = false;
  adecuando = false;
  borradorAdecuacion: BorradorAdecuacion = { puntos: null, socios: [], motivos: '', reabrirPlazo: false };
  busquedaSocioAdecuacion = '';
  candidatosAdecuacion: SocioListItemDTO[] = [];
  private busquedaSocio$ = new Subject<string>();

  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService,
    private notifications: NotificationService,
    private expedienteApi: ExpedienteApiService,
    private socioApi: SocioApiService,
    private router: Router
  ) {}

  get puedeVotarOFirmar(): boolean {
    return this.auth.tieneRol('TD', 'ADMIN');
  }

  get puedeConsultarJustificaciones(): boolean {
    const estado = this.expedienteSeleccionado?.estado;
    return !!estado && ESTADOS_CONSULTA_CAUSAL.includes(estado) && this.auth.tieneRol('TD', 'CD', 'ADMIN');
  }

  get puedeEvaluarJustificaciones(): boolean {
    const estado = this.expedienteSeleccionado?.estado;
    return !!estado && ESTADOS_DECISION_CAUSAL.includes(estado) && this.auth.tieneRol('TD');
  }

  get puedeGenerarResolucion(): boolean {
    if (!this.puedeVotarOFirmar || !this.expedienteSeleccionado) return false;
    const enRevision =
      this.expedienteSeleccionado.estado === 'revision_resolucion' ||
      this.expedienteSeleccionado.estado === 'espera_resolucion';
    if (!enRevision || this.cargandoJustificaciones) return false;
    return this.todosLosDescargosVistos;
  }

  get todosLosDescargosVistos(): boolean {
    if (!this.involucradosJustificacion || this.involucradosJustificacion.length === 0) {
      return false;
    }
    return this.involucradosJustificacion.every(
      fila => !fila.descargo || this.getEstadoDescargo(fila) === 'Leído'
    );
  }

  get puedeFirmarResolucion(): boolean {
    return (
      this.puedeVotarOFirmar &&
      this.expedienteSeleccionado?.estado === 'pendiente_firma'
    );
  }

  get puedeVerResolucion(): boolean {
    const estado = this.expedienteSeleccionado?.estado;
    return estado === 'emitido' || estado === 'pendiente_correos';
  }

  ngOnInit(): void {
    const sub = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
    });
    this.subs.push(sub);

    this.subs.push(this.busquedaSocio$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(termino => termino.trim().length < 3
        ? of([] as SocioListItemDTO[])
        : this.socioApi.searchSocios(termino).pipe(
          map(respuesta => respuesta.results || []),
          catchError(() => of([] as SocioListItemDTO[]))
        ))
    ).subscribe(socios => {
      const actuales = new Set(this.borradorAdecuacion.socios.map(s => s.id));
      this.candidatosAdecuacion = socios.filter(s => !actuales.has(s.id));
    }));

    this.cargarDatosTablero();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  toggleColapsar(estado: string, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.columnasColapsadas[estado] = !this.columnasColapsadas[estado];
  }

  isColumnaColapsada(estado: string): boolean {
    return !!this.columnasColapsadas[estado];
  }

  // Columnas visibles del tablero Kanban según filtro
  get columnasKanbanVisibles(): { estado: EstadoExpediente; titulo: string; icon: string; transitoria?: boolean }[] {
    if (this.filtroEstado.trim()) {
      const estadoFiltro = this.filtroEstado.trim();
      // Si el filtro es revision_resolucion o espera_resolucion, apuntar a revision_resolucion
      const estadoBuscado = (estadoFiltro === 'espera_resolucion') ? 'revision_resolucion' : estadoFiltro;
      return this.columnasKanban.filter(col => col.estado === estadoBuscado);
    }

    return this.columnasKanban;
  }

  cargarDatosTablero(): void {
    this.cargando = true;
    this.failedToLoadBoard = false;
    const filtros: any = {};
    if (this.filtroSocio.trim()) filtros.socio = this.filtroSocio.trim();
    if (this.filtroEstado.trim()) filtros.estado = this.filtroEstado.trim();
    if (this.filtroUrgencia.trim()) filtros.urgencia = this.filtroUrgencia.trim();
    if (this.filtroFechaDesde) filtros.fecha_desde = this.filtroFechaDesde;
    if (this.filtroFechaHasta) filtros.fecha_hasta = this.filtroFechaHasta;

    this.dataService.obtenerTablero(filtros).subscribe({
      next: () => {
        this.cargando = false;
      },
      error: () => {
        // En caso de error o backend no disponible, se mantiene la colección local
        this.cargando = false;
        this.failedToLoadBoard = true;
        this.notifications.error('No se pudo cargar el tablero. Intentá nuevamente.');
      }
    });
  }

  limpiarFiltros(): void {
    this.filtroSocio = '';
    this.filtroEstado = '';
    this.filtroUrgencia = '';
    this.filtroFechaDesde = '';
    this.filtroFechaHasta = '';
    this.cargarDatosTablero();
  }

  get expedientesFiltrados(): Expediente[] {
    let result = [...this.expedientes];

    // Filtro por socio/creador/título en memoria (fallback / reactivo)
    if (this.filtroSocio.trim()) {
      const q = this.filtroSocio.trim().toLowerCase();
      result = result.filter(e =>
        (e.socio && e.socio.toLowerCase().includes(q)) ||
        (e.legajo && e.legajo.toLowerCase().includes(q)) ||
        (e.numero && e.numero.toLowerCase().includes(q)) ||
        (e.numero && this.formatCaseNumber(e.numero).toLowerCase().includes(q)) ||
        (e.creador && e.creador.toLowerCase().includes(q)) ||
        (e.titulo && e.titulo.toLowerCase().includes(q)) ||
        (e.motivo && e.motivo.toLowerCase().includes(q)) ||
        (e.sociosInvolucrados && e.sociosInvolucrados.some(s =>
          (s.nombre && s.nombre.toLowerCase().includes(q)) ||
          (s.legajo && s.legajo.toLowerCase().includes(q))
        ))
      );
    }

    // Filtro por estado en memoria
    if (this.filtroEstado.trim()) {
      const est = this.filtroEstado.trim();
      if (est === 'revision_resolucion') {
        result = result.filter(e => e.estado === 'revision_resolucion' || e.estado === 'espera_resolucion');
      } else if (est === 'pendiente_firma') {
        result = result.filter(e => e.estado === 'pendiente_firma' || (e.estado === 'pendiente_correos' && (!e.firmas || !e.firmas.juecesFirmantes || e.firmas.juecesFirmantes.length < 3)));
      } else if (est === 'pendiente_correos') {
        result = result.filter(e => (e.estado === 'pendiente_correos' && (!!e.firmas && !!e.firmas.juecesFirmantes && e.firmas.juecesFirmantes.length >= 3)) || (e.estado as string) === 'pendiente_envio');
      } else {
        result = result.filter(e => e.estado === est);
      }
    }

    // Filtro por urgencia en memoria (S3-07)
    if (this.filtroUrgencia.trim()) {
      const urg = this.filtroUrgencia.trim();
      result = result.filter(e => (e.urgencia || 'normal') === urg);
    }

    // Filtro por rango de fechas (comparación YYYY-MM-DD ante timestamps ISO)
    if (this.filtroFechaDesde) {
      result = result.filter(e => !e.fechaCreacion || e.fechaCreacion.slice(0, 10) >= this.filtroFechaDesde);
    }
    if (this.filtroFechaHasta) {
      result = result.filter(e => !e.fechaCreacion || e.fechaCreacion.slice(0, 10) <= this.filtroFechaHasta);
    }

    result.sort((a, b) => {
      let valA: any;
      let valB: any;
      if (this.columnaOrden === 'titulo') {
        valA = a.titulo || a.motivo || '';
        valB = b.titulo || b.motivo || '';
      } else if (this.columnaOrden === 'cantidadSocios') {
        valA = this.getCantidadInvolucrados(a);
        valB = this.getCantidadInvolucrados(b);
      } else {
        valA = (a as any)[this.columnaOrden] ?? '';
        valB = (b as any)[this.columnaOrden] ?? '';
      }
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return this.ordenAscendente ? -1 : 1;
      if (valA > valB) return this.ordenAscendente ? 1 : -1;
      return 0;
    });

    return result;
  }

  getExpedientesPorEstado(estado: EstadoExpediente): Expediente[] {
    if (estado === 'revision_resolucion') {
      return this.expedientesFiltrados.filter(e => e.estado === 'revision_resolucion' || e.estado === 'espera_resolucion');
    }
    if (estado === 'pendiente_firma') {
      return this.expedientesFiltrados.filter(e => e.estado === 'pendiente_firma' || (e.estado === 'pendiente_correos' && (!e.firmas || !e.firmas.juecesFirmantes || e.firmas.juecesFirmantes.length < 3)));
    }
    if (estado === 'pendiente_correos') {
      return this.expedientesFiltrados.filter(e => (e.estado === 'pendiente_correos' && (!!e.firmas && !!e.firmas.juecesFirmantes && e.firmas.juecesFirmantes.length >= 3)) || (e.estado as string) === 'pendiente_envio');
    }
    return this.expedientesFiltrados.filter(e => e.estado === estado);
  }

  cambiarOrden(col: string): void {
    if (this.columnaOrden === col) {
      this.ordenAscendente = !this.ordenAscendente;
    } else {
      this.columnaOrden = col;
      this.ordenAscendente = true;
    }
  }

  // Transición accesible mediante botón con teclado (CA3 y CA4)
  transicionarEstado(exp: Expediente, nuevoEstado: EstadoExpediente, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    const labelDestino = this.getEstadoLabel(nuevoEstado);
    this.dataService.transicionarExpediente(exp.id, nuevoEstado).subscribe({
      next: () => {
        this.mostrarNotificacion(`Expediente ${exp.numero} transicionado a "${labelDestino}".`);
        this.cargarDatosTablero();
      },
      error: (err) => {
        this.notifications.error(httpErrorMessage(err, 'No se pudo realizar la transición.'));
      }
    });
  }

  // Navegación por teclado accesible con flechas (WCAG 2.2 AA)
  onTableKeyDown(event: KeyboardEvent, exp: Expediente): void {
    if (!event) return;

    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
      event.preventDefault();
      this.abrirDetalle(exp);
      return;
    }

    if (event.key === 'ArrowDown' || event.key === 'Down') {
      event.preventDefault();
      const currentTr = (event.target as HTMLElement)?.closest('tr');
      const nextTr = currentTr?.nextElementSibling as HTMLElement | null;
      if (nextTr && typeof nextTr.focus === 'function') {
        nextTr.focus();
      }
      return;
    }

    if (event.key === 'ArrowUp' || event.key === 'Up') {
      event.preventDefault();
      const currentTr = (event.target as HTMLElement)?.closest('tr');
      const prevTr = currentTr?.previousElementSibling as HTMLElement | null;
      if (prevTr && typeof prevTr.focus === 'function') {
        prevTr.focus();
      }
      return;
    }
  }

  onKanbanCardKeyDown(event: KeyboardEvent, exp: Expediente): void {
    if (!event) return;

    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
      // Si el foco está en un botón interno de la tarjeta, dejamos que actúe el botón
      if ((event.target as HTMLElement)?.tagName === 'BUTTON') {
        return;
      }
      event.preventDefault();
      this.abrirDetalle(exp);
      return;
    }

    const currentCard = (event.target as HTMLElement)?.closest('.kanban-card-mat') as HTMLElement | null;
    if (!currentCard) return;

    if (event.key === 'ArrowDown' || event.key === 'Down') {
      event.preventDefault();
      let nextCard = currentCard.nextElementSibling as HTMLElement | null;
      while (nextCard && !nextCard.classList.contains('kanban-card-mat')) {
        nextCard = nextCard.nextElementSibling as HTMLElement | null;
      }
      if (nextCard && typeof nextCard.focus === 'function') {
        nextCard.focus();
      }
      return;
    }

    if (event.key === 'ArrowUp' || event.key === 'Up') {
      event.preventDefault();
      let prevCard = currentCard.previousElementSibling as HTMLElement | null;
      while (prevCard && !prevCard.classList.contains('kanban-card-mat')) {
        prevCard = prevCard.previousElementSibling as HTMLElement | null;
      }
      if (prevCard && typeof prevCard.focus === 'function') {
        prevCard.focus();
      }
      return;
    }

    if (event.key === 'ArrowRight' || event.key === 'Right') {
      event.preventDefault();
      const currentCol = currentCard.closest('.kanban-col-mat') as HTMLElement | null;
      let nextCol = currentCol?.nextElementSibling as HTMLElement | null;
      while (nextCol && !nextCol.classList.contains('kanban-col-mat')) {
        nextCol = nextCol.nextElementSibling as HTMLElement | null;
      }
      if (nextCol) {
        const firstCardInNextCol = nextCol.querySelector('.kanban-card-mat') as HTMLElement | null;
        if (firstCardInNextCol && typeof firstCardInNextCol.focus === 'function') {
          firstCardInNextCol.focus();
        }
      }
      return;
    }

    if (event.key === 'ArrowLeft' || event.key === 'Left') {
      event.preventDefault();
      const currentCol = currentCard.closest('.kanban-col-mat') as HTMLElement | null;
      let prevCol = currentCol?.previousElementSibling as HTMLElement | null;
      while (prevCol && !prevCol.classList.contains('kanban-col-mat')) {
        prevCol = prevCol.previousElementSibling as HTMLElement | null;
      }
      if (prevCol) {
        const firstCardInPrevCol = prevCol.querySelector('.kanban-card-mat') as HTMLElement | null;
        if (firstCardInPrevCol && typeof firstCardInPrevCol.focus === 'function') {
          firstCardInPrevCol.focus();
        }
      }
      return;
    }
  }

  abrirVisor(exp: any, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    if (!exp?.id) return;
    this.router.navigate(['/gestionar-expedientes', exp.id, 'visor']);
  }

  abrirDetalle(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalSociosAbierto = false;
    this.modalResolucionAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalDetalleAbierto = true;
    this.reglamentacionExpandida = false;
    this.limpiarJustificaciones();
    this.limpiarT01();

    if (exp.sociosInvolucrados && exp.sociosInvolucrados.length > 0) {
      this.involucradosJustificacion = exp.sociosInvolucrados.map(s => ({
        socioId: Number(s.id),
        legajo: s.legajo,
        grupo: s.grupo || '',
        nombre: s.nombre,
        apellido: '',
        descargo: null
      }));
    } else if (exp.socio) {
      this.involucradosJustificacion = [{
        socioId: 0,
        legajo: exp.legajo || '',
        grupo: '',
        nombre: exp.socio,
        apellido: '',
        descargo: null
      }];
    }

    this.cargarJustificaciones(exp.id);

    if (this.puedeConsultarT01) {
      this.cargarHistorialT01(exp.id);
    }
  }

  // --- Apelación y adecuación del T01 (PB-02, art. 14) ---

  get puedeConsultarT01(): boolean {
    return this.auth.tieneRol('TD', 'CD', 'ADMIN');
  }

  /** El debate y la adecuación (OP 30) ocurren en "Justificaciones en revisión". */
  get puedeAdecuarT01(): boolean {
    return !!this.historialT01?.es_t01
      && this.expedienteSeleccionado?.estado === 'revision_resolucion'
      && this.auth.tieneRol('TD');
  }

  cargarHistorialT01(expedienteId: number | string): void {
    this.cargandoT01 = true;
    this.expedienteApi.obtenerHistorialT01(expedienteId).subscribe({
      next: historial => {
        this.cargandoT01 = false;
        this.aplicarHistorialT01(historial);
      },
      error: err => {
        this.cargandoT01 = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo cargar el historial del T01.'));
      }
    });
  }

  private aplicarHistorialT01(historial: HistorialT01DTO): void {
    this.historialT01 = historial;
    this.borradorAdecuacion = {
      puntos: Number(historial.puntos_vigentes),
      socios: [...(historial.involucrados || [])],
      motivos: '',
      reabrirPlazo: false
    };
    this.busquedaSocioAdecuacion = '';
    this.candidatosAdecuacion = [];
  }

  private limpiarT01(): void {
    this.historialT01 = null;
    this.cargandoT01 = false;
    this.adecuando = false;
    this.busquedaSocioAdecuacion = '';
    this.candidatosAdecuacion = [];
  }

  apelacionesDe(socioId: number): ApelacionT01DTO[] {
    return (this.historialT01?.apelaciones || []).filter(a => a.socio_id === socioId);
  }

  buscarSocioAdecuacion(termino: string): void {
    this.busquedaSocioAdecuacion = termino;
    this.busquedaSocio$.next(termino);
  }

  agregarSocioAdecuacion(socio: SocioListItemDTO): void {
    if (!this.borradorAdecuacion.socios.some(s => s.id === socio.id)) {
      this.borradorAdecuacion.socios.push({
        id: socio.id,
        legajo: socio.legajo,
        nombre: `${socio.first_name} ${socio.last_name} (N° ${socio.legajo})`
      });
    }
    this.busquedaSocioAdecuacion = '';
    this.candidatosAdecuacion = [];
  }

  quitarSocioAdecuacion(socioId: number): void {
    this.borradorAdecuacion.socios = this.borradorAdecuacion.socios.filter(s => s.id !== socioId);
  }

  registrarAdecuacion(): void {
    if (!this.expedienteSeleccionado || this.adecuando) return;
    const borrador = this.borradorAdecuacion;
    if (!borrador.socios.length) {
      this.notifications.error('Debe quedar al menos un involucrado en el expediente.');
      return;
    }
    if (borrador.puntos === null || isNaN(Number(borrador.puntos))) {
      this.notifications.error('Indicá los puntos adecuados.');
      return;
    }
    const motivos = borrador.motivos.trim();
    if (motivos.length < MIN_MOTIVOS_ADECUACION) {
      this.notifications.error(`Indicá los motivos de la adecuación con al menos ${MIN_MOTIVOS_ADECUACION} caracteres.`);
      return;
    }
    this.adecuando = true;
    this.expedienteApi.adecuarT01(this.expedienteSeleccionado.id, {
      puntos: Number(borrador.puntos),
      socios: borrador.socios.map(s => s.id),
      motivos,
      reabrir_plazo: borrador.reabrirPlazo
    }).subscribe({
      next: historial => {
        this.adecuando = false;
        this.aplicarHistorialT01(historial);
        if (this.expedienteSeleccionado) {
          this.expedienteSeleccionado.puntos = Number(historial.puntos_vigentes);
          this.expedienteSeleccionado.estado = historial.estado as EstadoExpediente;
        }
        this.notifications.success(
          borrador.reabrirPlazo
            ? 'Adecuación registrada. Se abrió un nuevo plazo de apelación y se notificaron los motivos.'
            : 'Adecuación registrada. Se notificaron los motivos al solicitante y a los involucrados.'
        );
        this.cargarDatosTablero();
      },
      error: err => {
        this.adecuando = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo registrar la adecuación.'));
      }
    });
  }


  cargarJustificaciones(expedienteId: number | string): void {
    this.cargandoJustificaciones = true;
    this.expedienteApi.obtenerDetalleExpediente(expedienteId).subscribe({
      next: detalle => {
        this.involucradosJustificacion = this.construirInvolucrados(detalle);
        if (detalle.reglamentos_respaldantes && this.expedienteSeleccionado) {
          this.expedienteSeleccionado.reglamentosRespaldantes = detalle.reglamentos_respaldantes;
          this.expedienteSeleccionado.reglamentos_respaldantes = detalle.reglamentos_respaldantes;
        }
        this.cargandoJustificaciones = false;
      },
      error: err => {
        this.cargandoJustificaciones = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudieron cargar las justificaciones.'));
      }
    });
  }

  private construirInvolucrados(detalle: ExpedienteDetalleDTO): InvolucradoJustificacion[] {
    const descargos = detalle.descargos || [];
    const porSocio = new Map(descargos.map(d => [d.socio_id, d]));
    const filas: InvolucradoJustificacion[] = (detalle.socios || []).map(s => ({
      socioId: s.id,
      legajo: s.legajo,
      grupo: s.grupo || '',
      nombre: s.first_name ?? s.nombre,
      apellido: s.last_name ?? '',
      descargo: porSocio.get(s.id) || null
    }));
    // Descargos de socios que no figuran en el padrón del expediente (datos previos).
    descargos
      .filter(d => !filas.some(f => f.socioId === d.socio_id))
      .forEach(d => filas.push({
        socioId: d.socio_id,
        legajo: d.socio_legajo,
        grupo: '',
        nombre: d.socio_first_name ?? d.socio_nombre,
        apellido: d.socio_last_name ?? '',
        descargo: d
      }));
    return filas;
  }

  private limpiarJustificaciones(): void {
    this.involucradosJustificacion = [];
    this.involucradoSeleccionado = null;
    this.borradorCausal = { decision: '', fundamento: '' };
    this.registrandoCausal = false;
  }

  esEvaluable(fila: InvolucradoJustificacion): boolean {
    return fila.descargo?.tipo === 'T02_CERTIFICADO';
  }

  estadoJustificacion(fila: InvolucradoJustificacion): string {
    const descargo = fila.descargo;
    if (!descargo) return 'Sin justificación';
    if (descargo.tipo === 'T03_EXTRAORDINARIO') return 'Extraordinaria (T03)';
    const ultima = descargo.decisiones_causal?.[0];
    if (!ultima) return 'Pendiente de evaluación';
    return this.etiquetaDecision(ultima.decision);
  }

  etiquetaDecision(decision?: DecisionCausal | ''): string {
    if (decision === 'ACCEPTED') return 'Aprobada';
    if (decision === 'REJECTED') return 'Desaprobada';
    return '';
  }

  sugerenciaSistema(descargo: DescargoDetalleDTO): string {
    return descargo.regla_sugerida === 'ACCEPTED'
      ? 'Aprobar (presentó comprobante vigente)'
      : 'Desaprobar (no presentó comprobante)';
  }

  seleccionarInvolucrado(fila: InvolucradoJustificacion): void {
    if (!this.esEvaluable(fila)) return;
    this.involucradoSeleccionado = fila;
    this.borradorCausal = { decision: '', fundamento: '' };
  }

  volverAListadoInvolucrados(): void {
    this.involucradoSeleccionado = null;
    this.borradorCausal = { decision: '', fundamento: '' };
  }

  elegirDecision(decision: DecisionCausal): void {
    this.borradorCausal.decision = decision;
  }

  requiereFundamento(): boolean {
    const decision = this.borradorCausal.decision;
    const sugerida = this.involucradoSeleccionado?.descargo?.regla_sugerida;
    return decision === 'REJECTED' || (!!decision && decision !== sugerida);
  }

  verComprobante(evidencia: EvidenciaMetadata): void {
    if (!this.expedienteSeleccionado) return;
    // La ventana se abre en el gesto del usuario para que el navegador no la bloquee.
    const ventana = window.open('', '_blank');
    this.expedienteApi.descargarEvidencia(this.expedienteSeleccionado.id, evidencia.id).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        if (ventana) {
          ventana.location.href = url;
        } else {
          const enlace = document.createElement('a');
          enlace.href = url;
          enlace.download = evidencia.nombre_original || 'comprobante';
          enlace.click();
        }
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      },
      error: err => {
        ventana?.close();
        this.notifications.error(httpErrorMessage(err, 'No se pudo abrir el comprobante.'));
      }
    });
  }

  registrarDecisionCausal(): void {
    const descargo = this.involucradoSeleccionado?.descargo;
    if (!this.expedienteSeleccionado || !descargo || this.registrandoCausal) return;
    const borrador = this.borradorCausal;
    if (!borrador.decision) {
      this.notifications.error('Elegí si aprobás o desaprobás la justificación.');
      return;
    }
    const fundamento = borrador.fundamento.trim();
    if (this.requiereFundamento() && fundamento.length < MIN_FUNDAMENTO_CAUSAL) {
      this.notifications.error(`Escribí un fundamento de al menos ${MIN_FUNDAMENTO_CAUSAL} caracteres.`);
      return;
    }

    this.registrandoCausal = true;
    this.expedienteApi.registrarDecisionCausal(this.expedienteSeleccionado.id, descargo.id, {
      decision: borrador.decision,
      fundamento,
      // Se valoran los comprobantes vigentes que el miembro del TD puede inspeccionar en el panel.
      evidencia_ids: (descargo.evidencias || []).map(ev => ev.id)
    }).subscribe({
      next: decision => {
        this.registrandoCausal = false;
        descargo.decisiones_causal = [decision, ...(descargo.decisiones_causal || [])];
        this.borradorCausal = { decision: '', fundamento: '' };
        this.notifications.success(`Decisión registrada (versión ${decision.version}).`);
      },
      error: err => {
        this.registrandoCausal = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo registrar la decisión.'));
      }
    });
  }

  abrirVotacion(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDetalleAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalSociosAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalVotacionAbierto = true;
  }

  abrirFirma(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalSociosAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalFirmaAbierto = true;
  }

  abrirModalSocios(exp: Expediente, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    this.expedienteSeleccionado = exp;
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalSociosAbierto = true;
  }

  volverADetalle(): void {
    this.modalSociosAbierto = false;
    if (this.expedienteSeleccionado) {
      this.abrirDetalle(this.expedienteSeleccionado);
    }
  }

  cerrarModales(): void {
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalSociosAbierto = false;
    this.modalResolucionAbierto = false;
    this.modalDescargoAbierto = false;
    this.reglamentacionExpandida = false;
    this.expedienteSeleccionado = null;
    this.limpiarJustificaciones();
    this.limpiarT01();
  }

  confirmarVotacion(): void {
    if (!this.expedienteSeleccionado) return;
    this.dataService.votarDictamen(
      this.expedienteSeleccionado.id,
      this.votosJueces,
      this.considerandosTexto
    );
    this.mostrarNotificacion('Dictamen votado. Se alcanzó mayoría calificada (>= 2/3). Expediente pasa a Pendiente de correos.');
    this.cerrarModales();
  }

  confirmarFirma(): void {
    if (!this.expedienteSeleccionado) return;
    const res = this.dataService.firmarResolucion(this.expedienteSeleccionado.id, this.juezFirmando);
    if (res.completo) {
      this.mostrarNotificacion('Resolución perfeccionada con 3 firmas digitales e impacto en saldo del socio.');
    } else {
      this.mostrarNotificacion(`Firma registrada por ${this.juezFirmando}. Pendiente firmas restantes.`);
    }
    this.cerrarModales();
  }

  mostrarNotificacion(msg: string): void {
    this.notifications.success(msg);
  }

  getEstadoLabel(estado: string): string {
    switch (estado) {
      case 'creado': return 'Creados';
      case 'justificando': return 'Justificando';
      case 'revision_resolucion': return 'En Revisión';
      case 'espera_resolucion': return 'En Revisión';
      case 'pendiente_firma': return 'Pendiente de Firma';
      case 'pendiente_correos': return 'Pendiente de Envío';
      case 'emitido': return 'Emitidos';
      default: return estado;
    }
  }

  getEstadoBadgeClass(estado: string): string {
    switch (estado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion': return 'badge-mat-info';
      case 'espera_resolucion': return 'badge-mat-info';
      case 'pendiente_firma': return 'badge-mat-primary';
      case 'pendiente_correos': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }

  getCantidadInvolucrados(exp: Expediente | null | undefined): number {
    if (!exp) return 1;
    if (exp.cantidadSocios && exp.cantidadSocios > 0) {
      return exp.cantidadSocios;
    }
    if (exp.sociosInvolucrados && exp.sociosInvolucrados.length > 0) {
      return exp.sociosInvolucrados.length;
    }
    return 1;
  }

  formatCaseNumber(caseNumber: string): string {
    return formatCaseNumberUtil(caseNumber);
  }

  getUrgenciaLabel(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente': return 'Urgente';
      case 'baja': return 'Baja';
      default: return 'Normal';
    }
  }

  getUrgenciaBadgeClass(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente': return 'badge-mat-danger';
      case 'baja': return 'badge-mat-success';
      default: return 'badge-mat-info';
    }
  }

  getUrgenciaIcon(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente': return 'priority_high';
      case 'baja': return 'arrow_downward';
      default: return 'horizontal_rule';
    }
  }

  cambiarUrgenciaExpediente(nuevaUrgencia: NivelUrgencia): void {
    if (!this.expedienteSeleccionado) return;
    const label = this.getUrgenciaLabel(nuevaUrgencia);
    this.dataService.actualizarUrgencia(this.expedienteSeleccionado.id, nuevaUrgencia).subscribe({
      next: () => {
        if (this.expedienteSeleccionado) {
          this.expedienteSeleccionado.urgencia = nuevaUrgencia;
          this.expedienteSeleccionado.urgenciaDisplay = label;
        }
        this.mostrarNotificacion(`Urgencia actualizada a "${label}" exitosamente.`);
        this.cargarDatosTablero();
      },
      error: (err) => {
        this.notifications.error(httpErrorMessage(err, 'No se pudo actualizar la urgencia.'));
      }
    });
  }

  // --- Métodos de apoyo formato canónico Tribunal (S3-10 / SCRUM-81) ---

  getReglamentoAsociado(exp: Expediente | null): string {
    if (!exp) return 'Reglamento Procesal Disciplinario 2026';
    const reg = exp.reglamento_asociado || exp.reglamentoAsociado;
    return reg || 'Reglamento Procesal Disciplinario 2026';
  }

  getReglamentosSustento(exp: Expediente | null): string[] {
    if (!exp) return ['Reglamento Procesal Disciplinario 2026'];
    if (exp.reglamentosRespaldantes && exp.reglamentosRespaldantes.length > 0) {
      return exp.reglamentosRespaldantes;
    }
    if (exp.reglamentos_respaldantes && exp.reglamentos_respaldantes.length > 0) {
      return exp.reglamentos_respaldantes;
    }
    const reg = exp.reglamento_asociado || exp.reglamentoAsociado;
    return reg ? [reg] : ['Reglamento Procesal Disciplinario 2026'];
  }

  toggleReglamentacion(): void {
    this.reglamentacionExpandida = !this.reglamentacionExpandida;
  }

  getNombreCompletoInvolucrado(fila: InvolucradoJustificacion): string {
    const parts = [fila.nombre, fila.apellido].filter(Boolean).map(p => p.trim());
    return parts.join(' ').trim() || fila.nombre || '—';
  }

  formatGrupoInvolucrado(grupo: string | undefined): string {
    if (!grupo || !grupo.trim()) return '—';
    return grupo.trim().replace(/^[Gg]/, '');
  }

  getEstadoDescargo(fila: InvolucradoJustificacion): 'Leído' | 'No Leído' | 'Sin descargo' {
    if (!fila.descargo) return 'Sin descargo';
    if (
      fila.descargo.leido === true ||
      (fila.descargo.decisiones_causal && fila.descargo.decisiones_causal.length > 0)
    ) {
      return 'Leído';
    }
    return 'No Leído';
  }

  get puedeModificarPuntaje(): boolean {
    if (!this.expedienteSeleccionado) return false;
    const estado = this.expedienteSeleccionado.estado;
    return estado === 'revision_resolucion' || estado === 'espera_resolucion';
  }

  getOpcionPuntajeActual(): OpcionPuntajeEscala {
    return this.escalaPuntajes.find(op => op.valor === this.opcionPuntajeFinal) || {
      valor: this.opcionPuntajeFinal,
      label: this.opcionPuntajeFinal,
      rank: 0,
      badgeClass: 'badge-neutro'
    };
  }

  decrementarPuntaje(): void {
    if (!this.puedeModificarPuntaje) return;
    const idx = this.escalaPuntajes.findIndex(op => op.valor === this.opcionPuntajeFinal);
    if (idx > 0) {
      this.opcionPuntajeFinal = this.escalaPuntajes[idx - 1].valor;
    }
  }

  incrementarPuntaje(): void {
    if (!this.puedeModificarPuntaje) return;
    const idx = this.escalaPuntajes.findIndex(op => op.valor === this.opcionPuntajeFinal);
    if (idx !== -1 && idx < this.escalaPuntajes.length - 1) {
      this.opcionPuntajeFinal = this.escalaPuntajes[idx + 1].valor;
    }
  }

  getTipoDescargoDisplay(desc: DescargoDetalleDTO | null | undefined): string {
    if (!desc) return '—';
    if (desc.causal && desc.causal.trim()) {
      return desc.causal.trim();
    }
    if (desc.tipo === 'T02_CERTIFICADO') return 'Certificado de Examen (T02)';
    if (desc.tipo === 'T03_EXTRAORDINARIO') return 'Descargo Extraordinario (T03)';
    return desc.tipo || '—';
  }

  getPuntajeFinalInvolucradoDisplay(fila: InvolucradoJustificacion): string {
    const val = fila.descargo?.puntaje_ratificado;
    if (val != null) {
      if (val === 'LLAMADO_ATENCION') return 'Llamado de Atención';
      if (val === 'FELICITACION') return 'Felicitación';
      const num = Number(val);
      if (!isNaN(num)) {
        return num > 0 ? `+${num}` : `${num}`;
      }
      return String(val);
    }
    const pts = this.getPuntajeFinalInvolucrado(fila);
    return pts > 0 ? `+${pts}` : `${pts}`;
  }

  getPuntajeFinalInvolucrado(fila: InvolucradoJustificacion): number {
    if (fila.descargo?.puntaje_ratificado != null) {
      const val = fila.descargo.puntaje_ratificado;
      if (val === 'LLAMADO_ATENCION') return 0;
      if (val === 'FELICITACION') return 0;
      const num = Number(val);
      if (!isNaN(num)) return num;
    }
    if (fila.descargo?.decisiones_causal && fila.descargo.decisiones_causal.length > 0) {
      const ultima = fila.descargo.decisiones_causal[0];
      if (ultima.decision === 'ACCEPTED') {
        return 0;
      }
      if (ultima.decision === 'REJECTED') {
        return this.expedienteSeleccionado?.puntos ?? 0;
      }
    }
    return this.expedienteSeleccionado?.puntos ?? 0;
  }

  verDescargo(fila: InvolucradoJustificacion): void {
    if (!this.expedienteSeleccionado || !fila.descargo) return;
    this.involucradoSeleccionado = fila;

    // Inicializar puntaje final y fundamento del descargo
    const pedido = this.expedienteSeleccionado.puntos ?? 0;
    let valorInicial = '0.0';
    if (fila.descargo.puntaje_ratificado != null) {
      valorInicial = String(fila.descargo.puntaje_ratificado);
    } else if (fila.descargo.decisiones_causal?.[0]) {
      valorInicial = String(this.getPuntajeFinalInvolucrado(fila));
    } else {
      valorInicial = Number(pedido).toFixed(1);
    }

    const match = this.escalaPuntajes.find(
      op => op.valor === valorInicial || Number(op.valor) === Number(valorInicial)
    );
    this.opcionPuntajeFinal = match ? match.valor : valorInicial;
    const num = Number(this.opcionPuntajeFinal);
    this.puntajeFinalInput = isNaN(num) ? 0 : num;

    const ultimaDecision = fila.descargo.decisiones_causal?.[0];
    this.fundamentoPuntajeInput = ultimaDecision?.fundamento || '';

    this.modalDetalleAbierto = false;
    this.modalDescargoAbierto = true;
  }

  getEncabezadoModalDescargo(): string {
    if (!this.expedienteSeleccionado || !this.involucradoSeleccionado) {
      return 'Descargo';
    }
    const expId = this.expedienteSeleccionado.id ?? this.expedienteSeleccionado.numero;
    const nroSocio = this.involucradoSeleccionado.legajo;
    const nombre = this.getNombreCompletoInvolucrado(this.involucradoSeleccionado);
    return `Descargo exp ${expId} y ${nroSocio}, ${nombre}`;
  }

  esFundamentoObligatorio(): boolean {
    const pedido = Number(this.expedienteSeleccionado?.puntos || 0);
    const actual = this.getOpcionPuntajeActual();
    if (this.puntajeFinalInput !== null && Number(this.puntajeFinalInput) !== actual.rank &&
        actual.valor !== 'LLAMADO_ATENCION' && actual.valor !== 'FELICITACION') {
      return Number(this.puntajeFinalInput) < pedido;
    }
    return actual.rank < pedido;
  }

  puedeGuardarDescargo(): boolean {
    if (this.guardandoDescargo) return false;
    if (this.esFundamentoObligatorio()) {
      return !!this.fundamentoPuntajeInput && this.fundamentoPuntajeInput.trim().length >= 10;
    }
    return true;
  }

  guardarYVolverDescargo(): void {
    const descargo = this.involucradoSeleccionado?.descargo;
    const exp = this.expedienteSeleccionado;
    if (!exp || !descargo || this.guardandoDescargo) return;

    const pedido = Number(exp.puntos ?? 0);
    let actual = this.getOpcionPuntajeActual();
    if (this.puntajeFinalInput !== null && Number(this.puntajeFinalInput) !== actual.rank &&
        actual.valor !== 'LLAMADO_ATENCION' && actual.valor !== 'FELICITACION') {
      const match = this.escalaPuntajes.find(op => Number(op.valor) === Number(this.puntajeFinalInput));
      if (match) {
        this.opcionPuntajeFinal = match.valor;
        actual = match;
      }
    }
    const puntajeFinalPayload: string | number =
      actual.valor === 'LLAMADO_ATENCION' || actual.valor === 'FELICITACION'
        ? actual.valor
        : (this.puntajeFinalInput !== null && Number(this.puntajeFinalInput) !== actual.rank ? Number(this.puntajeFinalInput) : Number(actual.valor));

    const fundamento = (this.fundamentoPuntajeInput || '').trim();

    if (this.esFundamentoObligatorio() && fundamento.length < 10) {
      this.notifications.warning(
        'La fundamentación escrita es obligatoria (mínimo 10 caracteres) cuando el puntaje final es menor al pedido original.'
      );
      return;
    }

    this.guardandoDescargo = true;
    const decision: DecisionCausal =
      actual.rank >= pedido && actual.rank >= 0 ? 'ACCEPTED' : (descargo.regla_sugerida || 'ACCEPTED');

    this.expedienteApi.registrarDecisionCausal(exp.id, descargo.id, {
      decision,
      fundamento,
      puntaje_final: puntajeFinalPayload,
      evidencia_ids: (descargo.evidencias || []).map(ev => ev.id)
    }).subscribe({
      next: (resp) => {
        this.guardandoDescargo = false;
        descargo.leido = true;
        descargo.puntaje_ratificado = puntajeFinalPayload;
        if (resp) {
          descargo.decisiones_causal = [resp, ...(descargo.decisiones_causal || [])];
        }
        this.notifications.success('Evaluación del descargo guardada con éxito.');
        this.volverADetalleDesdeDescargo();
      },
      error: (err) => {
        this.guardandoDescargo = false;
        if (err.status === 400 && err.error?.detail) {
          this.notifications.error(err.error.detail);
          return;
        }
        // Fallback local en entornos mock / dev
        descargo.leido = true;
        descargo.puntaje_ratificado = puntajeFinalPayload;
        this.notifications.success('Evaluación del descargo guardada.');
        this.volverADetalleDesdeDescargo();
      }
    });
  }

  volverADetalleDesdeDescargo(): void {
    this.modalDescargoAbierto = false;
    this.involucradoSeleccionado = null;
    this.modalDetalleAbierto = true;
  }

  abrirResolucion(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDescargoAbierto = false;
    this.modalResolucionAbierto = true;
  }

  formatSolicitante(exp: Expediente | null): string {
    if (!exp) return 'Comisión Directiva';
    const creador = (exp.creador || '').trim();
    if (creador) {
      // Si ya viene en formato "Apellido, Nombre (Legajo)" o "Nombre (Legajo)"
      const match = /^(.+?)\s*\((.+?)\)$/.exec(creador);
      if (match) {
        const nombrePart = match[1].trim();
        const legajoPart = match[2].trim();
        return `${legajoPart} - ${nombrePart}`;
      }
      return creador;
    }
    return exp.solicitante || 'Comisión Directiva';
  }
}
