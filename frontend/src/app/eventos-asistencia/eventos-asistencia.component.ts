import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, EventoAsistencia, Socio } from '../services/tribunal-data.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-eventos-asistencia',
  templateUrl: './eventos-asistencia.component.html',
  styleUrls: ['./eventos-asistencia.component.scss']
})
export class EventosAsistenciaComponent implements OnInit, OnDestroy {
  eventos: EventoAsistencia[] = [];
  socios: Socio[] = [];
  eventoActivo: EventoAsistencia | null = null;
  socioSimulado = 'Ignacio Morales';
  estaEscaneando = false;
  mensajeAlerta = '';
  tipoAlerta: 'success' | 'danger' | 'info' = 'info';

  private subs: Subscription[] = [];

  constructor(public dataService: TribunalDataService) {}

  ngOnInit(): void {
    const subEvt = this.dataService.eventos$.subscribe(list => {
      this.eventos = list;
      if (!this.eventoActivo && list.length > 0) {
        this.eventoActivo = list.find(e => e.estado === 'EN_CURSO') || list[0];
      } else if (this.eventoActivo) {
        this.eventoActivo = list.find(e => e.id === this.eventoActivo?.id) || list[0];
      }
    });
    this.subs.push(subEvt);

    const subSoc = this.dataService.socios$.subscribe(list => {
      this.socios = list;
    });
    this.subs.push(subSoc);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  seleccionarEvento(evt: EventoAsistencia): void {
    this.eventoActivo = evt;
  }

  pasarElDedo(): void {
    if (!this.eventoActivo) return;
    if (this.eventoActivo.estado === 'CERRADO') {
      this.mostrarMensaje('El evento se encuentra formalmente cerrado. No se admiten registros biométricos.', 'danger');
      return;
    }

    this.estaEscaneando = true;
    setTimeout(() => {
      this.estaEscaneando = false;
      const ok = this.dataService.registrarAsistenciaBiometrica(this.eventoActivo!.id, this.socioSimulado);
      if (ok) {
        this.mostrarMensaje(`¡Asistencia confirmada! Huella verificada para ${this.socioSimulado}.`, 'success');
      }
    }, 600);
  }

  cerrarEvento(): void {
    if (!this.eventoActivo) return;
    if (confirm(`¿Confirmas el cierre formal de asistencia para "${this.eventoActivo.titulo}"? Se generarán expedientes disciplinarios de oficio para los ${this.eventoActivo.ausentes} socios ausentes.`)) {
      const res = this.dataService.cerrarEvento(this.eventoActivo.id);
      this.mostrarMensaje(`Evento cerrado formalmente. Se abrieron ${res.expedientesGenerados} expedientes en estado Expediente Creado.`, 'info');
    }
  }

  mostrarMensaje(msg: string, tipo: 'success' | 'danger' | 'info'): void {
    this.mensajeAlerta = msg;
    this.tipoAlerta = tipo;
    setTimeout(() => { this.mensajeAlerta = ''; }, 4500);
  }
}
