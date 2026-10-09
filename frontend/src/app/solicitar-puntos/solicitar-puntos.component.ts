import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';

import {
  ExpedienteApiService,
  SolicitudMonitoreo,
  SolicitudT01,
  SolicitudT01Payload,
  TipoAccionT01
} from '../services/expediente-api.service';
import { PadronApiService, PadronSocio } from '../services/padron-api.service';
import { SolicitudDetalleDialogComponent } from './solicitud-detalle-dialog/solicitud-detalle-dialog.component';

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
  tipoAccion: TipoAccionT01 = 'SANCTION';
  puntosSeleccionados: number | null = -1;
  causal = '';
  motivoTexto = '';
  titulo = '';
  razon = '';
  reglamentosDisponibles: string[] = [];
  reglamentosSeleccionados: string[] = [];
  anexoFecha = '';
  anexoLugar = '';
  anexoTestigos = '';
  anexoRelato = '';
  anexoExpandido = false;
  borradorId: string | null = null;
  estado: 'DRAFT' | 'ISSUED' | null = null;
  numeroExpediente: string | null = null;
  cargando = false;
  errorMensaje = '';
  exitoMensaje = '';

  // Panel Mis Solicitudes T01 (SCRUM-75 / PB-04)
  misSolicitudes: SolicitudMonitoreo[] = [];
  cargandoSolicitudes = false;
  errorSolicitudes = '';
  busquedaControl = new FormControl('');
  estadoFiltro = new FormControl('');
  private destroy$ = new Subject<void>();

  escalasSancion = [
    { valor: -0.5, desc: '-0.5 pts: Falta Leve' },
    { valor: -1, desc: '-1.0 pts: Falta Media' },
    { valor: -1.5, desc: '-1.5 pts: Falta Grave' },
    { valor: -2, desc: '-2.0 pts: Falta Muy Grave' }
  ];
  escalasMerito = [
    { valor: 0.5, desc: '+0.5 pts: Reconocimiento Leve' },
    { valor: 1, desc: '+1.0 pts: Reconocimiento Estándar' },
    { valor: 2, desc: '+2.0 pts: Reconocimiento Destacado' },
    { valor: 3, desc: '+3.0 pts: Máximo Reconocimiento' }
  ];

  constructor(
    private padronApi: PadronApiService,
    private expedienteApi: ExpedienteApiService,
    public dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.padronApi.listarSocios().subscribe({
      next: socios => {
        this.socios = socios;
      },
      error: error => this.mostrarError(error)
    });
    this.socioBusqueda.valueChanges.subscribe(value => this.filtrarSocios(value || ''));
    this.expedienteApi.listarReglamentos().subscribe({
      next: response => this.reglamentosDisponibles = response.reglamentos,
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
    this.destroy$.next();
    this.destroy$.complete();
  }

  cargarMisSolicitudes(): void {
    this.cargandoSolicitudes = true;
    this.errorSolicitudes = '';
    const search = this.busquedaControl.value?.trim() || undefined;
    const estado = this.estadoFiltro.value || undefined;
    this.expedienteApi.listarMisSolicitudes({ search, estado }).subscribe({
      next: solicitudes => {
        this.misSolicitudes = solicitudes;
        this.cargandoSolicitudes = false;
      },
      error: () => {
        this.errorSolicitudes = 'No se pudieron cargar las solicitudes iniciadas.';
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

  onTipoAccionChange(tipo: TipoAccionT01): void {
    this.tipoAccion = tipo;
    this.puntosSeleccionados = tipo === 'SANCTION' ? -1 : 1;
  }

  guardarBorrador(): void {
    this.errorMensaje = '';
    this.exitoMensaje = '';
    if (this.estado === 'ISSUED') return;
    this.cargando = true;
    const request = this.borradorId ? this.expedienteApi.actualizarBorrador(this.borradorId, this.payload()) : this.expedienteApi.crearBorrador(this.payload());
    request.subscribe({
      next: solicitud => {
        this.aplicarSolicitud(solicitud);
        this.exitoMensaje = 'Borrador guardado.';
        this.cargando = false;
        this.cargarMisSolicitudes();
      },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  emitirT01(): void {
    this.errorMensaje = '';
    this.exitoMensaje = '';
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
        this.exitoMensaje = `Expediente creado: ${emitida.numero_expediente}.`;
        this.cargando = false;
        this.cargarMisSolicitudes();
      },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  continuarEdicion(solicitud: SolicitudMonitoreo): void {
    if (solicitud.estado === 'ISSUED') return;

    this.borradorId = solicitud.id;
    this.estado = solicitud.estado;
    this.numeroExpediente = solicitud.numero_expediente;
    this.titulo = solicitud.titulo ?? '';
    this.causal = solicitud.causal ?? '';
    this.tipoAccion = solicitud.tipo_accion ?? 'SANCTION';
    this.puntosSeleccionados = solicitud.puntos ?? (this.tipoAccion === 'SANCTION' ? -1 : 1);
    this.razon = solicitud.razon || solicitud.motivo || '';
    this.reglamentosSeleccionados = solicitud.reglamentos_respaldantes ? [...solicitud.reglamentos_respaldantes] : [];
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
        subcomision: inv.subcomision ? { id: 0, name: inv.subcomision } : null,
        is_active: true
      }));
    } else {
      this.sociosSeleccionados = [];
    }

    this.sincronizarEstadoSocio();
    this.exitoMensaje = `Borrador "${solicitud.titulo || solicitud.numero}" cargado en el formulario.`;
    this.errorMensaje = '';

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
        this.exitoMensaje = 'Borrador eliminado correctamente.';
        this.errorMensaje = '';
        if (this.borradorId === solicitud.id) {
          this.resetearFormulario();
        }
        this.cargarMisSolicitudes();
      },
      error: error => this.mostrarError(error)
    });
  }

  resetearFormulario(): void {
    this.borradorId = null;
    this.estado = null;
    this.numeroExpediente = null;
    this.titulo = '';
    this.causal = '';
    this.tipoAccion = 'SANCTION';
    this.puntosSeleccionados = -1;
    this.razon = '';
    this.reglamentosSeleccionados = [];
    this.anexoFecha = '';
    this.anexoLugar = '';
    this.anexoTestigos = '';
    this.anexoRelato = '';
    this.anexoExpandido = false;
    this.sociosSeleccionados = [];
    this.sincronizarEstadoSocio();
  }

  abrirDetalle(solicitud: SolicitudMonitoreo): void {
    this.dialog.open(SolicitudDetalleDialogComponent, {
      width: '100%',
      maxWidth: '750px',
      data: solicitud
    });
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
    return {
      destinatario_socio_id: ids.length > 0 ? ids[0] : null,
      destinatarios_socios_ids: ids,
      tipo_accion: this.tipoAccion,
      titulo: this.titulo,
      causal: this.causal,
      puntos: this.puntosSeleccionados,
      motivo: this.razon,
      razon: this.razon,
      reglamentos_respaldantes: this.reglamentosSeleccionados,
      anexo_fecha: this.anexoFecha || null,
      anexo_lugar: this.anexoLugar,
      anexo_relato: this.anexoRelato,
      anexo_testigos: this.anexoTestigos
    };
  }

  private validarEmision(): boolean {
    if (!this.titulo.trim()) {
      this.errorMensaje = 'Indica el título de la solicitud.';
      return false;
    }
    if (this.sociosSeleccionados.length === 0) {
      this.errorMensaje = 'Selecciona al menos un socio involucrado.';
      return false;
    }
    if (!this.razon.trim()) {
      this.errorMensaje = 'Describe la razón de la solicitud.';
      return false;
    }
    if (this.puntosSeleccionados === null || this.puntosSeleccionados === undefined) {
      this.errorMensaje = 'Indica los puntos antes de emitir.';
      return false;
    }
    if ((this.tipoAccion === 'SANCTION' && this.puntosSeleccionados >= 0) || (this.tipoAccion === 'MERIT' && this.puntosSeleccionados <= 0)) {
      this.errorMensaje = 'Los puntos no son coherentes con el tipo de acción.';
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
    this.tipoAccion = solicitud.tipo_accion ?? this.tipoAccion;
    this.puntosSeleccionados = solicitud.puntos ?? this.puntosSeleccionados;
    this.razon = solicitud.razon || solicitud.motivo || this.razon;
    this.reglamentosSeleccionados = solicitud.reglamentos_respaldantes ?? this.reglamentosSeleccionados;
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
    if (error && typeof error.status === 'number' && error.status >= 500) {
      this.errorMensaje = 'El servicio no está disponible en este momento. Intentá nuevamente más tarde.';
      return;
    }

    const body = error && error.error;
    if (typeof body === 'string') {
      this.errorMensaje = 'No se pudo completar la operación.';
      return;
    }
    if (body && typeof body === 'object') {
      const detail = (body as { detail?: unknown }).detail;
      if (typeof detail === 'string' && detail.trim()) {
        this.errorMensaje = detail;
        return;
      }
      const messages = Object.values(body).flat().filter(value => typeof value === 'string');
      if (messages.length > 0) {
        this.errorMensaje = messages.join(' ');
        return;
      }
    }
    this.errorMensaje = 'No se pudo completar la operación.';
  }
}
