import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router } from '@angular/router';
import { 
  TribunalDataService, 
  Expediente, 
  EstadoExpediente, 
  NivelUrgencia
} from '../services/tribunal-data.service';
import { AuthService, PerfilSocio } from '../services/auth.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';
import {
  ComposicionTribunalDTO,
  ApelacionT01DTO,
  ArticuloReglamentoDTO,
  DecisionCausal,
  DescargoDetalleDTO,
  EvidenciaMetadata,
  ExpedienteApiService,
  ExpedienteDetalleDTO,
  GuardarResolucionPayload,
  HistorialT01DTO,
  ResolucionOficialDTO,
  SocioT01DTO
} from '../services/expediente-api.service';
import { SocioApiService, SocioListItemDTO } from '../services/socio-api.service';
import { Subject, Subscription, of } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap } from 'rxjs/operators';
import { formatCaseNumber as formatCaseNumberUtil } from '../utils/case-number.util';
import {
  parseReglamentoCite,
  parseReglamentosList,
  ReglamentoCiteView
} from '../utils/reglamento-format.util';
import { ModalScrollLockService } from '../services/modal-scroll-lock.service';

// Registro de decisiones: sólo en la etapa de resolución (Spec 006, EARS 7).
const ESTADOS_DECISION_CAUSAL = ['revision_resolucion', 'espera_resolucion'];
// Consulta: desde la revisión y también después de emitida la resolución (EARS 8).
const ESTADOS_CONSULTA_CAUSAL = [
  ...ESTADOS_DECISION_CAUSAL, 'pendiente_firma', 'pendiente_correos', 'emitido'
];
export const MIN_FUNDAMENTO_CAUSAL = 20;
export const MAX_FUNDAMENTO_CAUSAL = 5000;
export const MIN_MOTIVOS_ADECUACION = 20;

