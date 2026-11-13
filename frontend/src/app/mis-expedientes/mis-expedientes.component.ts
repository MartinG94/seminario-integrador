import { Component, OnInit, OnDestroy, Renderer2 } from '@angular/core';
import { TribunalDataService, Expediente, LogJustificativo } from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';
import {
  ExpedienteApiService,
  EvidenciaMetadata,
  DescargoVersionDto,
  HistorialT01DTO,
  OperacionDescargo,
  PeriodoApelacionDTO
} from '../services/expediente-api.service';
import { Subscription, interval } from 'rxjs';
import { formatCaseNumber, humanizeEstado } from '../utils/case-number.util';
import {
  parseReglamentoCite,
  parseReglamentosList,
  ReglamentoCiteView
} from '../utils/reglamento-format.util';
import { ModalScrollLockService } from '../services/modal-scroll-lock.service';

@Component({
  selector: 'app-mis-expedientes',
  templateUrl: './mis-expedientes.component.html',
  styleUrls: ['./mis-expedientes.component.scss']
})
export class MisExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  misExpedientes: Expediente[] = [];
  socioActual = '';
  saldoNeto = 0;
  felicitaciones = 0;
  llamadosAtencion = 0;

  // Ordenamiento de tabla
  columnaOrden = 'numero';
  ordenAscendente = true;
  filtroTab: 'todos' | 'en_tramite' | 'resueltos' = 'todos';

  setFiltroTab(tab: 'todos' | 'en_tramite' | 'resueltos'): void {
    this.filtroTab = tab;
  }

  get cantidadEnTramite(): number {
    return this.misExpedientes.filter((e) => e.estado !== 'emitido').length;
  }

  get cantidadResueltos(): number {
    return this.misExpedientes.filter((e) => e.estado === 'emitido').length;
  }

  // Modal T02/T03
  modalAbierto = false;
  expedienteSeleccionado: Expediente | null = null;
  tipoDescargo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO' = 'T02_CERTIFICADO';
  causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
  nombreArchivo = '';
  archivosSeleccionados: File[] = [];
  evidenciasExistentes: any[] = [];
  subiendoArchivos = false;
  readonly LIMITE_DOCUMENTOS = 5;
  readonly MAX_BYTES = 5 * 1024 * 1024; // 5 MB
  readonly MAX_CARACTERES_JUSTIFICACION = 5000; // Igual al límite del T01 (decisión del PO)
  relatoTexto = '';
  esEdicion = false;

  isDragging = false;

  // Modal propio de Confirmación
  modalConfirmacionAbierto = false;
  modalConfirmacionTitulo = '';
  modalConfirmacionMensaje = '';
  modalConfirmacionAccion: (() => void) | null = null;

  // Temporizador dinámico para cuenta regresiva (CA3)
  private tickerSub: Subscription | null = null;
  ahoraMs: number = Date.now();

  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService,
    private renderer: Renderer2,
    private notifications: NotificationService,
    private expedienteApi: ExpedienteApiService,
    private scrollLock: ModalScrollLockService
  ) {}

  ngOnInit(): void {
    const subPerfil = this.auth.perfil$.subscribe(perfil => {
      this.socioActual = perfil ? `${perfil.first_name} ${perfil.last_name}` : '';
      this.cargarMisExpedientes();
    });
    this.subs.push(subPerfil);

    const subExp = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
      if (!this.misExpedientes || this.misExpedientes.length === 0) {
        this.filtrarMisExpedientes();
      }
    });
    this.subs.push(subExp);

    const subSocios = this.dataService.socios$.subscribe(() => {
      this.actualizarSaldoNeto();
    });
    this.subs.push(subSocios);

    // Actualizador dinámico del reloj cada segundo (evita memory leaks desuscribiéndose en ngOnDestroy)
    this.tickerSub = interval(1000).subscribe(() => {
      this.ahoraMs = Date.now();
    });

    this.cargarMisExpedientes();
  }

  cargarMisExpedientes(): void {
    this.expedienteApi.listarMisExpedientes().subscribe({
      next: (expedientesApi) => {
        if (expedientesApi && Array.isArray(expedientesApi) && expedientesApi.length > 0) {
          this.misExpedientes = expedientesApi.map(e => this.mapearExpedienteApi(e));
          this.sincronizarDetalleAbierto();
          this.actualizarSaldoNeto();
        } else {
          this.filtrarMisExpedientes();
        }
      },
      error: () => {
        this.filtrarMisExpedientes();
      }
    });
  }

  /** El detalle abierto es una copia: se reapunta a la lista recién recibida para que botones y avisos reflejen el backend. */
  private sincronizarDetalleAbierto(): void {
    if (!this.expedienteDetalle) return;
    const actualizado = this.misExpedientes.find(e => e.id === this.expedienteDetalle!.id);
    if (actualizado) {
      this.expedienteDetalle = actualizado;
    }
  }

  private mapearExpedienteApi(raw: any): Expediente {
    const tieneDescargoReal = Boolean(
      raw.descargo_presentado && (
        (raw.descargo_texto && raw.descargo_texto.trim().length > 0) ||
        raw.descargo_causal ||
        raw.descargo_archivo ||
        (raw.evidencias && raw.evidencias.length > 0)
      )
    );

    const descargoObj = tieneDescargoReal ? {
      tipo: raw.descargo_tipo || 'T02_CERTIFICADO',
      causal: raw.descargo_causal,
      archivo: raw.descargo_archivo,
      texto: raw.descargo_texto || '',
      fecha: raw.descargo_presentado_at || raw.created_at || '',
      evidencias: raw.evidencias || []
    } : undefined;

    const justificacionAprobada = Boolean(
      raw.justificacion_aprobada ||
      (raw.descargo_presentado && (raw.estado === 'emitido' || raw.descargo?.puntaje_ratificado === 0)) ||
      (raw.descargos && raw.descargos.some((d: any) => d.puntaje_ratificado === 0))
    );

    return {
      id: String(raw.id),
      numero: raw.numero,
      socio: raw.socio_nombre || '',
      legajo: raw.socio_legajo || '',
      subcomision: raw.subcomision || 'General',
      motivo: raw.motivo || '',
      titulo: raw.titulo || raw.motivo || '',
      razon: raw.razon || raw.motivo || '',
      solicitante: raw.solicitante || raw.creador || '',
      creador: raw.creador || raw.solicitante || '',
      fechaCreacion: raw.created_at || '',
      estado: (() => {
        const limiteMs = raw.plazo_limite_at ? new Date(raw.plazo_limite_at).getTime() : 0;
        const vencido = (limiteMs > 0 && !isNaN(limiteMs))
          ? Date.now() > limiteMs
          : (raw.horas_restantes !== undefined && raw.horas_restantes <= 0 && raw.plazo_limite_at);
        return ((raw.estado || '').toLowerCase().trim() === 'justificando' && vencido)
          ? 'revision_resolucion'
          : raw.estado;
      })(),
      urgencia: raw.urgencia,
      horasRestantes: raw.horas_restantes ?? 0,
      tipo: (raw.puntos || 0) < 0 ? 'falta' : 'merito',
      puntos: raw.puntos || 0,
      esFelicitacion: !!raw.es_felicitacion || Math.abs(Number(raw.puntos) - 0.33) < 0.01,
      esLlamado: !!raw.es_llamado || Math.abs(Number(raw.puntos) - (-0.33)) < 0.01,
      justificacionAprobada: justificacionAprobada,
      plazoInicioAt: raw.plazo_inicio_at,
      plazoLimiteAt: raw.plazo_limite_at,
      esT01: !!raw.es_t01,
      descargoPresentado: raw.descargo_presentado,
      descargo: descargoObj,
      evidencias: raw.evidencias || [],
      cantidadSocios: raw.socios ? raw.socios.length : 1,
      sociosInvolucrados: raw.socios || [],
      reglamento_asociado: raw.reglamento_asociado || raw.reglamentoAsociado || '',
      reglamentoAsociado: raw.reglamento_asociado || raw.reglamentoAsociado || '',
      reglamentos_respaldantes: Array.isArray(raw.reglamentos_respaldantes)
        ? raw.reglamentos_respaldantes
        : Array.isArray(raw.reglamentosRespaldantes)
        ? raw.reglamentosRespaldantes
        : [],
      reglamentosRespaldantes: Array.isArray(raw.reglamentos_respaldantes)
        ? raw.reglamentos_respaldantes
        : Array.isArray(raw.reglamentosRespaldantes)
        ? raw.reglamentosRespaldantes
        : []
    };
  }

  /** Los expedientes del socio en sesión y cálculo de saldo neto de expedientes emitidos. */
  private filtrarMisExpedientes(): void {
    const perfil = this.auth.getPerfil();
    const nombre = this.socioActual.trim().toLowerCase();
    const legajo = perfil?.legajo ? String(perfil.legajo).trim().toLowerCase() : '';

    this.misExpedientes = (nombre || legajo)
      ? this.expedientes.filter(e => {
          const matchNombre = !!(nombre && e.socio && e.socio.trim().toLowerCase() === nombre);
          const matchLegajo = !!(legajo && e.legajo && String(e.legajo).trim().toLowerCase() === legajo);
          const matchInvolucrado = (e.sociosInvolucrados || []).some(s => {
            const sNombre = (s.nombre || '').trim().toLowerCase();
            const sLegajo = s.legajo ? String(s.legajo).trim().toLowerCase() : '';
            return (nombre && sNombre === nombre) || (legajo && sLegajo === legajo);
          });
          return matchNombre || matchLegajo || matchInvolucrado;
        })
      : [];
    this.actualizarSaldoNeto();
  }

  /**
   * Calcula el saldo de puntos estrictamente a partir de los expedientes emitidos (cerrados).
   * Aplica la exención de puntos para justificaciones aprobadas y la consolidación 3:1 de felicitaciones/llamados.
   */
  public actualizarSaldoNeto(): void {
    const emitidos = this.misExpedientes.filter(e => e.estado === 'emitido');
    let puntosOrdinarios = 0;
    let felCount = 0;
    let llamCount = 0;

    for (const exp of emitidos) {
      // Ignorar aquellos con justificación aprobada (descargo presentado con resolución o causal aprobada)
      const esJustAprobada = Boolean(
        exp.justificacionAprobada ||
        (exp.descargoPresentado && (exp.tipo === 'falta' || Number(exp.puntos) < 0))
      );
      if (esJustAprobada) {
        continue;
      }

      const pts = Number(exp.puntos || 0);
      if (exp.esFelicitacion || Math.abs(pts - 0.33) < 0.01) {
        felCount++;
      } else if (exp.esLlamado || Math.abs(pts - (-0.33)) < 0.01) {
        llamCount++;
      } else {
        puntosOrdinarios += pts;
      }
    }

    this.saldoNeto = puntosOrdinarios + Math.floor(felCount / 3) - Math.floor(llamCount / 3);
    this.felicitaciones = felCount % 3;
    this.llamadosAtencion = llamCount % 3;
  }

  ngOnDestroy(): void {
    if (this.tickerSub) {
      this.tickerSub.unsubscribe();
      this.tickerSub = null;
    }
    this.subs.forEach(s => s.unsubscribe());
    this.removerScrollBloqueo();
  }

  /**
   * Determina si el expediente tiene su plazo vencido según el timestamp del límite.
   */
  esPlazoVencido(exp: Expediente): boolean {
    if (!exp.plazoLimiteAt) {
      return exp.horasRestantes <= 0;
    }
    const limiteMs = new Date(exp.plazoLimiteAt).getTime();
    return this.ahoraMs > limiteMs;
  }

  /**
   * Formato de fecha exacta de vencimiento: "Vence: Jueves 15/10/2026 - 18:00 hs".
   */
  getDeadlineLabel(exp: Expediente): string {
    if (!exp.plazoLimiteAt) {
      return 'Vencimiento no fijado';
    }
    const d = new Date(exp.plazoLimiteAt);
    if (isNaN(d.getTime())) {
      return 'Fecha inválida';
    }
    const formatter = new Intl.DateTimeFormat('es-AR', {
      timeZone: 'America/Argentina/Buenos_Aires',
      weekday: 'long',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
    const parts = formatter.formatToParts(d);
    const map: { [key: string]: string } = {};
    parts.forEach(p => (map[p.type] = p.value));
    const rawWeekday = map['weekday'] || '';
    const diaNom = rawWeekday.charAt(0).toUpperCase() + rawWeekday.slice(1);

    return `Vence: ${diaNom} ${map['day']}/${map['month']}/${map['year']} - ${map['hour']}:${map['minute']} hs`;
  }

  // Modal Detalle
  modalDetalleAbierto = false;
  expedienteDetalle: Expediente | null = null;
  reglamentoExpandidoModal: string | null = null;

  /** Historial inmutable del descargo, proveniente del backend (no del estado local). */
  historialDescargo: LogJustificativo[] = [];

  getReglamentosCitas(exp: Expediente | null | undefined): ReglamentoCiteView[] {
    if (!exp) return [];
    const list =
      exp.reglamentos_respaldantes && exp.reglamentos_respaldantes.length > 0
        ? exp.reglamentos_respaldantes
        : exp.reglamentosRespaldantes;
    const single = exp.reglamento_asociado || exp.reglamentoAsociado;
    return parseReglamentosList(list, single);
  }

  toggleReglamentoExpandido(raw: string): void {
    this.reglamentoExpandidoModal = this.reglamentoExpandidoModal === raw ? null : raw;
  }

  get reglamentoExpandidoDetalle(): ReglamentoCiteView | null {
    if (!this.reglamentoExpandidoModal) return null;
    return parseReglamentoCite(this.reglamentoExpandidoModal);
  }

  abrirModalDetalle(exp: Expediente): void {
    this.expedienteDetalle = exp;
    this.modalDetalleAbierto = true;
    this.reglamentoExpandidoModal = null;
    this.actualizarScrollBloqueo();
    this.limpiarApelacion();
    if (exp.esT01) {
      this.cargarHistorialT01(exp.id);
    } else {
      this.cargarHistorialDescargo(exp.id);
    }
    this.expedienteApi.obtenerDetalleExpediente(exp.id, 'mis_expedientes').subscribe({
      next: (detalle) => {
        if (this.modalDetalleAbierto && this.expedienteDetalle?.id === String(detalle.id)) {
          this.expedienteDetalle = this.mapearExpedienteApi(detalle);
        }
      },
      error: () => {}
    });
    setTimeout(() => {
      const modalBody = (document.querySelector('.modal-dialog-tribunal .modal-detalle-body') ||
                         document.querySelector('.modal-dialog-custom .card-body') ||
                         document.querySelector('.modal-dialog-custom')) as HTMLElement;
      if (modalBody) {
        modalBody.focus({ preventScroll: true });
      }
    }, 50);
  }

  cerrarModalDetalle(): void {
    this.modalDetalleAbierto = false;
    this.expedienteDetalle = null;
    this.reglamentoExpandidoModal = null;
    this.historialDescargo = [];
    this.limpiarApelacion();
    this.actualizarScrollBloqueo();
  }

  // --- Apelación del T01 (PB-02): reemplaza al descargo T02/T03 ---

  readonly MIN_CARACTERES_APELACION = 20;
  historialT01: HistorialT01DTO | null = null;
  apelacionAbierta = false;
  textoApelacion = '';
  enviandoApelacion = false;

  /** Período de apelación vigente del socio en sesión (el backend devuelve sólo los propios). */
  get miPeriodoApelacion(): PeriodoApelacionDTO | null {
    const periodos = this.historialT01?.periodos || [];
    return periodos.length ? periodos[periodos.length - 1] : null;
  }

  get ultimaApelacion() {
    const apelaciones = this.historialT01?.apelaciones || [];
    return apelaciones.length ? apelaciones[apelaciones.length - 1] : null;
  }

  get puedeApelar(): boolean {
    const periodo = this.miPeriodoApelacion;
    return !!periodo && periodo.abierto && this.ahoraMs <= new Date(periodo.limite_at).getTime();
  }

  private limpiarApelacion(): void {
    this.historialT01 = null;
    this.apelacionAbierta = false;
    this.textoApelacion = '';
    this.enviandoApelacion = false;
  }

  private cargarHistorialT01(expedienteId: string): void {
    this.expedienteApi.obtenerHistorialT01(expedienteId).subscribe({
      next: historial => {
        if (this.expedienteDetalle?.id === expedienteId) {
          this.historialT01 = historial;
        }
      },
      error: err => this.notifications.error(httpErrorMessage(err, 'No se pudo cargar la apelación.'))
    });
  }

  abrirApelacion(): void {
    this.textoApelacion = this.ultimaApelacion?.texto || '';
    this.apelacionAbierta = true;
  }

  enviarApelacion(): void {
    const exp = this.expedienteDetalle;
    if (!exp || this.enviandoApelacion) return;
    const texto = this.textoApelacion.trim();
    if (texto.length < this.MIN_CARACTERES_APELACION) {
      this.notifications.error(`Escribí tu apelación con al menos ${this.MIN_CARACTERES_APELACION} caracteres.`);
      return;
    }
    if (texto.length > this.MAX_CARACTERES_JUSTIFICACION) {
      this.notifications.error(`La apelación no puede superar los ${this.MAX_CARACTERES_JUSTIFICACION} caracteres.`);
      return;
    }
    this.enviandoApelacion = true;
    this.expedienteApi.apelarT01(exp.id, texto).subscribe({
      next: historial => {
        this.enviandoApelacion = false;
        this.apelacionAbierta = false;
        this.historialT01 = historial;
        this.notifications.success('Apelación registrada. Te enviamos la constancia por mail.');
      },
      error: err => {
        this.enviandoApelacion = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo registrar la apelación.'));
      }
    });
  }

  /** Consulta las versiones del descargo y las mapea a las filas de la tabla de auditoría. */
  private cargarHistorialDescargo(expedienteId: string): void {
    this.expedienteApi.obtenerVersionesDescargo(expedienteId).subscribe({
      next: (versiones) => {
        if (this.expedienteDetalle?.id !== expedienteId) {
          return;
        }
        this.historialDescargo = versiones.map(v => this.mapearVersionAFila(v));
      },
      error: () => {
        this.historialDescargo = [];
        this.notifications.error('No se pudo cargar el historial del descargo.');
      }
    });
  }

  private refrescarHistorialSiEstaAbierto(expedienteId: string): void {
    if (this.modalDetalleAbierto && this.expedienteDetalle?.id === expedienteId) {
      this.cargarHistorialDescargo(expedienteId);
    }
  }

  private mapearVersionAFila(v: DescargoVersionDto): LogJustificativo {
    const operaciones: { [op in OperacionDescargo]: LogJustificativo['operacion'] } = {
      PRESENTADO: 'CREACION',
      CORREGIDO: 'EDICION',
      RETIRADO: 'ELIMINACION'
    };
    const modalidad = v.tipo === 'T02_CERTIFICADO' ? 'Con Certificado' : 'Otros';
    const cantidad = (v.evidencias || []).length;
    const comprobantes = `${cantidad} ${cantidad === 1 ? 'comprobante' : 'comprobantes'}`;
    const partes = [`v${v.numero}`, modalidad];
    if (v.causal && v.causal !== 'Otro' && v.causal !== 'Otros') {
      partes.push(v.causal);
    }
    partes.push(comprobantes);

    return {
      operacion: operaciones[v.operacion],
      accionLabel: v.operacion_display,
      usuario: `${v.socio_nombre} (Legajo ${v.socio_legajo})`,
      legajo: v.socio_legajo,
      timestamp: this.formatearMarcaDeTiempo(v.created_at),
      detalle: partes.join(' · ')
    };
  }

  private formatearMarcaDeTiempo(iso: string): string {
    const d = new Date(iso);
    if (isNaN(d.getTime())) {
      return '';
    }
    const partes = new Intl.DateTimeFormat('es-AR', {
      timeZone: 'America/Argentina/Buenos_Aires',
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).formatToParts(d);
    const mapa: { [key: string]: string } = {};
    partes.forEach(p => (mapa[p.type] = p.value));
    return `${mapa['day']}/${mapa['month']}/${mapa['year']} ${mapa['hour']}:${mapa['minute']} hs`;
  }

  /** Extrae el mensaje legible de una respuesta de error de la API (detail o primer error de campo). */
  private extraerMensajeError(err: any, porDefecto: string): string {
    const cuerpo = err?.error;
    if (cuerpo?.detail) {
      return String(cuerpo.detail);
    }
    if (cuerpo && typeof cuerpo === 'object') {
      const primero = Object.values(cuerpo)[0];
      const mensaje = Array.isArray(primero) ? primero[0] : primero;
      if (typeof mensaje === 'string' && mensaje) {
        return mensaje;
      }
    }
    return porDefecto;
  }

  /**
   * Formato dinámico compacto para el badge: "14d 17h" o "04h 12m" o "Plazo expirado".
   */
  getCompactCountdownLabel(exp: Expediente): string {
    if (!exp.plazoLimiteAt) {
      return exp.horasRestantes > 0 ? `${exp.horasRestantes}h` : '';
    }
    const limiteMs = new Date(exp.plazoLimiteAt).getTime();
    const diffMs = limiteMs - this.ahoraMs;

    if (diffMs <= 0) {
      return 'Expirado';
    }

    const segundosTotales = Math.floor(diffMs / 1000);
    const dias = Math.floor(segundosTotales / 86400);
    const horas = Math.floor((segundosTotales % 86400) / 3600);
    const minutos = Math.floor((segundosTotales % 3600) / 60);

    const horasStr = String(horas).padStart(2, '0');
    const minsStr = String(minutos).padStart(2, '0');

    if (dias > 0) {
      return `${dias}d ${horasStr}h`;
    }
    return `${horasStr}h ${minsStr}m`;
  }

  /**
   * Formato dinámico del contador: "2d 04h 15m restantes" o "Plazo expirado".
   */
  getCountdownLabel(exp: Expediente): string {
    if (!exp.plazoLimiteAt) {
      return `${exp.horasRestantes}h restantes`;
    }
    const limiteMs = new Date(exp.plazoLimiteAt).getTime();
    const diffMs = limiteMs - this.ahoraMs;

    if (diffMs <= 0) {
      return 'Plazo expirado';
    }

    const segundosTotales = Math.floor(diffMs / 1000);
    const dias = Math.floor(segundosTotales / 86400);
    const horas = Math.floor((segundosTotales % 86400) / 3600);
    const minutos = Math.floor((segundosTotales % 3600) / 60);

    const horasStr = String(horas).padStart(2, '0');
    const minsStr = String(minutos).padStart(2, '0');

    if (dias > 0) {
      return `${dias}d ${horasStr}h ${minsStr}m restantes`;
    }
    const segs = segundosTotales % 60;
    const segsStr = String(segs).padStart(2, '0');
    return `${horasStr}h ${minsStr}m ${segsStr}s restantes`;
  }

  abrirModalDescargo(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.esEdicion = false;
    this.tipoDescargo = 'T02_CERTIFICADO';
    this.causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
    this.nombreArchivo = '';
    this.archivosSeleccionados = [];
    this.evidenciasExistentes = [];
    this.relatoTexto = '';
    this.modalAbierto = true;
    this.actualizarScrollBloqueo();
  }

  abrirModalEditarDescargo(exp: Expediente): void {
    if (!exp.descargo) return;
    this.expedienteSeleccionado = exp;
    this.esEdicion = true;
    this.tipoDescargo = exp.descargo.tipo;
    if (this.tipoDescargo === 'T03_EXTRAORDINARIO') {
      this.causalSeleccionada = 'Otro';
    } else {
      this.causalSeleccionada = exp.descargo.causal || 'Examen Académico Universitario en UTN FRC';
    }
    this.nombreArchivo = exp.descargo.archivo || '';
    this.archivosSeleccionados = [];
    this.evidenciasExistentes = exp.descargo.evidencias ? [...exp.descargo.evidencias] : [];
    this.relatoTexto = exp.descargo.texto || '';
    this.modalAbierto = true;
    this.actualizarScrollBloqueo();
  }

  eliminarDescargo(exp: Expediente): void {
    if (!exp.descargo) return;
    this.abrirConfirmacion(
      'Retirar descargo',
      `¿Confirmas el retiro del descargo del expediente ${this.formatCaseNumber(exp.numero)}? Tu escrito y sus comprobantes quedan registrados en el historial y podrás presentar uno nuevo mientras el plazo siga abierto.`,
      () => {
        const perfil = this.auth.getPerfil();
        const nombre = perfil ? `${perfil.first_name} ${perfil.last_name}` : this.socioActual;
        const legajo = perfil?.legajo || '';

        // El retiro es una baja lógica en el backend: solo se refleja en pantalla si el servidor lo acepta.
        this.expedienteApi.eliminarDescargo(exp.id).subscribe({
          next: () => {
            this.dataService.eliminarDescargo(exp.id, { nombre, legajo });
            this.cargarMisExpedientes();
            this.refrescarHistorialSiEstaAbierto(exp.id);
            this.notifications.info(
              `Descargo del expediente ${this.formatCaseNumber(exp.numero)} retirado. Queda registrado en el historial.`
            );
          },
          error: (err) => {
            this.notifications.error(
              this.extraerMensajeError(err, 'No se pudo retirar el descargo. Intenta nuevamente.')
            );
          }
        });
      }
    );
  }

  cerrarModal(): void {
    this.modalAbierto = false;
    this.expedienteSeleccionado = null;
    this.archivosSeleccionados = [];
    this.evidenciasExistentes = [];
    this.actualizarScrollBloqueo();
  }

  private actualizarScrollBloqueo(): void {
    const estaAbierto = this.modalDetalleAbierto || this.modalAbierto || this.modalConfirmacionAbierto;
    const body = document.body;
    const docElem = document.documentElement;
    const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;

    if (estaAbierto) {
      this.renderer.addClass(body, 'modal-open');
      this.renderer.setStyle(body, 'overflow', 'hidden');
      this.renderer.setStyle(docElem, 'overflow', 'hidden');
      if (mainPanel) {
        this.renderer.setStyle(mainPanel, 'overflow', 'hidden');
      }
      this.scrollLock.lock();
    } else {
      this.scrollLock.reset();
      this.removerScrollBloqueo();
    }
  }

  private removerScrollBloqueo(): void {
    const body = document.body;
    const docElem = document.documentElement;
    const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;

    this.renderer.removeClass(body, 'modal-open');
    this.renderer.removeStyle(body, 'overflow');
    this.renderer.removeStyle(docElem, 'overflow');
    if (mainPanel) {
      this.renderer.removeStyle(mainPanel, 'overflow');
    }
  }

  abrirConfirmacion(titulo: string, mensaje: string, onConfirm: () => void): void {
    this.modalConfirmacionTitulo = titulo;
    this.modalConfirmacionMensaje = mensaje;
    this.modalConfirmacionAccion = onConfirm;
    this.modalConfirmacionAbierto = true;
    this.actualizarScrollBloqueo();
  }

  cerrarConfirmacion(): void {
    this.modalConfirmacionAbierto = false;
    this.modalConfirmacionAccion = null;
    this.actualizarScrollBloqueo();
  }

  confirmarAccion(): void {
    if (this.modalConfirmacionAccion) {
      this.modalConfirmacionAccion();
    }
    this.cerrarConfirmacion();
  }

  get totalComprobantes(): number {
    return this.evidenciasExistentes.length + this.archivosSeleccionados.length;
  }

  get limiteActual(): number {
    return this.tipoDescargo === 'T03_EXTRAORDINARIO' ? 5 : 3;
  }

  get puedeSubirMas(): boolean {
    return this.totalComprobantes < this.limiteActual;
  }

  onCausalChange(): void {
    if (this.causalSeleccionada === 'Otro') {
      this.tipoDescargo = 'T03_EXTRAORDINARIO';
    } else {
      this.tipoDescargo = 'T02_CERTIFICADO';
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
  }

  onFileDropped(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = false;
    if (event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
      this.procesarArchivos(Array.from(event.dataTransfer.files));
    }
  }

  onFileSelected(event: any): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    this.procesarArchivos(Array.from(input.files));
    input.value = '';
  }

  procesarArchivos(nuevos: File[]): void {
    if (!nuevos || nuevos.length === 0) return;
    const limite = this.limiteActual;
    const totalComprobantes = this.evidenciasExistentes.length + this.archivosSeleccionados.length + nuevos.length;

    if (totalComprobantes > limite) {
      this.notifications.error(`Solo se admite un máximo de ${limite} documentos en total.`);
      return;
    }

    for (const f of nuevos) {
      if (f.size > this.MAX_BYTES) {
        this.notifications.error(`El archivo "${f.name}" supera el límite de 5 MB.`);
        return;
      }
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.jpg', '.jpeg', '.png'].includes(ext)) {
        this.notifications.error(`El archivo "${f.name}" no tiene un formato válido (PDF, JPG, PNG).`);
        return;
      }

      // Validación de duplicados: chequear contra archivos ya guardados
      const yaExisteEnCustodia = this.evidenciasExistentes.some(
        ev => (ev.nombre_original || ev.name || '').toLowerCase() === f.name.toLowerCase()
      );
      if (yaExisteEnCustodia) {
        this.notifications.error(`El documento "${f.name}" ya se encuentra adjunto.`);
        return;
      }

      // Validación de duplicados: chequear contra archivos ya seleccionados en esta tanda
      const yaSeleccionado = this.archivosSeleccionados.some(
        sel => sel.name.toLowerCase() === f.name.toLowerCase() && sel.size === f.size
      );
      if (yaSeleccionado) {
        this.notifications.error(`El archivo "${f.name}" ya está seleccionado.`);
        return;
      }

      this.archivosSeleccionados.push(f);
    }
    this.nombreArchivo = this.archivosSeleccionados.map(f => f.name).join(', ');
  }

  removerArchivo(index: number): void {
    const archivo = this.archivosSeleccionados[index];
    const nombre = archivo ? archivo.name : 'este archivo';
    this.abrirConfirmacion(
      'Quitar archivo',
      `¿Confirmas que deseas quitar el archivo "${nombre}" de la selección?`,
      () => {
        this.archivosSeleccionados.splice(index, 1);
        this.nombreArchivo = this.archivosSeleccionados.map(f => f.name).join(', ');
      }
    );
  }

  removerEvidenciaExistente(index: number): void {
    const ev = this.evidenciasExistentes[index];
    const nombre = ev ? (ev.nombre_original || ev.name) : 'este documento';
    this.abrirConfirmacion(
      'Eliminar documento',
      `¿Confirmas que deseas eliminar el documento "${nombre}"?`,
      () => {
        this.evidenciasExistentes.splice(index, 1);
        this.notifications.info(`Documento "${nombre}" eliminado del justificativo.`);
      }
    );
  }

  formatFileSize(bytes: number): string {
    if (!bytes) return '0 B';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  descargarEvidencia(ev: any): void {
    if (!this.expedienteDetalle) return;
    this.expedienteApi.descargarEvidencia(this.expedienteDetalle.id, ev.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = ev.nombre_original || 'comprobante';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        this.notifications.info(`Descargando comprobante: ${ev.nombre_original}`);
      },
      error: () => {
        this.notifications.error('Error al descargar el comprobante probatorio.');
      }
    });
  }

  enviarDescargo(): void {
    if (!this.expedienteSeleccionado) return;

    const totalComprobantes = this.evidenciasExistentes.length + this.archivosSeleccionados.length;

    if (totalComprobantes > this.LIMITE_DOCUMENTOS) {
      this.notifications.error(`Solo se permite un máximo de ${this.LIMITE_DOCUMENTOS} documentos.`);
      return;
    }

    if (this.tipoDescargo === 'T02_CERTIFICADO') {
      if (totalComprobantes === 0 && !this.nombreArchivo) {
        this.notifications.error('Debe adjuntar al menos un documento.');
        return;
      }
    } else {
      if (!this.relatoTexto.trim()) {
        this.notifications.error('Por favor ingrese el motivo de la justificación.');
        return;
      }
    }

    if (this.relatoTexto && this.relatoTexto.length > this.MAX_CARACTERES_JUSTIFICACION) {
      this.notifications.error(
        `El motivo o justificación no puede superar los ${this.MAX_CARACTERES_JUSTIFICACION} caracteres.`
      );
      return;
    }

    const perfil = this.auth.getPerfil();
    const nombre = perfil ? `${perfil.first_name} ${perfil.last_name}` : this.socioActual;
    const legajo = perfil?.legajo || '';
    const expId = this.expedienteSeleccionado.id;
    const textoAEnviar = this.relatoTexto ? this.relatoTexto.trim() : '';

    const guardarEnDataService = (todasLasEvidencias: any[]) => {
      this.dataService.enviarDescargo(
        expId,
        this.tipoDescargo,
        {
          causal: this.tipoDescargo === 'T02_CERTIFICADO' ? this.causalSeleccionada : 'Otro',
          archivo: this.nombreArchivo || (todasLasEvidencias.length > 0 ? todasLasEvidencias[0].nombre_original : undefined),
          archivos: todasLasEvidencias.map(e => e.nombre_original || e.name || 'documento'),
          texto: textoAEnviar || (this.tipoDescargo === 'T02_CERTIFICADO' ? `Justificación presentada bajo causal: ${this.causalSeleccionada}.` : ''),
          evidencias: todasLasEvidencias
        },
        {
          nombre,
          legajo,
          esEdicion: this.esEdicion
        }
      );
      this.notifications.success('Justificación y documentos registrados correctamente.');
      this.subiendoArchivos = false;
      this.cerrarModal();
      this.cargarMisExpedientes();
      this.refrescarHistorialSiEstaAbierto(expId);
    };

    // Un rechazo del servidor (plazo vencido, validación) no se presenta como éxito ni cierra el modal.
    const manejarRechazo = (err: any) => {
      this.subiendoArchivos = false;
      this.notifications.error(
        this.extraerMensajeError(err, 'No se pudo registrar el descargo. Intenta nuevamente.')
      );
    };

    if (this.archivosSeleccionados.length > 0) {
      this.subiendoArchivos = true;
      this.expedienteApi.subirEvidencias(expId, this.archivosSeleccionados, this.tipoDescargo).subscribe({
        next: (nuevasEvidencias) => {
          const todasLasEvidencias = [...this.evidenciasExistentes, ...nuevasEvidencias];
          const ids = todasLasEvidencias.map(e => e.id);
          this.expedienteApi.presentarDescargo(expId, {
            tipo: this.tipoDescargo,
            causal: this.tipoDescargo === 'T02_CERTIFICADO' ? this.causalSeleccionada : undefined,
            texto: textoAEnviar,
            evidencia_ids: ids
          }).subscribe({
            next: () => guardarEnDataService(todasLasEvidencias),
            error: manejarRechazo
          });
        },
        error: (err) => {
          this.subiendoArchivos = false;
          const msg = err?.error?.detail || 'Error al guardar los documentos.';
          this.notifications.error(msg);
        }
      });
    } else {
      const ids = this.evidenciasExistentes.map(e => e.id);
      this.expedienteApi.presentarDescargo(expId, {
        tipo: this.tipoDescargo,
        causal: this.tipoDescargo === 'T02_CERTIFICADO' ? this.causalSeleccionada : undefined,
        texto: textoAEnviar,
        evidencia_ids: ids
      }).subscribe({
        next: () => guardarEnDataService(this.evidenciasExistentes),
        error: manejarRechazo
      });
    }
  }

  getBadgeClaseOperacion(operacion: string): string {
    switch (operacion) {
      case 'CREACION': return 'badge-success';
      case 'EDICION': return 'badge-info';
      case 'ELIMINACION': return 'badge-danger';
      default: return 'badge-secondary';
    }
  }

  formatCaseNumber(numero: string | null | undefined): string {
    return formatCaseNumber(numero);
  }

  formatSolicitante(exp: Expediente | null | undefined): string {
    if (!exp) return 'Comisión Directiva';
    const creador = (exp.solicitante || exp.creador || '').trim();
    if (creador) {
      const match = /^(.+?)\s*\((.+?)\)$/.exec(creador);
      if (match) {
        const nombrePart = match[1].trim();
        const legajoPart = match[2].trim();
        return `${legajoPart} - ${nombrePart}`;
      }
      return creador;
    }
    return 'Comisión Directiva';
  }

  getEstadoLabel(estado: string, exp?: Expediente): string {
    const normalizado = (estado || '').toLowerCase().trim();
    if (normalizado === 'justificando' && exp) {
      if (this.esPlazoVencido(exp)) {
        return 'En Revisión';
      }
      const tiempo = this.getCompactCountdownLabel(exp);
      return tiempo ? `Justificando ${tiempo}` : 'Justificando';
    }
    if (normalizado === 'revision_resolucion') {
      return 'En Revisión';
    }

    switch (normalizado) {
      case 'creado': return 'Creado';
      case 'justificando': return 'Justificando';
      case 'revision_resolucion':
      case 'espera_resolucion': return 'En Revisión';
      case 'pendiente_firma': return 'Pendiente de Firma';
      case 'pendiente_correos': return 'Pendiente de Envío';
      case 'emitido': return 'Emitido';
      default: return humanizeEstado(estado);
    }
  }

  getEstadoBadgeClass(estado: string, exp?: Expediente): string {
    const normalizado = (estado || '').toLowerCase().trim();
    if (normalizado === 'justificando' && exp && this.esPlazoVencido(exp)) {
      return 'badge-mat-info';
    }
    switch (normalizado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion':
      case 'espera_resolucion': return 'badge-mat-info';
      case 'pendiente_firma': return 'badge-mat-primary';
      case 'pendiente_correos': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }


  onTableKeyDown(event: KeyboardEvent, exp: Expediente): void {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      this.abrirModalDetalle(exp);
    }
  }

  getCantidadInvolucrados(exp: Expediente): number {
    if (typeof exp.cantidadSocios === 'number' && exp.cantidadSocios > 0) {
      return exp.cantidadSocios;
    }
    if (exp.sociosInvolucrados && exp.sociosInvolucrados.length > 0) {
      return exp.sociosInvolucrados.length;
    }
    const raw = (exp as any).involucrados;
    if (Array.isArray(raw) && raw.length > 0) {
      return raw.length;
    }
    return 1;
  }

  getUrgenciaLabel(urgencia?: string): string {
    switch ((urgencia || '').toLowerCase()) {
      case 'urgente': return 'URGENTE';
      case 'baja': return 'BAJA';
      case 'normal':
      default:
        return 'NORMAL';
    }
  }

  getUrgenciaBadgeClass(urgencia?: string): string {
    switch ((urgencia || '').toLowerCase()) {
      case 'urgente': return 'badge-urgencia-urgente badge-mat-danger';
      case 'baja': return 'badge-urgencia-baja badge-mat-info';
      case 'normal':
      default:
        return 'badge-urgencia-normal badge-mat-info';
    }
  }

  getUrgenciaIcon(urgencia?: string): string {
    switch ((urgencia || '').toLowerCase()) {
      case 'urgente': return 'priority_high';
      case 'baja': return 'arrow_downward';
      case 'normal':
      default:
        return 'remove';
    }
  }

  get expedientesOrdenados(): Expediente[] {
    let lista = [...this.misExpedientes];
    if (this.filtroTab === 'en_tramite') {
      lista = lista.filter((e) => e.estado !== 'emitido');
    } else if (this.filtroTab === 'resueltos') {
      lista = lista.filter((e) => e.estado === 'emitido');
    }
    lista.sort((a, b) => {
      let valA: any = (a as any)[this.columnaOrden];
      let valB: any = (b as any)[this.columnaOrden];
      if (this.columnaOrden === 'titulo') {
        valA = a.titulo || a.motivo || '';
        valB = b.titulo || b.motivo || '';
      }
      if (this.columnaOrden === 'numero') {
        const parseNum = (str: string) => {
          const s = str || '';
          let m = s.match(/(?:EXP-)?0*(\d+)\/(\d{4})/i);
          if (m) {
            return { num: parseInt(m[1], 10), year: parseInt(m[2], 10) };
          }
          m = s.match(/(?:EXP-)?(\d{4})-(\d+)/i);
          if (m) {
            return { num: parseInt(m[2], 10), year: parseInt(m[1], 10) };
          }
          return null;
        };
        const pA = parseNum(a.numero || '');
        const pB = parseNum(b.numero || '');
        if (pA && pB) {
          if (pA.year !== pB.year) {
            return this.ordenAscendente ? pB.year - pA.year : pA.year - pB.year;
          }
          return this.ordenAscendente ? pA.num - pB.num : pB.num - pA.num;
        }
        valA = a.numero || '';
        valB = b.numero || '';
      }
      if (this.columnaOrden === 'involucrados') {
        valA = this.getCantidadInvolucrados(a);
        valB = this.getCantidadInvolucrados(b);
      }
      if (this.columnaOrden === 'urgencia') {
        valA = (a.urgencia || 'normal').toLowerCase();
        valB = (b.urgencia || 'normal').toLowerCase();
      }
      if (this.columnaOrden === 'fechaCreacion' || this.columnaOrden === 'fecha') {
        valA = new Date(a.fechaCreacion || 0).getTime();
        valB = new Date(b.fechaCreacion || 0).getTime();
      }
      if (this.columnaOrden === 'puntos') {
        valA = Number(a.puntos || 0);
        valB = Number(b.puntos || 0);
      }
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return this.ordenAscendente ? -1 : 1;
      if (valA > valB) return this.ordenAscendente ? 1 : -1;
      return 0;
    });
    return lista;
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

  getColorClasePuntos(puntos: number): string {
    if (puntos < -9.0) {
      return 'puntos-rojo';
    }
    if (puntos < -7.0) {
      return 'puntos-amarillo';
    }
    if (puntos < 0) {
      return 'puntos-gris';
    }
    return 'puntos-verde';
  }

  getHeaderClassPuntos(puntos: number): string {
    if (puntos < -9.0) {
      return 'card-header-danger';
    }
    if (puntos < -7.0) {
      return 'card-header-warning';
    }
    if (puntos < 0) {
      return 'card-header-secondary';
    }
    return 'card-header-success';
  }
}
