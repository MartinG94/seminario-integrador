import { Component, ElementRef, OnDestroy, OnInit, Renderer2, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

import {
  AntecedenteT03DTO,
  ArticuloReglamentoDTO,
  ExpedienteApiService,
  SolicitudMonitoreo,
  SolicitudT01,
  SolicitudT01Payload,
  TipoAccionT01
} from '../services/expediente-api.service';
import { PadronApiService, PadronSocio } from '../services/padron-api.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';
import type { NivelUrgencia } from '../services/tribunal-data.service';
import { SolicitudDetalleDialogComponent } from './solicitud-detalle-dialog/solicitud-detalle-dialog.component';
import { formatCaseNumber } from '../utils/case-number.util';
import { ModalScrollLockService } from '../services/modal-scroll-lock.service';
import {
  parseReglamentoCite,
  parseReglamentosList,
  ReglamentoCiteView
} from '../utils/reglamento-format.util';

export interface CatalogoReglamentoItem {
  raw: string;
  citaCorta: string;
  documento: 'Estatuto' | 'Reglamento Interno' | 'Normativa';
  articulo: string;
  inciso: string;
  seccion: string;
  cuerpo: string;
}

@Component({
  selector: 'app-solicitar-puntos',
  templateUrl: './solicitar-puntos.component.html',
  styleUrls: ['./solicitar-puntos.component.scss']
})
export class SolicitarPuntosComponent implements OnInit, OnDestroy {
  socios: PadronSocio[] = [];
  sociosSeleccionados: PadronSocio[] = [];
  socioBusqueda = new FormControl('');
  sociosFiltrados: PadronSocio[] = [];
  urgency: NivelUrgencia = 'normal';
  puntosSeleccionados: number | null = -1;
  causal = '';
  motivoTexto = '';
  titulo = '';
  razon = '';
  private _reglamentosDisponibles: string[] = [];
  get reglamentosDisponibles(): string[] {
    return this._reglamentosDisponibles;
  }
  set reglamentosDisponibles(value: string[]) {
    this._reglamentosDisponibles = value || [];
    this.actualizarCatalogoItemsModal();
  }

  private _articulosDisponibles: ArticuloReglamentoDTO[] = [];
  get articulosDisponibles(): ArticuloReglamentoDTO[] {
    return this._articulosDisponibles;
  }
  set articulosDisponibles(value: ArticuloReglamentoDTO[]) {
    this._articulosDisponibles = value || [];
    this.actualizarCatalogoItemsModal();
  }
  reglamentosSeleccionados: string[] = [];
  filtroReglamentos = '';
  modalReglamentosAbierto = false;
  filtroDocumentoModal: 'TODOS' | 'Reglamento Interno' | 'Estatuto' = 'TODOS';
  reglamentoExpandidoForm: string | null = null;
  catalogoItemsModal: CatalogoReglamentoItem[] = [];
  @ViewChild('modalSearchInput') modalSearchInput?: ElementRef<HTMLInputElement>;
  @ViewChild('modalReglamentosDialog') modalReglamentosDialog?: ElementRef<HTMLElement>;
  @ViewChild('modalReglamentosBody') modalReglamentosBody?: ElementRef<HTMLElement>;
  private elementoFocoPrevio: HTMLElement | null = null;
  anexoFecha = '';
  anexoLugar = '';
  anexoTestigos = '';
  anexoRelato = '';
  anexoExpandido = false;
  borradorId: string | null = null;
  estado: 'DRAFT' | 'ISSUED' | null = null;
  numeroExpediente: string | null = null;
  cargando = false;

  // Expedientes Referenciados / Antecedentes (Opcional)
  expedientesReferenciadosSeleccionados: AntecedenteT03DTO[] = [];
  modalExpedientesAbierto = false;
  catalogoExpedientesModal: AntecedenteT03DTO[] = [];
  cargandoCatalogoExpedientes = false;
  catalogoExpedientesCargado = false;

  // Panel Mis Solicitudes T01 (SCRUM-75 / PB-04)
  misSolicitudes: SolicitudMonitoreo[] = [];
  cargandoSolicitudes = false;
  failedToLoadRequests = false;
  busquedaControl = new FormControl('');
  estadoFiltro = new FormControl('');
  private destroy$ = new Subject<void>();

  // Ordenamiento de tabla (PB-04 / SCRUM-75)
  columnaOrden = 'numero';
  ordenAscendente = true;

  // Modal de Detalle de Solicitud (estilo Gestionar Expedientes)
  modalDetalleAbierto = false;
  solicitudSeleccionada: SolicitudMonitoreo | null = null;

  // Pestañas principales: 'nueva' (Formulario T01) vs 'creadas' (Mis Solicitudes)
  tabActiva: 'nueva' | 'creadas' = 'nueva';

  /** Valor numérico que representa el Llamado de Atención (rank usado por el Tribunal). */
  static readonly PUNTOS_LLAMADO_ATENCION = -0.25;
  /** Valor numérico que representa la Felicitación (rank usado por el Tribunal). */
  static readonly PUNTOS_FELICITACION = 0.25;

  /** Escala de puntaje (misma que gestionar-expedientes, sin el 0.0 de eximición). */
  readonly escalaPuntos: number[] = [-3, -2.5, -2, -1.5, -1, -0.5, -0.25, 0.25, 0.5, 1, 1.5, 2, 2.5, 3];

  /** El tipo de acción se deriva del signo de los puntos solicitados. */
  get tipoAccion(): TipoAccionT01 {
    return (this.puntosSeleccionados ?? -1) < 0 ? 'SANCTION' : 'MERIT';
  }

  get puntosTexto(): string {
    const valor = this.puntosSeleccionados ?? -1;
    if (valor === SolicitarPuntosComponent.PUNTOS_LLAMADO_ATENCION) return 'Llamado de Atención';
    if (valor === SolicitarPuntosComponent.PUNTOS_FELICITACION) return 'Felicitación';
    return `${valor > 0 ? '+' : ''}${valor.toFixed(1)} pts`;
  }

  private get indicePuntos(): number {
    return this.escalaPuntos.indexOf(this.normalizarPuntos(this.puntosSeleccionados));
  }

  /** Etiqueta del tipo de acción según el valor elegido. */
  get tipoAccionTexto(): string {
    const valor = this.puntosSeleccionados ?? -1;
    if (valor === SolicitarPuntosComponent.PUNTOS_LLAMADO_ATENCION) return 'Apercibimiento';
    if (valor === SolicitarPuntosComponent.PUNTOS_FELICITACION) return 'Reconocimiento';
    return this.tipoAccion === 'SANCTION' ? 'Sanción' : 'Premio';
  }

  get puedeDecrementarPuntos(): boolean {
    return this.estado !== 'ISSUED' && !this.cargando && this.indicePuntos > 0;
  }

  get puedeIncrementarPuntos(): boolean {
    return this.estado !== 'ISSUED' && !this.cargando && this.indicePuntos < this.escalaPuntos.length - 1;
  }

  decrementarPuntos(): void {
    if (!this.puedeDecrementarPuntos) return;
    this.puntosSeleccionados = this.escalaPuntos[this.indicePuntos - 1];
  }

  incrementarPuntos(): void {
    if (!this.puedeIncrementarPuntos) return;
    this.puntosSeleccionados = this.escalaPuntos[this.indicePuntos + 1];
  }

  /** Ajusta cualquier valor (p. ej. de un borrador previo) al paso de escala más cercano. */
  private normalizarPuntos(valor: number | null | undefined): number {
    const numero = Number(valor);
    if (valor === null || valor === undefined || isNaN(numero) || numero === 0) {
      return -1;
    }
    return this.escalaPuntos.reduce((mejor, paso) =>
      Math.abs(paso - numero) < Math.abs(mejor - numero) ? paso : mejor
    );
  }

  constructor(
    private padronApi: PadronApiService,
    private expedienteApi: ExpedienteApiService,
    public dialog: MatDialog,
    private notifications: NotificationService,
    private renderer: Renderer2,
    private scrollLock: ModalScrollLockService
  ) {}

  ngOnInit(): void {
    this.padronApi.listarSocios().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: socios => {
        this.socios = socios;
      },
      error: error => this.mostrarError(error)
    });
    this.socioBusqueda.valueChanges.pipe(
      takeUntil(this.destroy$)
    ).subscribe(value => this.filtrarSocios(value || ''));
    this.expedienteApi.listarReglamentos().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: response => {
        this.reglamentosDisponibles = response.reglamentos || [];
        this.articulosDisponibles = (response as any).articulos || [];
        this.actualizarCatalogoItemsModal();
      },
      error: error => this.mostrarError(error)
    });

    this.cargarMisSolicitudes();

    this.busquedaControl.valueChanges.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntil(this.destroy$)
    ).subscribe(() => this.cargarMisSolicitudes());

    this.estadoFiltro.valueChanges.pipe(
      takeUntil(this.destroy$)
    ).subscribe(() => this.cargarMisSolicitudes());
  }

  ngOnDestroy(): void {
    this.scrollLock.reset();
    this.destroy$.next();
    this.destroy$.complete();
  }

  cargarMisSolicitudes(): void {
    this.cargandoSolicitudes = true;
    this.failedToLoadRequests = false;
    const search = this.busquedaControl.value?.trim() || undefined;
    const estado = this.estadoFiltro.value || undefined;
    this.expedienteApi.listarMisSolicitudes({ search, estado }).pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: solicitudes => {
        this.misSolicitudes = solicitudes;
        this.cargandoSolicitudes = false;
      },
      error: () => {
        this.failedToLoadRequests = true;
        this.notifications.error('No se pudieron cargar las solicitudes iniciadas.');
        this.cargandoSolicitudes = false;
      }
    });
  }

  filtrarSocios(termino: string): void {
    const texto = termino.trim().toLowerCase();
    if (texto.length < 3) {
      this.sociosFiltrados = [];
      return;
    }
    const idsYaSeleccionados = new Set(this.sociosSeleccionados.map(s => s.socio_id));
    this.sociosFiltrados = this.socios.filter(socio =>
      !idsYaSeleccionados.has(socio.socio_id) &&
      [socio.legajo, socio.first_name, socio.last_name]
        .some(valor => valor && valor.toLowerCase().includes(texto))
    );
  }

  seleccionarSocio(socio: PadronSocio): void {
    this.agregarSocio(socio);
  }

  agregarSocio(socio: PadronSocio): void {
    if (this.estado === 'ISSUED') {
      return;
    }
    const yaExiste = this.sociosSeleccionados.some(s => s.socio_id === socio.socio_id);
    if (!yaExiste) {
      this.sociosSeleccionados.push(socio);
    }
    this.socioBusqueda.setValue('', { emitEvent: false });
    this.sociosFiltrados = [];
  }

  eliminarSocio(socioId: number): void {
    if (this.estado === 'ISSUED') {
      return;
    }
    this.sociosSeleccionados = this.sociosSeleccionados.filter(s => s.socio_id !== socioId);
  }

  nombreSocio(socio: PadronSocio): string {
    return `${socio.last_name}, ${socio.first_name}`;
  }

  guardarBorrador(): void {
    if (this.estado === 'ISSUED') return;
    this.cargando = true;
    const request = this.borradorId ? this.expedienteApi.actualizarBorrador(this.borradorId, this.payload()) : this.expedienteApi.crearBorrador(this.payload());
    request.subscribe({
      next: solicitud => {
        this.aplicarSolicitud(solicitud);
        this.notifications.success('Borrador guardado.');
        this.cargando = false;
        this.cargarMisSolicitudes();
      },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  emitirT01(): void {
    if (!this.validarEmision() || this.estado === 'ISSUED') return;
    this.cargando = true;
    const guardar = this.borradorId ? this.expedienteApi.actualizarBorrador(this.borradorId, this.payload()) : this.expedienteApi.crearBorrador(this.payload());
    guardar.subscribe({
      next: solicitud => this.emitirPersistido(solicitud),
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  private emitirPersistido(solicitud: SolicitudT01): void {
    this.aplicarSolicitud(solicitud);
    this.expedienteApi.emitir(solicitud.id).subscribe({
      next: emitida => {
        this.aplicarSolicitud(emitida);
        this.notifications.success(`Expediente creado: ${emitida.numero_expediente}.`);
        this.cargando = false;
        this.cargarMisSolicitudes();
      },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  setTab(tab: 'nueva' | 'creadas'): void {
    this.tabActiva = tab;
  }

  continuarEdicion(solicitud: SolicitudMonitoreo): void {
    if (solicitud.estado === 'ISSUED') return;

    this.tabActiva = 'nueva';
    this.borradorId = solicitud.id;
    this.estado = solicitud.estado;
    this.numeroExpediente = solicitud.numero_expediente;
    this.titulo = solicitud.titulo ?? '';
    this.causal = solicitud.causal ?? '';
    this.urgency = solicitud.urgencia ?? 'normal';
    if (solicitud.puntaje_especial === 'LLAMADO_ATENCION' || solicitud.puntos === -0.25) {
      this.puntosSeleccionados = SolicitarPuntosComponent.PUNTOS_LLAMADO_ATENCION;
    } else if (solicitud.puntaje_especial === 'FELICITACION' || solicitud.puntos === 0.25) {
      this.puntosSeleccionados = SolicitarPuntosComponent.PUNTOS_FELICITACION;
    } else {
      this.puntosSeleccionados = this.normalizarPuntos(solicitud.puntos);
    }
    this.razon = solicitud.razon || solicitud.motivo || '';
    this.reglamentosSeleccionados = solicitud.reglamentos_respaldantes ? [...solicitud.reglamentos_respaldantes] : [];
    this.reglamentoExpandidoForm = null;
    this.anexoFecha = solicitud.anexo_fecha ?? '';
    this.anexoLugar = solicitud.anexo_lugar ?? '';
    this.anexoTestigos = solicitud.anexo_testigos ?? '';
    this.anexoRelato = solicitud.anexo_relato ?? '';
    this.anexoExpandido = !!(this.anexoFecha || this.anexoLugar || this.anexoTestigos || this.anexoRelato);

    const ids = (solicitud.destinatarios_socios_ids && solicitud.destinatarios_socios_ids.length > 0)
      ? solicitud.destinatarios_socios_ids
      : (solicitud.involucrados ? solicitud.involucrados.map(i => i.socio_id!).filter(Boolean) : []);

    if (ids.length > 0 && this.socios.length > 0) {
      this.sociosSeleccionados = this.socios.filter(s => ids.includes(s.socio_id));
    } else if (solicitud.involucrados && solicitud.involucrados.length > 0) {
      this.sociosSeleccionados = solicitud.involucrados.map(inv => ({
        socio_id: inv.socio_id || 0,
        legajo: inv.legajo || '',
        first_name: inv.first_name || '',
        last_name: inv.last_name || '',
        grupo: inv.grupo || null,
        subcomision: inv.subcomision ? { id: 0, name: inv.subcomision } : null,
        is_active: true
      }));
    } else {
      this.sociosSeleccionados = [];
    }

    if (solicitud.expedientes_referenciados_detalle && solicitud.expedientes_referenciados_detalle.length > 0) {
      this.expedientesReferenciadosSeleccionados = [...solicitud.expedientes_referenciados_detalle];
    } else {
      this.expedientesReferenciadosSeleccionados = [];
    }

    this.sincronizarEstadoSocio();
    this.notifications.info(`Borrador "${solicitud.titulo || solicitud.numero}" cargado en el formulario.`);

    if (typeof window !== 'undefined' && window.scrollTo) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  eliminarBorrador(solicitud: SolicitudMonitoreo): void {
    if (solicitud.estado === 'ISSUED') return;
    const confirmacion = window.confirm(`¿Estás seguro de que deseás eliminar el borrador "${solicitud.titulo || solicitud.numero}"?`);
    if (!confirmacion) return;

    this.expedienteApi.eliminarBorrador(solicitud.id).subscribe({
      next: () => {
        this.notifications.success('Borrador eliminado correctamente.');
        if (this.borradorId === solicitud.id) {
          this.resetearFormulario();
        }
        this.cargarMisSolicitudes();
      },
      error: error => this.mostrarError(error)
    });
  }

  get reglamentosFiltrados(): string[] {
    const busqueda = (this.filtroReglamentos || '').trim().toLowerCase();
    if (!busqueda) {
      return this.reglamentosDisponibles;
    }
    return this.reglamentosDisponibles.filter(reg =>
      reg.toLowerCase().includes(busqueda) || this.reglamentosSeleccionados.includes(reg)
    );
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

  get articulosModalFiltrados(): CatalogoReglamentoItem[] {
    const busqueda = (this.filtroReglamentos || '').trim().toLowerCase();
    return this.catalogoItemsModal.filter(item => {
      if (this.filtroDocumentoModal !== 'TODOS' && item.documento !== this.filtroDocumentoModal) {
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

  get reglamentosSeleccionadosCitas(): ReglamentoCiteView[] {
    return parseReglamentosList(this.reglamentosSeleccionados, null, this.articulosDisponibles);
  }

  get reglamentoExpandidoFormDetalle(): ReglamentoCiteView | null {
    if (!this.reglamentoExpandidoForm || !this.reglamentosSeleccionados.includes(this.reglamentoExpandidoForm)) {
      return null;
    }
    return parseReglamentoCite(this.reglamentoExpandidoForm, this.articulosDisponibles);
  }

  abrirModalReglamentos(): void {
    if (this.estado === 'ISSUED') return;
    this.elementoFocoPrevio = (typeof document !== 'undefined' ? document.activeElement as HTMLElement : null);
    this.modalReglamentosAbierto = true;
    this.scrollLock.lock();
    setTimeout(() => {
      if (this.modalReglamentosBody?.nativeElement) {
        this.modalReglamentosBody.nativeElement.scrollTop = 0;
      }
      this.modalReglamentosDialog?.nativeElement?.focus({ preventScroll: true });
      if (this.modalSearchInput?.nativeElement) {
        this.modalSearchInput.nativeElement.focus({ preventScroll: true });
      }
    }, 0);
  }

  cerrarModalReglamentos(): void {
    this.modalReglamentosAbierto = false;
    this.scrollLock.unlock();
    if (this.elementoFocoPrevio && typeof this.elementoFocoPrevio.focus === 'function') {
      this.elementoFocoPrevio.focus({ preventScroll: true });
    }
    this.elementoFocoPrevio = null;
  }

  onModalReglamentosKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.cerrarModalReglamentos();
      return;
    }

    if (['ArrowDown', 'ArrowUp', 'PageDown', 'PageUp'].includes(event.key)) {
      const delta = (event.key === 'ArrowDown' ? 40 : event.key === 'ArrowUp' ? -40 : event.key === 'PageDown' ? 200 : -200);
      if (this.modalReglamentosBody?.nativeElement) {
        this.modalReglamentosBody.nativeElement.scrollTop += delta;
      }
      event.preventDefault();
      event.stopPropagation();
    }
  }

  setFiltroDocumentoModal(doc: 'TODOS' | 'Reglamento Interno' | 'Estatuto'): void {
    this.filtroDocumentoModal = doc;
  }

  esReglamentoSeleccionado(raw: string): boolean {
    return this.reglamentosSeleccionados.includes(raw);
  }

  contarSeleccionadosPorDocumento(doc: 'Estatuto' | 'Reglamento Interno'): number {
    return this.reglamentosSeleccionadosCitas.filter(c => c.documento === doc).length;
  }

  toggleExpandirReglamentoForm(raw: string): void {
    this.reglamentoExpandidoForm = this.reglamentoExpandidoForm === raw ? null : raw;
  }

  formatReglamentosCitas(regs: string[] | undefined): ReglamentoCiteView[] {
    return parseReglamentosList(regs, null, this.articulosDisponibles);
  }

  toggleReglamento(reglamento: string): void {
    if (this.estado === 'ISSUED') return;
    const idx = this.reglamentosSeleccionados.indexOf(reglamento);
    if (idx >= 0) {
      this.reglamentosSeleccionados.splice(idx, 1);
      if (this.reglamentoExpandidoForm === reglamento) {
        this.reglamentoExpandidoForm = null;
      }
    } else {
      this.reglamentosSeleccionados.push(reglamento);
    }
  }

  removerReglamento(reglamento: string): void {
    if (this.estado === 'ISSUED') return;
    this.reglamentosSeleccionados = this.reglamentosSeleccionados.filter(r => r !== reglamento);
    if (this.reglamentoExpandidoForm === reglamento) {
      this.reglamentoExpandidoForm = null;
    }
  }

  limpiarReglamentos(): void {
    if (this.estado === 'ISSUED') return;
    this.reglamentosSeleccionados = [];
    this.reglamentoExpandidoForm = null;
  }

  abrirModalExpedientes(): void {
    if (this.estado === 'ISSUED') return;
    this.modalExpedientesAbierto = true;
    if (!this.catalogoExpedientesCargado) {
      this.cargarCatalogoExpedientes();
    }
  }

  cerrarModalExpedientes(): void {
    this.modalExpedientesAbierto = false;
  }

  onExpedientesSeleccionadosChange(seleccionados: AntecedenteT03DTO[]): void {
    this.expedientesReferenciadosSeleccionados = [...seleccionados];
  }

  removerExpedienteReferenciado(id: number): void {
    if (this.estado === 'ISSUED') return;
    this.expedientesReferenciadosSeleccionados = this.expedientesReferenciadosSeleccionados.filter(e => e.id !== id);
  }

  limpiarExpedientesReferenciados(): void {
    if (this.estado === 'ISSUED') return;
    this.expedientesReferenciadosSeleccionados = [];
  }

  cargarCatalogoExpedientes(): void {
    this.cargandoCatalogoExpedientes = true;
    this.expedienteApi.listarCatalogoAntecedentes().pipe(
      takeUntil(this.destroy$)
    ).subscribe({
      next: catalogo => {
        this.catalogoExpedientesModal = catalogo;
        this.cargandoCatalogoExpedientes = false;
        this.catalogoExpedientesCargado = true;
      },
      error: error => {
        this.cargandoCatalogoExpedientes = false;
        this.mostrarError(error);
      }
    });
  }

  resetearFormulario(): void {
    this.scrollLock.reset();
    this.borradorId = null;
    this.estado = null;
    this.numeroExpediente = null;
    this.titulo = '';
    this.causal = '';
    this.urgency = 'normal';
    this.puntosSeleccionados = -1;
    this.razon = '';
    this.filtroReglamentos = '';
    this.reglamentosSeleccionados = [];
    this.reglamentoExpandidoForm = null;
    this.modalReglamentosAbierto = false;
    this.filtroDocumentoModal = 'TODOS';
    this.expedientesReferenciadosSeleccionados = [];
    this.modalExpedientesAbierto = false;
    this.anexoFecha = '';
    this.anexoLugar = '';
    this.anexoTestigos = '';
    this.anexoRelato = '';
    this.anexoExpandido = false;
    this.sociosSeleccionados = [];
    this.sincronizarEstadoSocio();
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

  get misSolicitudesOrdenadas(): SolicitudMonitoreo[] {
    if (!this.misSolicitudes || this.misSolicitudes.length === 0) {
      return [];
    }
    const result = [...this.misSolicitudes];
    result.sort((a, b) => {
      let valA: any;
      let valB: any;
      switch (this.columnaOrden) {
        case 'numero':
          valA = this.formatSolicitudExpediente(a);
          valB = this.formatSolicitudExpediente(b);
          break;
        case 'titulo':
          valA = a.titulo || a.motivo || '';
          valB = b.titulo || b.motivo || '';
          break;
        case 'involucrados':
        case 'cantidadSocios':
          valA = a.involucrados?.length || 0;
          valB = b.involucrados?.length || 0;
          return this.ordenAscendente ? valA - valB : valB - valA;
        case 'fecha':
        case 'fechaCreacion':
          valA = new Date(a.fecha || a.created_at || 0).getTime();
          valB = new Date(b.fecha || b.created_at || 0).getTime();
          return this.ordenAscendente ? valA - valB : valB - valA;
        case 'puntos':
          valA = a.puntos ?? 0;
          valB = b.puntos ?? 0;
          return this.ordenAscendente ? valA - valB : valB - valA;
        case 'urgencia': {
          const pesos: Record<string, number> = { urgente: 3, normal: 2, baja: 1 };
          valA = pesos[a.urgencia || 'normal'] || 0;
          valB = pesos[b.urgencia || 'normal'] || 0;
          return this.ordenAscendente ? valA - valB : valB - valA;
        }
        case 'estado':
          valA = this.obtenerTextoEstado(a);
          valB = this.obtenerTextoEstado(b);
          break;
        default:
          valA = (a as any)[this.columnaOrden] ?? '';
          valB = (b as any)[this.columnaOrden] ?? '';
          break;
      }
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return this.ordenAscendente ? -1 : 1;
      if (valA > valB) return this.ordenAscendente ? 1 : -1;
      return 0;
    });
    return result;
  }

  onTableKeyDown(event: KeyboardEvent, solicitud: SolicitudMonitoreo): void {
    if (!event) return;
    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
      event.preventDefault();
      this.abrirDetalle(solicitud);
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

  abrirDetalle(solicitud: SolicitudMonitoreo): void {
    this.solicitudSeleccionada = solicitud;
    this.modalDetalleAbierto = true;
    this.scrollLock.lock();
    setTimeout(() => {
      const modalBody = (document.querySelector('.modal-detalle-body') || document.querySelector('.modal-dialog-custom')) as HTMLElement;
      if (modalBody) {
        modalBody.focus({ preventScroll: true });
      }
    }, 50);
  }

  cerrarModalDetalle(): void {
    this.modalDetalleAbierto = false;
    this.solicitudSeleccionada = null;
    this.scrollLock.unlock();
  }

  obtenerClaseBadge(solicitud: SolicitudMonitoreo): string {
    if (solicitud.estado === 'DRAFT') {
      return 'badge-mat-rose';
    }
    switch (solicitud.estado_procesal) {
      case 'creado':
        return 'badge-mat-info';
      case 'justificando':
      case 'en_descargo':
        return 'badge-mat-warning';
      case 'revision_resolucion':
      case 'espera_resolucion':
      case 'evaluacion':
        return 'badge-mat-primary';
      case 'pendiente_correos':
        return 'badge-mat-rose';
      case 'emitido':
      case 'resuelto':
        return 'badge-mat-success';
      case 'rechazado':
      case 'desestimado':
        return 'badge-mat-danger';
      default:
        return 'badge-mat-info';
    }
  }

  obtenerTextoEstado(solicitud: SolicitudMonitoreo): string {
    if (solicitud.estado === 'DRAFT') {
      return 'Borrador';
    }
    return solicitud.estado_procesal_display || 'En Trámite';
  }

  obtenerClaseUrgencia(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente':
        return 'badge-mat-danger';
      case 'baja':
        return 'badge-mat-success';
      case 'normal':
      default:
        return 'badge-mat-info';
    }
  }

  obtenerIconoUrgencia(urgencia?: string): string {
    switch (urgencia) {
      case 'urgente':
        return 'priority_high';
      case 'baja':
        return 'arrow_downward';
      case 'normal':
      default:
        return 'horizontal_rule';
    }
  }

  obtenerTextoInvolucrados(solicitud: SolicitudMonitoreo): string {
    if (!solicitud.involucrados || solicitud.involucrados.length === 0) {
      return 'Sin socios asignados';
    }
    if (solicitud.involucrados.length === 1) {
      const inv = solicitud.involucrados[0];
      return `${inv.last_name}, ${inv.first_name}`;
    }
    const primero = solicitud.involucrados[0];
    return `${primero.last_name}, ${primero.first_name} (+${solicitud.involucrados.length - 1})`;
  }

  private payload(): SolicitudT01Payload {
    const ids = this.sociosSeleccionados.map(s => s.socio_id);
    let puntajeEspecial: 'LLAMADO_ATENCION' | 'FELICITACION' | '' = '';
    if (this.puntosSeleccionados === SolicitarPuntosComponent.PUNTOS_LLAMADO_ATENCION) {
      puntajeEspecial = 'LLAMADO_ATENCION';
    } else if (this.puntosSeleccionados === SolicitarPuntosComponent.PUNTOS_FELICITACION) {
      puntajeEspecial = 'FELICITACION';
    }
    return {
      destinatario_socio_id: ids.length > 0 ? ids[0] : null,
      destinatarios_socios_ids: ids,
      tipo_accion: this.tipoAccion,
      puntaje_especial: puntajeEspecial,
      urgencia: this.urgency,
      titulo: this.titulo,
      causal: this.causal,
      puntos: this.puntosSeleccionados,
      motivo: this.razon,
      razon: this.razon,
      reglamentos_respaldantes: this.reglamentosSeleccionados,
      expedientes_referenciados: this.expedientesReferenciadosSeleccionados.map(e => e.id),
      anexo_fecha: this.anexoFecha || null,
      anexo_lugar: this.anexoLugar,
      anexo_relato: this.anexoRelato,
      anexo_testigos: this.anexoTestigos
    };
  }

  private validarEmision(): boolean {
    if (!this.titulo.trim()) {
      this.notifications.error('Indica el título de la solicitud.');
      return false;
    }
    if (this.sociosSeleccionados.length === 0) {
      this.notifications.error('Selecciona al menos un socio involucrado.');
      return false;
    }
    if (!this.razon.trim()) {
      this.notifications.error('Describe la razón de la solicitud.');
      return false;
    }
    if (this.puntosSeleccionados === null || this.puntosSeleccionados === undefined) {
      this.notifications.error('Indica los puntos antes de emitir.');
      return false;
    }
    if (!this.reglamentosSeleccionados || this.reglamentosSeleccionados.length === 0) {
      this.notifications.error('Seleccioná al menos un artículo del reglamento respaldante.');
      return false;
    }
    return true;
  }

  private aplicarSolicitud(solicitud: SolicitudT01): void {
    this.borradorId = solicitud.id;
    this.estado = solicitud.estado;
    this.numeroExpediente = solicitud.numero_expediente;
    this.titulo = solicitud.titulo ?? this.titulo;
    this.causal = solicitud.causal ?? this.causal;
    this.urgency = solicitud.urgencia ?? 'normal';
    if (solicitud.puntaje_especial === 'LLAMADO_ATENCION' || solicitud.puntos === -0.25) {
      this.puntosSeleccionados = SolicitarPuntosComponent.PUNTOS_LLAMADO_ATENCION;
    } else if (solicitud.puntaje_especial === 'FELICITACION' || solicitud.puntos === 0.25) {
      this.puntosSeleccionados = SolicitarPuntosComponent.PUNTOS_FELICITACION;
    } else {
      this.puntosSeleccionados = solicitud.puntos == null ? this.puntosSeleccionados : this.normalizarPuntos(Number(solicitud.puntos));
    }
    this.razon = solicitud.razon || solicitud.motivo || this.razon;
    if (solicitud.reglamentos_respaldantes && solicitud.reglamentos_respaldantes.length > 0) {
      this.reglamentosSeleccionados = solicitud.reglamentos_respaldantes;
    }
    if (solicitud.expedientes_referenciados_detalle && solicitud.expedientes_referenciados_detalle.length > 0) {
      this.expedientesReferenciadosSeleccionados = [...solicitud.expedientes_referenciados_detalle];
    }
    this.anexoFecha = solicitud.anexo_fecha ?? this.anexoFecha;
    this.anexoLugar = solicitud.anexo_lugar ?? this.anexoLugar;
    this.anexoTestigos = solicitud.anexo_testigos ?? this.anexoTestigos;
    this.anexoRelato = solicitud.anexo_relato ?? this.anexoRelato;

    const ids = (solicitud.destinatarios_socios_ids && solicitud.destinatarios_socios_ids.length > 0)
      ? solicitud.destinatarios_socios_ids
      : (solicitud.destinatario_socio_id ? [solicitud.destinatario_socio_id] : []);

    if (ids.length > 0 && this.socios.length > 0) {
      this.sociosSeleccionados = this.socios.filter(s => ids.includes(s.socio_id));
    }
    this.sincronizarEstadoSocio();
  }

  sincronizarEstadoSocio(): void {
    if (this.estado === 'ISSUED') {
      this.socioBusqueda.disable({ emitEvent: false });
    } else {
      this.socioBusqueda.enable({ emitEvent: false });
    }
  }

  private mostrarError(error: { status?: number; error?: unknown }): void {
    const fallback = error?.status === 0 || error?.status >= 500
      ? 'El servicio no está disponible en este momento. Intentá nuevamente más tarde.'
      : 'No se pudo completar la operación.';
    this.notifications.error(httpErrorMessage(error, fallback));
  }

  formatCaseNumber(numero: string | null | undefined): string {
    return formatCaseNumber(numero);
  }

  formatSolicitudExpediente(s: SolicitudMonitoreo | SolicitudT01 | null | undefined): string {
    if (!s || s.estado === 'DRAFT') {
      return 'Borrador sin número';
    }
    const raw = s.numero_expediente && !s.numero_expediente.startsWith('T01-')
      ? s.numero_expediente
      : ('numero' in s && s.numero ? s.numero : '');
    if (!raw || raw === 'Borrador sin número') {
      return 'Borrador sin número';
    }
    return this.formatCaseNumber(raw);
  }
}
