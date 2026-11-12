import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { AntecedenteT03DTO } from '../../services/expediente-api.service';
import { formatCaseNumber } from '../../utils/case-number.util';

@Component({
  selector: 'app-tabla-expedientes-referenciados',
  templateUrl: './tabla-expedientes-referenciados.component.html',
  styleUrls: ['./tabla-expedientes-referenciados.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TablaExpedientesReferenciadosComponent {
  @Input() expedientes: AntecedenteT03DTO[] = [];
  @Input() editable = false;
  @Input() compacta = false;
  @Input() emptyMessage = 'No hay expedientes de referencia seleccionados.';
  @Output() remover = new EventEmitter<number>();

  formatCaseNumber(numero?: string | null): string {
    return formatCaseNumber(numero);
  }

  onRemover(id: number): void {
    this.remover.emit(id);
  }

  trackById(index: number, item: AntecedenteT03DTO): number {
    return item.id ?? index;
  }

  esSancion(exp: AntecedenteT03DTO): boolean {
    if (exp.tipo_accion === 'SANCTION') return true;
    if (exp.tipo_accion === 'MERIT') return false;
    if (exp.puntos !== undefined && exp.puntos !== null) {
      return Number(exp.puntos) < 0;
    }
    return true;
  }
}