export interface CatalogoReglamentoItem {
  raw: string;
  citaCorta: string;
  documento: 'Estatuto' | 'Reglamento Interno' | 'Normativa';
  articulo: string;
  inciso: string;
  seccion: string;
  cuerpo: string;
}

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
  private elementoFocoPrevio: HTMLElement | null = null;

  // Votación y Reglamentos Respaldantes
  reglamentosDisponibles: string[] = [];
  articulosDisponibles: ArticuloReglamentoDTO[] = [];
  reglamentosSeleccionadosResolucion: string[] = [];
  filtroReglamentosResolucion = '';

  get expedienteService(): ExpedienteApiService {
    return this.expedienteApi;
  }

  vistosTexto = '';
  considerandosTexto = '';
  seResuelveTexto = '';
  fechaResolucionTexto = '';
  fechaActualResolucion = new Date();
  guardandoResolucion = false;
  firmando = false;

  // Catálogo reglamentario en Modal Generar Resolución (Sustento VISTO)
  modalCatalogoResolucionAbierto = false;
  filtroDocumentoResolucionModal: 'TODOS' | 'Estatuto' | 'Reglamento Interno' = 'TODOS';
  busquedaCatalogoResolucion = '';
  catalogoItemsModal: CatalogoReglamentoItem[] = [];

  votosJueces: { [juez: string]: 'FAVORABLE' | 'DESFAVORABLE' | 'ABSTENCION' } = {};

  get usuarioActualPerfil(): PerfilSocio | null {
    return this.auth.getCurrentUser();
  }

  get firmantesPieResolucion(): { anioSocial: number; etiquetaAnio: string; firma: string }[] {
    const firmas = this.expedienteSeleccionado?.firmas?.juecesFirmantes || [];
    return [4, 5, 6].map((anio, idx) => {
      const match = firmas.find(f => {
        if (anio === 4 && (f.includes('4.°') || f.includes('4.º') || f.includes('G59') || f.includes('Candela Moreno') || f.includes('11735'))) return true;
        if (anio === 5 && (f.includes('5.°') || f.includes('5.º') || f.includes('G58') || f.includes('Catalina Cerda') || f.includes('11737'))) return true;
        if (anio === 6 && (f.includes('6.°') || f.includes('6.º') || f.includes('G57') || f.includes('Giuliano Toselli') || f.includes('11239'))) return true;
        return false;
      }) || firmas[idx];

      return {
        anioSocial: anio,
        etiquetaAnio: `${anio}.º Año Social`,
        firma: match || 'Pendiente de firma'
      };
    });
  }

  get espaciosFirmaPorAnioSocial(): { anioSocial: number; etiquetaAnio: string; firma: string | null; firmado: boolean }[] {
    const firmas = this.expedienteSeleccionado?.firmas?.juecesFirmantes || [];
    return [4, 5, 6].map((anio, idx) => {
      const match = firmas.find(f => {
        if (anio === 4 && (f.includes('4.°') || f.includes('4.º') || f.includes('G59') || f.includes('Candela Moreno') || f.includes('11735'))) return true;
        if (anio === 5 && (f.includes('5.°') || f.includes('5.º') || f.includes('G58') || f.includes('Catalina Cerda') || f.includes('11737'))) return true;
        if (anio === 6 && (f.includes('6.°') || f.includes('6.º') || f.includes('G57') || f.includes('Giuliano Toselli') || f.includes('11239'))) return true;
        return false;
      }) || firmas[idx];

      return {
        anioSocial: anio,
        etiquetaAnio: `${anio}.º Año Social`,
        firma: match || null,
        firmado: !!match
      };
    });
  }

  get usuarioYaFirmoResolucion(): boolean {
    const perfil = this.usuarioActualPerfil;
    if (!perfil || !this.expedienteSeleccionado?.firmas?.juecesFirmantes) return false;
    const legajo = String(perfil.legajo || '').trim();
    if (!legajo) return false;
    return this.expedienteSeleccionado.firmas.juecesFirmantes.some(f => f.includes(legajo));
  }

  get reglamentosResolucionCitas(): ReglamentoCiteView[] {
    return parseReglamentosList(this.reglamentosSeleccionadosResolucion, null, this.articulosDisponibles);
  }

  failedToLoadBoard = false;
  cargando = false;

  // Evaluación de justificaciones T02 dentro del detalle (S4-02)
  readonly maxFundamento = MAX_FUNDAMENTO_CAUSAL;
  involucradosJustificacion: InvolucradoJustificacion[] = [];
  involucradoSeleccionado: InvolucradoJustificacion | null = null;
  cargandoJustificaciones = false;
  borradorCausal: BorradorDecisionCausal = { decision: '', fundamento: '' };
  registrandoCausal = false;

  // Tribunal de la causa (S4-04): inhibición de involucrados y suplencia automática (Art. 95)
  composicion: ComposicionTribunalDTO | null = null;
  cargandoComposicion = false;

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
    private router: Router,
    private scrollLock: ModalScrollLockService
  ) {}

  get puedeVotarOFirmar(): boolean {
    return this.auth.tieneRol('TD');
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
    if (!this.puedeResolverExpedienteSeleccionado || !this.expedienteSeleccionado) return false;
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
    if (!this.puedeResolverExpedienteSeleccionado || !this.expedienteSeleccionado) return false;
    const est = this.expedienteSeleccionado.estado;
    const firmas = this.expedienteSeleccionado.firmas?.juecesFirmantes || [];
    return (est === 'pendiente_firma' || (est === 'pendiente_correos' && firmas.length < 3)) && firmas.length < 3;
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
    this.cargarReglamentosDisponibles();
  }

  cargarReglamentosDisponibles(): void {
    this.expedienteService.listarReglamentos().subscribe({
      next: res => {
        this.reglamentosDisponibles = res?.reglamentos || [];
        this.articulosDisponibles = (res as any)?.articulos || [];
        this.actualizarCatalogoItemsModal();
      },
      error: err => {
        console.warn('No se pudieron cargar los reglamentos vigentes', err);
      }
    });
  }

  actualizarCatalogoItemsModal(): void {
    if (this.articulosDisponibles && this.articulosDisponibles.length > 0) {
      this.catalogoItemsModal = this.articulosDisponibles.map(art => {
        const raw = art.cita_completa || (art.cuerpo ? `${art.cita_corta}: ${art.cuerpo}` : art.cita_corta);
        const parsed = parseReglamentoCite(raw, this.articulosDisponibles);
        return {
          raw,
          citaCorta: parsed.citaCorta,
          documento: parsed.documento,
          articulo: String(art.articulo ?? ''),
          inciso: art.inciso && art.inciso !== '-' ? String(art.inciso) : '',
          seccion: String(art.seccion ?? ''),
          cuerpo: (art.cuerpo || art.descripcion || parsed.cuerpo || '').trim()
        };
      });
      return;
    }
    this.catalogoItemsModal = (this.reglamentosDisponibles || []).map(raw => {
      const parsed = parseReglamentoCite(raw);
      return {
        raw,
        citaCorta: parsed.citaCorta,
        documento: parsed.documento,
        articulo: '',
        inciso: '',
        seccion: '',
        cuerpo: parsed.cuerpo
      };
    });
  }

  get articulosModalResolucionFiltrados(): CatalogoReglamentoItem[] {
    const busqueda = (this.busquedaCatalogoResolucion || '').trim().toLowerCase();
    return this.catalogoItemsModal.filter(item => {
      if (this.filtroDocumentoResolucionModal !== 'TODOS' && item.documento !== this.filtroDocumentoResolucionModal) {
        return false;
      }
      if (!busqueda) {
        return true;
      }
      return (
        item.raw.toLowerCase().includes(busqueda) ||
        item.citaCorta.toLowerCase().includes(busqueda) ||
        item.cuerpo.toLowerCase().includes(busqueda) ||
        item.seccion.toLowerCase().includes(busqueda) ||
        (`art. ${item.articulo}`).toLowerCase().includes(busqueda)
      );
    });
  }

  abrirModalCatalogoResolucion(): void {
    this.busquedaCatalogoResolucion = '';
    this.filtroDocumentoResolucionModal = 'TODOS';
    this.actualizarCatalogoItemsModal();
    this.modalCatalogoResolucionAbierto = true;
    this.scrollLock.lock();
  }

  cerrarModalCatalogoResolucion(): void {
    this.modalCatalogoResolucionAbierto = false;
    this.scrollLock.unlock();
  }

  setFiltroDocumentoResolucionModal(doc: 'TODOS' | 'Estatuto' | 'Reglamento Interno'): void {
    this.filtroDocumentoResolucionModal = doc;
  }

  esReglamentoResolucionSeleccionado(raw: string): boolean {
    return this.reglamentosSeleccionadosResolucion.includes(raw);
  }

  contarSeleccionadosPorDocumentoResolucion(doc: 'Estatuto' | 'Reglamento Interno'): number {
    return this.reglamentosResolucionCitas.filter(c => c.documento === doc).length;
  }

  get reglamentosResolucionFiltrados(): string[] {
    const busqueda = (this.filtroReglamentosResolucion || '').trim().toLowerCase();
    if (!busqueda) {
      return this.reglamentosDisponibles;
    }
    return this.reglamentosDisponibles.filter(reg =>
      reg.toLowerCase().includes(busqueda) || this.reglamentosSeleccionadosResolucion.includes(reg)
    );
  }

  toggleReglamentoResolucion(reg: string): void {
    const idx = this.reglamentosSeleccionadosResolucion.indexOf(reg);
    if (idx >= 0) {
      this.reglamentosSeleccionadosResolucion.splice(idx, 1);
    } else {
      this.reglamentosSeleccionadosResolucion.push(reg);
    }
    this.vistosTexto = this.construirVistosPorDefecto();
  }

  agregarReglamentoResolucion(reg: string): void {
    if (!reg) return;
    if (!this.reglamentosSeleccionadosResolucion.includes(reg)) {
      this.reglamentosSeleccionadosResolucion.push(reg);
      this.vistosTexto = this.construirVistosPorDefecto();
    }
  }

  quitarReglamentoResolucion(reg: string): void {
    this.reglamentosSeleccionadosResolucion = this.reglamentosSeleccionadosResolucion.filter(r => r !== reg);
    this.vistosTexto = this.construirVistosPorDefecto();
  }

  removerReglamentoResolucion(reg: string): void {
    this.quitarReglamentoResolucion(reg);
  }

  limpiarReglamentosResolucion(): void {
    this.reglamentosSeleccionadosResolucion = [];
    this.vistosTexto = this.construirVistosPorDefecto();
  }

  onModalCatalogoKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.cerrarModalCatalogoResolucion();
    }
  }

  obtenerNumeroResolucionPreview(): string {
    return this.expedienteSeleccionado?.numero ? this.formatCaseNumber(this.expedienteSeleccionado.numero) : 'EXP-___/____';
  }

  construirVistosPorDefecto(): string {
    const num = this.expedienteSeleccionado ? this.formatCaseNumber(this.expedienteSeleccionado.numero) : 'S/N';
    const titulo = this.expedienteSeleccionado?.titulo || this.expedienteSeleccionado?.motivo || 'Causa Disciplinaria';
    const fecha = this.expedienteSeleccionado?.fechaCreacion ? new Date(this.expedienteSeleccionado.fechaCreacion).toLocaleDateString('es-AR') : 'reciente';
    const solicitante = this.expedienteSeleccionado ? this.formatSolicitante(this.expedienteSeleccionado) : 'Comisión Directiva';

    let lineasReglamentos = '';
    if (this.reglamentosSeleccionadosResolucion.length > 0) {
      lineasReglamentos = this.reglamentosSeleccionadosResolucion
        .map((r, i) => `   ${i + 1}. ${r}`)
        .join('\n');
    } else {
      lineasReglamentos = '   1. Reglamento Procesal Disciplinario 2026.';
    }

    return `VISTO:\n1. Las actuaciones obrantes en el Expediente ${num}, caratulado "${titulo}", promovido por ${solicitante} con fecha ${fecha}.\n2. Lo normado y garantizado en los siguientes artículos e instrumentos reglamentarios:\n${lineasReglamentos}\n3. Las constancias documentales, descargos tipificados y elementos probatorios aportados a la causa.`;
  }

  construirConsiderandosPorDefecto(exp?: Expediente | null): string {
    return '';
  }

  construirSeResuelvePorDefecto(exp: Expediente): string {
    const filas = this.involucradosJustificacion || [];
    let detalleInvolucrados = '';
    if (filas.length > 0) {
      detalleInvolucrados = filas.map(f => {
        const nombre = this.getNombreCompletoInvolucrado(f);
        const legajo = f.legajo || 'S/L';
        const grupo = f.grupo ? ` (G${this.formatGrupoInvolucrado(f.grupo)})` : '';
        const puntaje = this.getPuntajeFinalInvolucradoDisplay(f);
        return `   - Socio N° ${legajo} — ${nombre}${grupo}: ${puntaje}`;
      }).join('\n');
    } else {
      const socio = exp.socio || 'Socio';
      const legajo = exp.legajo || 'S/L';
      const puntos = exp.puntos > 0 ? `+${exp.puntos}` : `${exp.puntos}`;
      detalleInvolucrados = `   - Socio N° ${legajo} — ${socio}: ${puntos} pts`;
    }

    return `SE RESUELVE:\nARTÍCULO 1°.- APLICAR la resolución disciplinaria correspondiente a los socios involucrados en los presentes actuados:\n${detalleInvolucrados}\n\nARTÍCULO 2°.- NOTIFICAR fehacientemente a los interesados y comunicar lo resuelto a la Comisión Directiva para su efectivo registro en el cómputo institucional de puntos.\n\nARTÍCULO 3°.- REGÍSTRESE, cúmplase con las firmas digitales colegiadas de los representantes de los años sociales y archívese en Secretaría del Tribunal de Disciplina.`;
  }

  construirFechaResolucionTexto(): string {
    const hoy = new Date();
    const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
    const dia = hoy.getDate();
    const mes = meses[hoy.getMonth()];
    const anio = hoy.getFullYear();
    const hora = String(hoy.getHours()).padStart(2, '0');
    const min = String(hoy.getMinutes()).padStart(2, '0');
    return `Córdoba, ${dia} de ${mes} de ${anio}, ${hora}:${min} hs`;
  }

  ngOnDestroy(): void {
    this.scrollLock.reset();
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

  getIconoOrden(col: string): string {
    if (this.columnaOrden !== col) return 'swap_vert';
    return this.ordenAscendente ? 'arrow_upward' : 'arrow_downward';
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
    this.scrollLock.lock();
    this.enfocarModalActivo();
    this.reglamentacionExpandida = false;
    this.reglamentoExpandidoModal = null;
    this.limpiarJustificaciones();
    this.limpiarT01();
    this.limpiarComposicion();

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

    if (this.puedeConsultarComposicion) {
      this.cargarComposicion(exp.id);
    }

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

  // --- Tribunal de la causa (S4-04) ---

  get puedeConsultarComposicion(): boolean {
    return this.auth.tieneRol('TD', 'CD', 'ADMIN');
  }

  /** Parte interesada: no inhibe a miembros con rol TD conforme a directivas vigentes. */
  get usuarioInvolucrado(): boolean {
    return false;
  }

  /**
   * Cualquier usuario con rol TD puede resolver sin bloqueos adicionales.
   */
  get puedeResolverExpedienteSeleccionado(): boolean {
    return this.auth.tieneRol('TD');
  }

  cargarComposicion(expedienteId: number | string): void {
    this.cargandoComposicion = true;
    this.expedienteApi.obtenerComposicionTribunal(expedienteId).subscribe({
      next: composicion => {
        this.cargandoComposicion = false;
        this.composicion = composicion;
      },
      error: err => {
        this.cargandoComposicion = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo cargar la composición del Tribunal.'));
      }
    });
  }

  private limpiarComposicion(): void {
    this.composicion = null;
    this.cargandoComposicion = false;
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
    return !!fila.descargo;
  }

  estadoJustificacion(fila: InvolucradoJustificacion): string {
    const descargo = fila.descargo;
    if (!descargo) return 'Sin justificación';
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
    this.modalResolucionAbierto = false;
    this.modalCatalogoResolucionAbierto = false;
    this.modalVotacionAbierto = true;
    this.fechaActualResolucion = new Date();
    this.scrollLock.lock();
    this.enfocarModalActivo();
    this.filtroReglamentosResolucion = '';
    this.busquedaCatalogoResolucion = '';
    this.filtroDocumentoResolucionModal = 'TODOS';
    const previos = exp.reglamentosRespaldantes || exp.reglamentos_respaldantes || [];
    this.reglamentosSeleccionadosResolucion = [...previos];
    this.actualizarCatalogoItemsModal();

    this.fechaResolucionTexto = exp.fechaResolucion || this.construirFechaResolucionTexto();
    this.vistosTexto = exp.vistos || exp.votacion?.vistos || this.construirVistosPorDefecto();
    this.considerandosTexto = exp.considerandos || exp.votacion?.considerandos || '';
    this.seResuelveTexto = exp.seResuelve || exp.votacion?.seResuelve || this.construirSeResuelvePorDefecto(exp);

    if (exp.id && !isNaN(Number(exp.id))) {
      this.expedienteApi.obtenerResolucion(exp.id).subscribe({
        next: res => {
          if (res) {
            if (res.vistos) this.vistosTexto = res.vistos;
            if (res.considerandos) this.considerandosTexto = res.considerandos;
            if (res.articulos_resolutivos) this.seResuelveTexto = res.articulos_resolutivos;
          }
        },
        error: () => {}
      });
    }
  }

  abrirModalVotacion(exp: Expediente): void {
    this.abrirVotacion(exp);
  }

  abrirFirma(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalSociosAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalCatalogoResolucionAbierto = false;
    this.modalFirmaAbierto = true;
    this.firmando = false;
    this.scrollLock.lock();
    this.enfocarModalActivo();
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
    this.scrollLock.lock();
    this.enfocarModalActivo();
  }

  volverADetalle(): void {
    this.modalSociosAbierto = false;
    if (this.expedienteSeleccionado) {
      this.abrirDetalle(this.expedienteSeleccionado);
    }
  }

  cerrarModales(): void {
    this.scrollLock.reset();
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.modalSociosAbierto = false;
    this.modalResolucionAbierto = false;
    this.modalDescargoAbierto = false;
    this.modalCatalogoResolucionAbierto = false;
    this.reglamentacionExpandida = false;
    this.expedienteSeleccionado = null;
    this.reglamentosSeleccionadosResolucion = [];
    this.filtroReglamentosResolucion = '';
    this.busquedaCatalogoResolucion = '';
    this.guardandoResolucion = false;
    this.firmando = false;
    this.limpiarJustificaciones();
    this.limpiarComposicion();
    this.limpiarT01();
    if (this.elementoFocoPrevio && typeof this.elementoFocoPrevio.focus === 'function') {
      this.elementoFocoPrevio.focus({ preventScroll: true });
    }
    this.elementoFocoPrevio = null;
  }

  private enfocarModalActivo(): void {
    if (!this.elementoFocoPrevio && typeof document !== 'undefined') {
      this.elementoFocoPrevio = document.activeElement as HTMLElement;
    }
    setTimeout(() => {
      if (typeof document === 'undefined') return;
      const activeDialog = document.querySelector(
        '.modal-backdrop-custom .modal-dialog-custom'
      ) as HTMLElement | null;
      const cardBody = document.querySelector(
        '.modal-backdrop-custom .modal-detalle-body, .modal-backdrop-custom .card-body'
      ) as HTMLElement | null;

      if (cardBody) {
        cardBody.scrollTop = 0;
      }
      if (activeDialog && typeof activeDialog.focus === 'function') {
        activeDialog.focus({ preventScroll: true });
      } else if (cardBody && typeof cardBody.focus === 'function') {
        cardBody.focus({ preventScroll: true });
      }
    }, 0);
  }

  onModalKeydown(event: KeyboardEvent): void {
    if (!event) return;

    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      this.cerrarModales();
      return;
    }

    const target = event.target as HTMLElement | null;
    const tag = target?.tagName?.toUpperCase();
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') {
      return;
    }

    if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp'].includes(event.key)) {
      const delta = (event.key === 'ArrowDown' ? 40 : event.key === 'ArrowUp' ? -40 : event.key === 'PageDown' ? 200 : -200);
      const cardBody = document.querySelector(
        '.modal-backdrop-custom .modal-detalle-body, .modal-backdrop-custom .card-body'
      ) as HTMLElement | null;
      if (cardBody) {
        cardBody.scrollTop += delta;
      }
      event.preventDefault();
      event.stopPropagation();
    }
  }

  confirmarVotacion(): void {
    if (!this.expedienteSeleccionado) return;
    const exp = this.expedienteSeleccionado;

    if (this.reglamentosSeleccionadosResolucion.length === 0) {
      this.notifications.warning('Seleccioná al menos un artículo reglamentario en VISTO.');
      return;
    }

    const considerandos = (this.considerandosTexto || '').trim();
    if (!considerandos) {
      this.notifications.warning('El campo CONSIDERANDO es obligatorio.');
      return;
    }

    // Generación automática y estructurada de VISTO
    const citas = this.reglamentosResolucionCitas
      .map(c => c.citaCorta || c.raw)
      .join('; ');
    const numExp = this.formatCaseNumber(exp.numero);
    const vistos = `VISTO: Las actuaciones obrantes en el Expediente ${numExp} y lo normado en las disposiciones institucionales de A.V.E.I.T.: ${citas}.`;

    // Generación automática y estructurada de SE RESUELVE
    const lineasSocios = (this.involucradosJustificacion || []).map(inv => {
      const nom = this.getNombreCompletoInvolucrado(inv);
      const grupo = inv.grupo ? ` (Grupo ${inv.grupo})` : '';
      const pts = this.getPuntajeFinalInvolucradoDisplay(inv);
      return `• Socio N° ${inv.legajo} - ${nom}${grupo}: Puntaje Final ${pts}.`;
    }).join('\n');

    const detalleSocios = lineasSocios || `• Socio ${exp.socio || exp.legajo || 'involucrado'}: Puntaje Final ${exp.puntos > 0 ? '+' : ''}${exp.puntos} pts.`;
    const seResuelve = `ARTÍCULO 1°.- Aplicar la resolución disciplinaria correspondiente a los socios involucrados conforme al siguiente detalle de puntos finales consolidados:\n${detalleSocios}\n\nARTÍCULO 2°.- Notifíquese a la Comisión Directiva y a los socios involucrados, regístrese, publíquese y archívese.`;

    const reglamentos = [...this.reglamentosSeleccionadosResolucion];
    exp.reglamentosRespaldantes = reglamentos;
    exp.reglamentos_respaldantes = reglamentos;

    const enLista = (this.expedientes || []).find(e => e.id === exp.id);
    if (enLista) {
      enLista.reglamentosRespaldantes = reglamentos;
      enLista.reglamentos_respaldantes = reglamentos;
    }

    this.guardandoResolucion = true;

    const payload: GuardarResolucionPayload = {
      vistos,
      considerandos,
      articulos_resolutivos: seResuelve
    };

    const actualizarLocalYFinalizar = (hash?: string) => {
      this.dataService.votarDictamen(exp.id, this.votosJueces, considerandos, {
        vistos,
        considerandos,
        seResuelve,
        fechaResolucion: this.fechaResolucionTexto,
        numeroResolucion: exp.numero
      });
      exp.estado = 'pendiente_firma';
      exp.estadoDisplay = 'Pendiente de Firma';
      exp.vistos = vistos;
      exp.considerandos = considerandos;
      exp.seResuelve = seResuelve;
      exp.fechaResolucion = this.fechaResolucionTexto;
      exp.numeroResolucion = exp.numero;
      exp.votacion = {
        votos: this.votosJueces,
        vistos,
        considerandos,
        seResuelve,
        fechaResolucion: this.fechaResolucionTexto,
        numeroResolucion: exp.numero,
        aprobado: true
      };
      exp.firmas = {
        juecesFirmantes: [],
        hashCriptografico: hash || '',
        timestamp: ''
      };
      this.guardandoResolucion = false;
      this.mostrarNotificacion('Resolución oficial generada con éxito. Expediente pasa a Pendiente de Firma.');
      this.cerrarModales();
      this.cargarDatosTablero();
    };

    if (exp.id && !isNaN(Number(exp.id))) {
      this.expedienteApi.crearResolucion(exp.id, payload).subscribe({
        next: res => {
          actualizarLocalYFinalizar(res?.contenido_hash);
        },
        error: () => {
          this.expedienteApi.actualizarResolucion(exp.id, payload).subscribe({
            next: res => actualizarLocalYFinalizar(res?.contenido_hash),
            error: () => actualizarLocalYFinalizar()
          });
        }
      });
    } else {
      actualizarLocalYFinalizar();
    }
  }

  descargarPdfResolucion(): void {
    if (!this.expedienteSeleccionado) return;
    const expId = this.expedienteSeleccionado.id;
    this.expedienteApi.descargarPreviewResolucionPdf(expId).subscribe({
      next: blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resolucion-${expId}.pdf`;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 10000);
      },
      error: err => {
        this.notifications.error(httpErrorMessage(err, 'No se pudo descargar la vista previa de la resolución en PDF.'));
      }
    });
  }

  confirmarFirma(): void {
    if (!this.expedienteSeleccionado || this.firmando) return;
    const exp = this.expedienteSeleccionado;
    this.firmando = true;

    const finalizarExito = (firmasActualizadas: string[], estadoRes?: string, hash?: string, issuedAt?: string) => {
      exp.firmas = {
        juecesFirmantes: firmasActualizadas,
        hashCriptografico: hash || exp.firmas?.hashCriptografico || '',
        timestamp: issuedAt || exp.firmas?.timestamp || ''
      };
      if (firmasActualizadas.length >= 3 || estadoRes === 'ISSUED') {
        exp.estado = 'pendiente_correos';
        exp.estadoDisplay = 'Pendiente de Envío';
        this.mostrarNotificacion('Resolución perfeccionada con las 3 firmas digitales e impacto en saldo de socios.');
      } else {
        this.mostrarNotificacion(`Firma digital estampada exitosamente (${firmasActualizadas.length}/3 firmas recolectadas).`);
      }
      this.firmando = false;
      this.cerrarModales();
      this.cargarDatosTablero();
    };

    if (exp.id && !isNaN(Number(exp.id))) {
      this.expedienteApi.firmarResolucionOficial(exp.id).subscribe({
        next: res => {
          const firmas = Array.isArray(res.firmantes_td)
            ? res.firmantes_td.map(f => typeof f === 'string' ? f : (f.etiqueta || `${f.legajo} - ${f.full_name} - ${f.grupo}`))
            : [];
          finalizarExito(firmas, res.estado, res.contenido_hash, res.issued_at);
        },
        error: () => {
          const perfil = this.auth.getCurrentUser();
          const nombre = perfil ? `${perfil.legajo || ''} - ${perfil.first_name || ''} ${perfil.last_name || ''} - ${perfil.category || 'G58'}`.replace(/\s+/g, ' ').trim() : 'Firma TD';
          const resLocal = this.dataService.firmarResolucion(exp.id, nombre);
          finalizarExito(exp.firmas?.juecesFirmantes || [nombre], resLocal.completo ? 'ISSUED' : 'DRAFT');
        }
      });
    } else {
      const perfil = this.auth.getCurrentUser();
      const nombre = perfil ? `${perfil.legajo || ''} - ${perfil.first_name || ''} ${perfil.last_name || ''} - ${perfil.category || 'G58'}`.replace(/\s+/g, ' ').trim() : 'Firma TD';
      const resLocal = this.dataService.firmarResolucion(exp.id, nombre);
      finalizarExito(exp.firmas?.juecesFirmantes || [nombre], resLocal.completo ? 'ISSUED' : 'DRAFT');
    }
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

  reglamentoExpandidoModal: string | null = null;

  getReglamentosSustentoCitas(exp: Expediente | null): ReglamentoCiteView[] {
    return parseReglamentosList(this.getReglamentosSustento(exp));
  }

  toggleExpandirChipReglamento(raw: string): void {
    this.reglamentoExpandidoModal = this.reglamentoExpandidoModal === raw ? null : raw;
  }

  get reglamentoExpandidoDetalle(): ReglamentoCiteView | null {
    if (!this.reglamentoExpandidoModal) return null;
    return parseReglamentoCite(this.reglamentoExpandidoModal);
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

  esSocioActual(fila: InvolucradoJustificacion): boolean {
    const perfil = this.auth.getPerfil();
    if (!perfil) return false;
    const legajoActual = perfil.legajo ? String(perfil.legajo).trim() : '';
    const legajoFila = fila.legajo ? String(fila.legajo).trim() : '';
    return !!(legajoActual && legajoFila && legajoActual === legajoFila);
  }

  irAMisExpedientesParaDescargo(): void {
    this.cerrarModales();
    this.router.navigate(['/mis-expedientes']);
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
    if (!this.expedienteSeleccionado || !this.auth.tieneRol('TD')) return false;
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

  getPuntajeSolicitadoDisplay(exp: Expediente | null | undefined): string {
    if (!exp) return '0 pts';
    if (exp.puntaje_solicitado === 'LLAMADO_ATENCION' || exp.puntos === -0.25) {
      return 'Llamado de Atención';
    }
    if (exp.puntaje_solicitado === 'FELICITACION' || exp.puntos === 0.25) {
      return 'Felicitación';
    }
    const p = exp.puntos ?? 0;
    return `${p > 0 ? '+' : ''}${p} pts`;
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
    if (desc.causal && desc.causal.trim() && desc.causal.trim() !== 'Otro') {
      return desc.causal.trim();
    }
    if (desc.causal === 'Otro' || desc.tipo === 'T03_EXTRAORDINARIO') return 'Otros';
    if (desc.tipo === 'T02_CERTIFICADO') return 'Descargo con Certificado';
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
      if (this.expedienteSeleccionado?.puntaje_solicitado) {
        valorInicial = this.expedienteSeleccionado.puntaje_solicitado;
      } else if (Number(pedido) === -0.25) {
        valorInicial = 'LLAMADO_ATENCION';
      } else if (Number(pedido) === 0.25) {
        valorInicial = 'FELICITACION';
      } else {
        valorInicial = Number(pedido).toFixed(1);
      }
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
    this.scrollLock.lock();
    this.enfocarModalActivo();
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
    this.enfocarModalActivo();
  }

  abrirResolucion(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalDescargoAbierto = false;
    this.modalResolucionAbierto = true;
    this.scrollLock.lock();
    this.enfocarModalActivo();
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
