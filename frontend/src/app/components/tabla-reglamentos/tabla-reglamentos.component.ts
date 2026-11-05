import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy } from '@angular/core';
import { ReglamentoCiteView } from '../../utils/reglamento-format.util';

@Component({
  selector: 'app-tabla-reglamentos',
  templateUrl: './tabla-reglamentos.component.html',
  styleUrls: ['./tabla-reglamentos.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class TablaReglamentosComponent {
  @Input() articulos: ReglamentoCiteView[] = [];
  @Input() editable = false;
  @Input() compacta = false;
  @Input() emptyMessage = 'No hay artículos reglamentarios seleccionados.';
  @Output() remover = new EventEmitter<string>();

  onRemover(raw: string): void {
    this.remover.emit(raw);
  }

  trackByRaw(index: number, item: ReglamentoCiteView): string {
    return item.raw || `${item.documento}-${item.articulo}-${item.inciso}-${index}`;
  }
}
