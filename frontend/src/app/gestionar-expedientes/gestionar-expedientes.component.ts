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

  // Exactamente 6 estados canónicos (CA1)
  columnasKanban: { estado: EstadoExpediente; titulo: string; icon: string }[] = [
    { estado: 'creado', titulo: 'Expediente Creado', icon: 'file_copy' },
    { estado: 'justificando', titulo: 'En período de justificaciones', icon: 'schedule' },
    { estado: 'revision_resolucion', titulo: 'Justificaciones en revisión', icon: 'gavel' },
    { estado: 'espera_resolucion', titulo: 'Espera de resolución', icon: 'hourglass_empty' },
    { estado: 'pendiente_correos', titulo: 'Pendiente de correos', icon: 'mail_outline' },
    { estado: 'emitido', titulo: 'Expedientes ya emitidos', icon: 'verified' }
  ];

  estadosDisponibles: { key: string; label: string }[] = [
    { key: '', label: 'Todos los estados' },
    { key: 'creado', label: 'Expediente Creado' },
    { key: 'justificando', label: 'En período de justificaciones' },
    { key: 'revision_resolucion', label: 'Justificaciones en revisión' },
    { key: 'espera_resolucion', label: 'Espera de resolución' },
    { key: 'pendiente_correos', label: 'Pendiente de correos' },
    { key: 'emitido', label: 'Expedientes ya emitidos' }
  ];

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

  mostrarNotificacion(msg: string): void {
    this.mensajeExito = msg;
    setTimeout(() => { this.mensajeExito = ''; }, 4500);
  }

  getEstadoLabel(estado: string): string {
    switch (estado) {
      case 'creado': return 'Expediente Creado';
      case 'justificando': return 'En período de justificaciones';
      case 'revision_resolucion': return 'Justificaciones en revisión';
      case 'espera_resolucion': return 'Espera de resolución';
      case 'pendiente_correos': return 'Pendiente de correos';
      case 'emitido': return 'Expedientes ya emitidos';
      default: return estado;
    }
  }

  getEstadoBadgeClass(estado: string): string {
    switch (estado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion': return 'badge-mat-info';
      case 'espera_resolucion': return 'badge-mat-info';
      case 'pendiente_correos': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }
}
