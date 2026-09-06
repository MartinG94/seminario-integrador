import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-mis-expedientes',
  templateUrl: './mis-expedientes.component.html',
  styleUrls: ['./mis-expedientes.component.scss']
})
export class MisExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  misExpedientes: Expediente[] = [];
  socioActual = 'Ignacio Morales';
  saldoNeto = -2.5;

  // Modal T02/T03
  modalAbierto = false;
  expedienteSeleccionado: Expediente | null = null;
  tipoDescargo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO' = 'T02_CERTIFICADO';
  causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
  nombreArchivo = '';
  relatoTexto = '';
  errorMensaje = '';

  private subs: Subscription[] = [];

  constructor(public dataService: TribunalDataService) {}

  ngOnInit(): void {
    const subExp = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
      this.misExpedientes = list.filter(e => e.socio.toLowerCase() === this.socioActual.toLowerCase());
    });
    this.subs.push(subExp);

    const subSocios = this.dataService.socios$.subscribe(socios => {
      const s = socios.find(soc => soc.nombre.toLowerCase() === this.socioActual.toLowerCase());
      if (s) {
        this.saldoNeto = s.saldo;
      }
    });
    this.subs.push(subSocios);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  abrirModalDescargo(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.tipoDescargo = 'T02_CERTIFICADO';
    this.causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
    this.nombreArchivo = '';
    this.relatoTexto = '';
    this.errorMensaje = '';
    this.modalAbierto = true;
  }

  cerrarModal(): void {
    this.modalAbierto = false;
    this.expedienteSeleccionado = null;
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.nombreArchivo = file.name;
    }
  }

  enviarDescargo(): void {
    if (!this.expedienteSeleccionado) return;

    if (this.tipoDescargo === 'T02_CERTIFICADO') {
      if (!this.nombreArchivo) {
        this.errorMensaje = 'Es obligatorio adjuntar el comprobante o constancia digital (PDF, JPG o PNG).';
        return;
      }
    } else {
      if (!this.relatoTexto.trim()) {
        this.errorMensaje = 'Por favor expone detalladamente los hechos y motivos extraordinarios.';
        return;
      }
    }

    this.dataService.enviarDescargo(this.expedienteSeleccionado.id, this.tipoDescargo, {
      causal: this.causalSeleccionada,
      archivo: this.nombreArchivo,
      texto: this.relatoTexto || `Justificación formal presentada bajo causal de ${this.causalSeleccionada}.`
    });

    this.cerrarModal();
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
