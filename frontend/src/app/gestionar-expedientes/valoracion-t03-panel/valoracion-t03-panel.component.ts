import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';

import {
  AntecedenteT03DTO,
  DecisionCausal,
  RegistrarValoracionT03Payload,
  ValoracionT03DTO
} from '../../services/expediente-api.service';
import { NotificationService } from '../../services/notification.service';
import { formatCaseNumber } from '../../utils/case-number.util';
import { MAX_FUNDAMENTO_CAUSAL, MIN_FUNDAMENTO_CAUSAL } from '../gestionar-expedientes.component';

/**
 * Formulario e historial de la valoración de un T03 (S4-03).
 * La sala actúa de contenedor: busca los antecedentes, registra y refresca el historial.
 */
@Component({
  selector: 'app-valoracion-t03-panel',
  templateUrl: './valoracion-t03-panel.component.html',
  styleUrls: ['./valoracion-t03-panel.component.scss']
})
export class ValoracionT03PanelComponent implements OnChanges {
  @Input() descargoId = 0;
  @Input() puedeValorar = false;
  @Input() registrando = false;
  @Input() buscandoAntecedente = false;
  @Input() antecedentes: AntecedenteT03DTO[] = [];
  @Input() historial: ValoracionT03DTO[] = [];

  @Output() registrar = new EventEmitter<RegistrarValoracionT03Payload>();
  @Output() buscarAntecedente = new EventEmitter<string>();
  @Output() quitarAntecedente = new EventEmitter<number>();

  readonly maxFundamento = MAX_FUNDAMENTO_CAUSAL;
  readonly formatearNumero = formatCaseNumber;

  resultado: DecisionCausal | '' = '';
  fundamento = '';
  numeroAntecedente = '';

  constructor(private notifications: NotificationService) {}

  ngOnChanges(changes: SimpleChanges): void {
    const historial = changes['historial'];
    if (historial && !historial.firstChange) {
      this.resultado = '';
      this.fundamento = '';
    }
    const antecedentes = changes['antecedentes'];
    if (antecedentes && !antecedentes.firstChange
        && antecedentes.currentValue.length > antecedentes.previousValue.length) {
      this.numeroAntecedente = '';
    }
  }

  elegirResultado(resultado: DecisionCausal): void {
    this.resultado = resultado;
  }

  condicionAutor(valoracion: ValoracionT03DTO): string {
    return valoracion.autor_condicion === 'NO_INFORMADA'
      ? 'Condición no informada'
      : valoracion.autor_condicion_display;
  }

  agregarAntecedente(): void {
    const numero = this.numeroAntecedente.trim();
    if (!numero) {
      this.notifications.error('Escribí el número del expediente antecedente.');
      return;
    }
    this.buscarAntecedente.emit(numero);
  }

  enviar(): void {
    if (this.registrando) return;
    if (this.buscandoAntecedente) {
      this.notifications.error('Esperá a que termine la búsqueda del antecedente.');
      return;
    }
    if (!this.resultado) {
      this.notifications.error('Elegí si aprobás o desaprobás el T03.');
      return;
    }
    const fundamento = this.fundamento.trim();
    if (fundamento.length < MIN_FUNDAMENTO_CAUSAL) {
      this.notifications.error(`Escribí un fundamento de al menos ${MIN_FUNDAMENTO_CAUSAL} caracteres.`);
      return;
    }
    if (fundamento.length > MAX_FUNDAMENTO_CAUSAL) {
      this.notifications.error(`El fundamento no puede superar los ${MAX_FUNDAMENTO_CAUSAL} caracteres.`);
      return;
    }
    this.registrar.emit({
      resultado: this.resultado,
      fundamento,
      antecedente_ids: this.antecedentes.map(antecedente => antecedente.id)
    });
  }
}
