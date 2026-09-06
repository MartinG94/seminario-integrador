import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Expediente, EstadoExpediente } from '../services/tribunal-data.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-gestionar-expedientes',
  templateUrl: './gestionar-expedientes.component.html',
  styleUrls: ['./gestionar-expedientes.component.scss']
})
export class GestionarExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  vistaActual: 'kanban' | 'tabla' = 'kanban';
  filtroTexto = '';
  columnaOrden = 'numero';
  ordenAscendente = true;

  // Estados canónicos consolidados
  columnasKanban: { estado: EstadoExpediente; titulo: string; icon: string }[] = [
    { estado: 'creado', titulo: 'Expediente Creado', icon: 'file_copy' },
    { estado: 'justificando', titulo: 'En período de justificaciones', icon: 'schedule' },
    { estado: 'revision_resolucion', titulo: 'En revisión y resolución', icon: 'gavel' },
    { estado: 'pendiente_firma', titulo: 'Pendiente de firma y envío', icon: 'history_edu' },
    { estado: 'emitido', titulo: 'Expedientes ya emitidos', icon: 'verified' }
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

  private subs: Subscription[] = [];

  constructor(public dataService: TribunalDataService) {}

  ngOnInit(): void {
    const sub = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  get expedientesFiltrados(): Expediente[] {
    let result = [...this.expedientes];
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase();
      result = result.filter(e => 
        e.numero.toLowerCase().includes(q) ||
        e.socio.toLowerCase().includes(q) ||
        e.subcomision.toLowerCase().includes(q) ||
        e.motivo.toLowerCase().includes(q)
      );
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
    this.mostrarNotificacion('Dictamen votado. Se alcanzó mayoría calificada (>= 2/3). Expediente pasa a Pendiente de firma.');
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
      case 'revision_resolucion': return 'En revisión y resolución';
      case 'pendiente_firma': return 'Pendiente de firma y envío';
      case 'emitido': return 'Expedientes ya emitidos';
      default: return estado;
    }
  }

  getEstadoBadgeClass(estado: string): string {
    switch (estado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion': return 'badge-mat-info';
      case 'pendiente_firma': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }
}
