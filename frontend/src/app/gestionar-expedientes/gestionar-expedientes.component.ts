import { Component, OnInit, OnDestroy } from '@angular/core';
import { 
  TribunalDataService, 
  Expediente, 
  EstadoExpediente, 
  NivelUrgencia
} from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';
import {
  DecisionCausal,
  DescargoDetalleDTO,
  EvidenciaMetadata,
  ExpedienteApiService,
  ExpedienteDetalleDTO
} from '../services/expediente-api.service';
import { Subscription } from 'rxjs';
import { formatCaseNumber as formatCaseNumberUtil } from '../utils/case-number.util';

// Registro de decisiones: sólo en la etapa de resolución (Spec 006, EARS 7).
const ESTADOS_DECISION_CAUSAL = ['revision_resolucion', 'espera_resolucion'];
// Consulta: desde la revisión y también después de emitida la resolución (EARS 8).
const ESTADOS_CONSULTA_CAUSAL = [
  ...ESTADOS_DECISION_CAUSAL, 'pendiente_firma', 'pendiente_correos', 'emitido'
];
export const MIN_FUNDAMENTO_CAUSAL = 20;
export const MAX_FUNDAMENTO_CAUSAL = 5000;

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
  filtroFechaDesde: string = '';
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
    { key: '', label: 'Todos los estados' },
    { key: 'creado', label: 'Creados' },
    { key: 'justificando', label: 'Justificando' },
    { key: 'revision_resolucion', label: 'En Revisión' },
    { key: 'pendiente_firma', label: 'Pendiente de Firma' },
    { key: 'pendiente_correos', label: 'Pendiente de Envío' },
    { key: 'emitido', label: 'Emitidos' }
  ];

  urgenciasDisponibles: { key: string; label: string }[] = [
    { key: '', label: 'Todas las urgencias' },
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
  expedienteSeleccionado: Expediente | null = null;

  // Votación
  votosJueces: { [juez: string]: 'FAVORABLE' | 'DESFAVORABLE' | 'ABSTENCION' } = {
    'Dr. Argañaraz (Presidente TD)': 'FAVORABLE',
    'Dra. Bustos (Vocal 1)': 'FAVORABLE',
    'Ing. Rossi (Vocal 2)': 'DESFAVORABLE'
  };
  considerandosTexto = 'Por cuanto las pruebas documentales aportadas y la constancia de asistencia demuestran la concurrencia de la causal invocada.';

  // Firma
  juezFirmando = 'Dr. Argañaraz (Presidente TD)';
  juecesDisponibles = [
    'Dr. Argañaraz (Presidente TD)',
    'Dra. Bustos (Vocal 1)',
    'Ing. Rossi (Vocal 2)'
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

  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService,
    private notifications: NotificationService,
    private expedienteApi: ExpedienteApiService
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

  ngOnInit(): void {
    const sub = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
    });
    this.subs.push(sub);

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

  abrirDetalle(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalSociosAbierto = false;
    this.modalDetalleAbierto = true;
    this.limpiarJustificaciones();
    if (this.puedeConsultarJustificaciones) {
      this.cargarJustificaciones(exp.id);
    }
  }

  cargarJustificaciones(expedienteId: number | string): void {
    this.cargandoJustificaciones = true;
    this.expedienteApi.obtenerDetalleExpediente(expedienteId).subscribe({
      next: detalle => {
        this.involucradosJustificacion = this.construirInvolucrados(detalle);
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
      // Se valoran los comprobantes vigentes que el vocal puede inspeccionar en el panel.
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
    this.modalVotacionAbierto = true;
  }

  abrirFirma(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalSociosAbierto = false;
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
    this.expedienteSeleccionado = null;
    this.limpiarJustificaciones();
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
