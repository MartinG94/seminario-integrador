import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Expediente, EstadoExpediente } from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-gestionar-expedientes',
  templateUrl: './gestionar-expedientes.component.html',
  styleUrls: ['./gestionar-expedientes.component.scss']
})
export class GestionarExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  vistaActual: 'kanban' | 'tabla' = 'kanban';

  // Filtros explícitos (CA2)
  filtroSocio: string = '';
  filtroEstado: string = '';
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

  // Estado de colapso de columnas
  columnasColapsadas: { [estado: string]: boolean } = {
    emitido: false
  };

  // Modales
  modalDetalleAbierto = false;
  modalVotacionAbierto = false;
  modalFirmaAbierto = false;
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

  mensajeExito = '';
  cargando = false;

  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService
  ) {}

  get puedeVotarOFirmar(): boolean {
    return this.auth.tieneRol('TD', 'ADMIN');
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
    const filtros: any = {};
    if (this.filtroSocio.trim()) filtros.socio = this.filtroSocio.trim();
    if (this.filtroEstado.trim()) filtros.estado = this.filtroEstado.trim();
    if (this.filtroFechaDesde) filtros.fecha_desde = this.filtroFechaDesde;
    if (this.filtroFechaHasta) filtros.fecha_hasta = this.filtroFechaHasta;

    this.dataService.obtenerTablero(filtros).subscribe({
      next: () => {
        this.cargando = false;
      },
      error: () => {
        // En caso de error o backend no disponible, se mantiene la colección local
        this.cargando = false;
      }
    });
  }

  limpiarFiltros(): void {
    this.filtroSocio = '';
    this.filtroEstado = '';
    this.filtroFechaDesde = '';
    this.filtroFechaHasta = '';
    this.cargarDatosTablero();
  }

  get expedientesFiltrados(): Expediente[] {
    let result = [...this.expedientes];

    // Filtro por socio en memoria (fallback / reactivo)
    if (this.filtroSocio.trim()) {
      const q = this.filtroSocio.trim().toLowerCase();
      result = result.filter(e =>
        (e.socio && e.socio.toLowerCase().includes(q)) ||
        (e.legajo && e.legajo.toLowerCase().includes(q)) ||
        (e.numero && e.numero.toLowerCase().includes(q))
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

    // Filtro por rango de fechas
    if (this.filtroFechaDesde) {
      result = result.filter(e => !e.fechaCreacion || e.fechaCreacion >= this.filtroFechaDesde);
    }
    if (this.filtroFechaHasta) {
      result = result.filter(e => !e.fechaCreacion || e.fechaCreacion <= this.filtroFechaHasta);
    }

    result.sort((a, b) => {
      let valA = (a as any)[this.columnaOrden];
      let valB = (b as any)[this.columnaOrden];
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
        const errorMsg = err?.error?.to_status || err?.error?.detail || 'No se pudo realizar la transición.';
        this.mostrarNotificacion(`Error: ${errorMsg}`);
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
    this.modalDetalleAbierto = true;
  }

  abrirVotacion(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalVotacionAbierto = true;
  }

  abrirFirma(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.modalFirmaAbierto = true;
  }

  cerrarModales(): void {
    this.modalDetalleAbierto = false;
    this.modalVotacionAbierto = false;
    this.modalFirmaAbierto = false;
    this.expedienteSeleccionado = null;
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

  confirmarFirmaColegiado(): void {
    if (!this.expedienteSeleccionado) return;
    this.juecesDisponibles.forEach(juez => {
      this.dataService.firmarResolucion(this.expedienteSeleccionado!.id, juez);
    });
    this.mostrarNotificacion('Resolución perfeccionada con las 3 firmas del Tribunal colegiado e impacto en saldo del socio.');
    this.cerrarModales();
  }

  mostrarNotificacion(msg: string): void {
    this.mensajeExito = msg;
    setTimeout(() => { this.mensajeExito = ''; }, 4500);
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
}
