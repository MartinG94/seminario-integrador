import { Component, OnInit, OnDestroy, Renderer2 } from '@angular/core';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { ExpedienteApiService, EvidenciaMetadata } from '../services/expediente-api.service';
import { Subscription, interval } from 'rxjs';

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

  // Ordenamiento de tabla
  columnaOrden = 'numero';
  ordenAscendente = true;

  // Modal T02/T03
  modalAbierto = false;
  expedienteSeleccionado: Expediente | null = null;
  tipoDescargo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO' = 'T02_CERTIFICADO';
  causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
  nombreArchivo = '';
  archivosSeleccionados: File[] = [];
  evidenciasExistentes: any[] = [];
  subiendoArchivos = false;
  readonly LIMITE_T02 = 3;
  readonly LIMITE_T03 = 5;
  readonly MAX_BYTES = 5 * 1024 * 1024; // 5 MB
  relatoTexto = '';
  esEdicion = false;

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
    private expedienteApi: ExpedienteApiService
  ) {}

  ngOnInit(): void {
    const subPerfil = this.auth.perfil$.subscribe(perfil => {
      this.socioActual = perfil ? `${perfil.first_name} ${perfil.last_name}` : '';
      this.filtrarMisExpedientes();
    });
    this.subs.push(subPerfil);

    const subExp = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
      this.filtrarMisExpedientes();
      if (this.expedienteDetalle) {
        const actualizado = list.find(e => e.id === this.expedienteDetalle!.id);
        if (actualizado) {
          this.expedienteDetalle = actualizado;
        }
      }
    });
    this.subs.push(subExp);

    const subSocios = this.dataService.socios$.subscribe(socios => {
      const s = socios.find(soc => soc.nombre.toLowerCase() === this.socioActual.toLowerCase());
      this.saldoNeto = s ? s.saldo : 0;
    });
    this.subs.push(subSocios);

    // Actualizador dinámico del reloj cada segundo (evita memory leaks desuscribiéndose en ngOnDestroy)
    this.tickerSub = interval(1000).subscribe(() => {
      this.ahoraMs = Date.now();
    });
  }

  /** Los expedientes del socio en sesión; hoy provienen de datos simulados. */
  private filtrarMisExpedientes(): void {
    const nombre = this.socioActual.trim().toLowerCase();
    this.misExpedientes = nombre
      ? this.expedientes.filter(e => e.socio.toLowerCase() === nombre)
      : [];
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

  abrirModalDetalle(exp: Expediente): void {
    this.expedienteDetalle = exp;
    this.modalDetalleAbierto = true;
    this.actualizarScrollBloqueo();
  }

  cerrarModalDetalle(): void {
    this.modalDetalleAbierto = false;
    this.expedienteDetalle = null;
    this.actualizarScrollBloqueo();
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
      'Eliminar Justificativo',
      `¿Confirmas la eliminación del justificativo para el expediente ${exp.numero}? La causa volverá al estado 'Justificando' y se registrará la baja en el historial.`,
      () => {
        const perfil = this.auth.getPerfil();
        const nombre = perfil ? `${perfil.first_name} ${perfil.last_name}` : this.socioActual;
        const legajo = perfil?.legajo || '';
        
        // Sincronizar con backend: dar de baja el descargo y sus evidencias (es_vigente = false)
        this.expedienteApi.eliminarDescargo(exp.id).subscribe({
          next: () => {},
          error: () => {}
        });

        this.dataService.eliminarDescargo(exp.id, { nombre, legajo });
        this.notifications.info(`Justificativo del expediente ${exp.numero} eliminado.`);
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
    } else {
      this.removerScrollBloqueo();
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
    return this.tipoDescargo === 'T02_CERTIFICADO' ? this.LIMITE_T02 : this.LIMITE_T03;
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

  onFileSelected(event: any): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;

    const nuevos = Array.from(input.files);
    const limite = this.limiteActual;
    const totalComprobantes = this.evidenciasExistentes.length + this.archivosSeleccionados.length + nuevos.length;

    if (totalComprobantes > limite) {
      this.notifications.error(`Solo se admite un máximo de ${limite} documentos en total.`);
      input.value = '';
      return;
    }

    for (const f of nuevos) {
      if (f.size > this.MAX_BYTES) {
        this.notifications.error(`El archivo "${f.name}" supera el límite de 5 MB.`);
        input.value = '';
        return;
      }
      const ext = f.name.substring(f.name.lastIndexOf('.')).toLowerCase();
      if (!['.pdf', '.jpg', '.jpeg', '.png'].includes(ext)) {
        this.notifications.error(`El archivo "${f.name}" no tiene un formato válido (PDF, JPG, PNG).`);
        input.value = '';
        return;
      }

      // Validación de duplicados: chequear contra archivos ya guardados
      const yaExisteEnCustodia = this.evidenciasExistentes.some(
        ev => (ev.nombre_original || ev.name || '').toLowerCase() === f.name.toLowerCase()
      );
      if (yaExisteEnCustodia) {
        this.notifications.error(`El documento "${f.name}" ya se encuentra adjunto.`);
        input.value = '';
        return;
      }

      // Validación de duplicados: chequear contra archivos ya seleccionados en esta tanda
      const yaSeleccionado = this.archivosSeleccionados.some(
        sel => sel.name.toLowerCase() === f.name.toLowerCase() && sel.size === f.size
      );
      if (yaSeleccionado) {
        this.notifications.error(`El archivo "${f.name}" ya está seleccionado.`);
        input.value = '';
        return;
      }

      this.archivosSeleccionados.push(f);
    }
    this.nombreArchivo = this.archivosSeleccionados.map(f => f.name).join(', ');
    input.value = '';
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

    if (this.tipoDescargo === 'T02_CERTIFICADO') {
      if (totalComprobantes === 0 && !this.nombreArchivo) {
        this.notifications.error('Debe adjuntar al menos un documento.');
        return;
      }
      if (totalComprobantes > this.LIMITE_T02) {
        this.notifications.error(`Solo se permite un máximo de ${this.LIMITE_T02} documentos.`);
        return;
      }
    } else {
      if (!this.relatoTexto.trim()) {
        this.notifications.error('Por favor ingrese el motivo de la justificación.');
        return;
      }
      if (totalComprobantes > this.LIMITE_T03) {
        this.notifications.error(`Solo se permite un máximo de ${this.LIMITE_T03} documentos.`);
        return;
      }
    }

    const perfil = this.auth.getPerfil();
    const nombre = perfil ? `${perfil.first_name} ${perfil.last_name}` : this.socioActual;
    const legajo = perfil?.legajo || '';
    const expId = this.expedienteSeleccionado.id;

    const guardarEnDataService = (todasLasEvidencias: any[]) => {
      this.dataService.enviarDescargo(
        expId,
        this.tipoDescargo,
        {
          causal: this.tipoDescargo === 'T02_CERTIFICADO' ? this.causalSeleccionada : 'Otro',
          archivo: this.nombreArchivo || (todasLasEvidencias.length > 0 ? todasLasEvidencias[0].nombre_original : undefined),
          archivos: todasLasEvidencias.map(e => e.nombre_original || e.name || 'documento'),
          texto: this.relatoTexto || `Justificación presentada bajo causal: ${this.causalSeleccionada}.`,
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
            texto: this.relatoTexto,
            evidencia_ids: ids
          }).subscribe({
            next: () => guardarEnDataService(todasLasEvidencias),
            error: () => guardarEnDataService(todasLasEvidencias)
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
        texto: this.relatoTexto,
        evidencia_ids: ids
      }).subscribe({
        next: () => guardarEnDataService(this.evidenciasExistentes),
        error: () => guardarEnDataService(this.evidenciasExistentes)
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

  getEstadoLabel(estado: string, exp?: Expediente): string {
    if (estado === 'justificando' && exp) {
      if (this.esPlazoVencido(exp)) {
        return 'Resolviendo';
      }
      const tiempo = this.getCompactCountdownLabel(exp);
      return tiempo ? `Justificando · ${tiempo}` : 'Justificando';
    }
    if (estado === 'revision_resolucion') {
      return exp?.descargo ? 'Revisando Justificación' : 'Resolviendo';
    }

    switch (estado) {
      case 'creado': return 'Expediente Creado';
      case 'justificando': return 'Justificando';
      case 'revision_resolucion': return 'Revisando Justificación';
      case 'pendiente_firma': return 'Pendiente de firma';
      case 'emitido': return 'Emitido';
      default: return estado;
    }
  }

  getEstadoBadgeClass(estado: string, exp?: Expediente): string {
    if (estado === 'justificando' && exp && this.esPlazoVencido(exp)) {
      return 'badge-mat-danger';
    }
    switch (estado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion': return 'badge-mat-info';
      case 'pendiente_firma': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }

  get expedientesOrdenados(): Expediente[] {
    const lista = [...this.misExpedientes];
    lista.sort((a, b) => {
      let valA = (a as any)[this.columnaOrden];
      let valB = (b as any)[this.columnaOrden];
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
