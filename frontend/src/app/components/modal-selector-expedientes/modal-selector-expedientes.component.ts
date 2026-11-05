import {
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  Output,
  SimpleChanges,
  ViewChild
} from '@angular/core';
import { AntecedenteT03DTO } from '../../services/expediente-api.service';
import { ModalScrollLockService } from '../../services/modal-scroll-lock.service';
import { formatCaseNumber } from '../../utils/case-number.util';

export type FiltroTipoExpediente = 'TODOS' | 'SANCTION' | 'MERIT';

@Component({
  selector: 'app-modal-selector-expedientes',
  templateUrl: './modal-selector-expedientes.component.html',
  styleUrls: ['./modal-selector-expedientes.component.scss']
})
export class ModalSelectorExpedientesComponent implements OnChanges, OnDestroy {
  @Input() abierto = false;
  @Input() tituloModal = 'Seleccionar Expediente(s) de Referencia';
  @Input() subtituloModal = 'Podés seleccionar uno o varios expedientes emitidos como referencia o antecedente.';
  @Input() catalogo: AntecedenteT03DTO[] = [];
  @Input() cargando = false;
  @Input() seleccionados: AntecedenteT03DTO[] = [];

  @Output() seleccionadosChange = new EventEmitter<AntecedenteT03DTO[]>();
  @Output() cerrar = new EventEmitter<void>();

  @ViewChild('searchInput') searchInputElement?: ElementRef<HTMLInputElement>;
  @ViewChild('modalDialog') modalDialogElement?: ElementRef<HTMLElement>;

  filtroTipo: FiltroTipoExpediente = 'TODOS';
  filtroTexto = '';
  seleccionadosLocales: AntecedenteT03DTO[] = [];

  private isLocked = false;

  constructor(private modalScrollLock: ModalScrollLockService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['abierto']) {
      if (this.abierto) {
        this.sincronizarSeleccionados();
        this.filtroTexto = '';
        this.filtroTipo = 'TODOS';
        this.lockScroll();
        setTimeout(() => {
          this.searchInputElement?.nativeElement?.focus();
        }, 100);
      } else {
        this.unlockScroll();
      }
    }
    if (changes['seleccionados'] && !this.abierto) {
      this.sincronizarSeleccionados();
    }
  }

  ngOnDestroy(): void {
    this.unlockScroll();
  }

  private lockScroll(): void {
    if (!this.isLocked) {
      this.modalScrollLock.lock();
      this.isLocked = true;
    }
  }

  private unlockScroll(): void {
    if (this.isLocked) {
      this.modalScrollLock.unlock();
      this.isLocked = false;
    }
  }

  sincronizarSeleccionados(): void {
    this.seleccionadosLocales = [...(this.seleccionados || [])];
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopPropagation();
      this.onCerrar();
    }
  }

  setFiltroTipo(tipo: FiltroTipoExpediente): void {
    this.filtroTipo = tipo;
  }

  limpiarBusqueda(): void {
    this.filtroTexto = '';
  }

  esSancion(exp: AntecedenteT03DTO): boolean {
    if (exp.tipo_accion === 'SANCTION') return true;
    if (exp.tipo_accion === 'MERIT') return false;
    if (exp.puntos !== undefined && exp.puntos !== null) {
      return Number(exp.puntos) < 0;
    }
    return true;
  }

  formatCaseNumber(numero?: string | null): string {
    return formatCaseNumber(numero);
  }

  estaSeleccionado(id: number): boolean {
    return this.seleccionadosLocales.some(e => e.id === id);
  }

  toggleExpediente(exp: AntecedenteT03DTO): void {
    const idx = this.seleccionadosLocales.findIndex(e => e.id === exp.id);
    if (idx >= 0) {
      this.seleccionadosLocales = this.seleccionadosLocales.filter(e => e.id !== exp.id);
    } else {
      this.seleccionadosLocales = [...this.seleccionadosLocales, exp];
    }
  }

  limpiarSeleccion(): void {
    this.seleccionadosLocales = [];
  }

  confirmar(): void {
    this.seleccionadosChange.emit([...this.seleccionadosLocales]);
    this.onCerrar();
  }

  onCerrar(): void {
    this.unlockScroll();
    this.cerrar.emit();
  }

  contarPorTipo(tipo: 'SANCTION' | 'MERIT'): number {
    return (this.catalogo || []).filter(exp => tipo === 'SANCTION' ? this.esSancion(exp) : !this.esSancion(exp)).length;
  }

  contarSeleccionadosPorTipo(tipo: 'SANCTION' | 'MERIT'): number {
    return this.seleccionadosLocales.filter(exp => tipo === 'SANCTION' ? this.esSancion(exp) : !this.esSancion(exp)).length;
  }

  get expedientesFiltrados(): AntecedenteT03DTO[] {
    let resultado = this.catalogo || [];

    if (this.filtroTipo === 'SANCTION') {
      resultado = resultado.filter(exp => this.esSancion(exp));
    } else if (this.filtroTipo === 'MERIT') {
      resultado = resultado.filter(exp => !this.esSancion(exp));
    }

    if (this.filtroTexto && this.filtroTexto.trim()) {
      const q = this.filtroTexto.trim().toLowerCase();
      resultado = resultado.filter(exp => {
        const numOriginal = (exp.numero || '').toLowerCase();
        const numFormat = this.formatCaseNumber(exp.numero).toLowerCase();
        const titulo = (exp.titulo || '').toLowerCase();
        const motivo = (exp.motivo || '').toLowerCase();
        const reglamento = (exp.reglamento_invocado || '').toLowerCase();
        return (
          numOriginal.includes(q) ||
          numFormat.includes(q) ||
          titulo.includes(q) ||
          motivo.includes(q) ||
          reglamento.includes(q)
        );
      });
    }

    return resultado;
  }

  trackById(index: number, item: AntecedenteT03DTO): number {
    return item.id ?? index;
  }
}
