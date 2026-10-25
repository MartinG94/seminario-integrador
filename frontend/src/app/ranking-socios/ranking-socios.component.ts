import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { RankingService } from '../services/ranking.service';
import { NotificationService } from '../services/notification.service';
import { RankingSocio } from './ranking-socio.model';
import { RANKING_THRESHOLDS } from './ranking-thresholds';
// Ficha Institucional reemplazada por Detalle de expedientes (mejora UX ranking); se conserva sin uso.
// import { SocioLegajoDialogComponent } from './socio-legajo-dialog/socio-legajo-dialog.component';
import { ExpedientesSocioDialogComponent } from './expedientes-socio-dialog/expedientes-socio-dialog.component';

export type RankingColumnaOrden =
  | 'posicion'
  | 'socio'
  | 'legajo'
  | 'categoria'
  | 'grupo'
  | 'subcomision'
  | 'saldo';

@Component({
  selector: 'app-ranking-socios',
  templateUrl: './ranking-socios.component.html',
  styleUrls: ['./ranking-socios.component.scss']
})
export class RankingSociosComponent implements OnInit {
  socios: RankingSocio[] = [];
  sortKey: RankingColumnaOrden | null = null;
  sortDir: 'asc' | 'desc' = 'asc';

  filtroTexto = '';
  filtroCategoria: 'ACTIVO' | 'PASIVO' | '' = '';
  filtroSubcomision = '';
  filtroGrupo = '';

  subcomisiones: string[] = [];
  grupos: string[] = [];

  paginaActual = 1;
  tamanoPagina = 10;
  opcionesTamano = [10, 25, 50, 100, 0];

  tabActiva: 'general' | 'alertas' = 'general';

  cargando = false;
  error: string | null = null;

  constructor(
    public rankingService: RankingService,
    public dialog: MatDialog,
    private notifications: NotificationService
  ) {}

  // Ficha Institucional reemplazada por Detalle de expedientes (mejora UX ranking); se conserva sin uso.
  /*
  abrirLegajoSocio(socio: RankingSocio): void {
    if (!socio) return;
    this.dialog.open(SocioLegajoDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: {
        socioId: socio.id,
        nombreSocio: `${socio.nombre} ${socio.apellido}`.trim(),
        saldo: socio.saldo
      }
    });
  }
  */

  abrirExpedientesSocio(socio: RankingSocio): void {
    if (!socio) return;

    this.dialog.open(ExpedientesSocioDialogComponent, {
      width: '100%',
      maxWidth: '700px',
      data: {
        legajo: socio.legajo,
        nombreSocio: `${socio.nombre} ${socio.apellido}`.trim(),
        saldo: socio.saldo
      }
    });
  }

  onRowKeyDown(event: KeyboardEvent, socio: RankingSocio): void {
    if (!event) return;

    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
      event.preventDefault();
      this.abrirExpedientesSocio(socio);
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

  ngOnInit(): void {
    this.cargando = true;
    this.error = null;

    this.rankingService.obtenerRanking().subscribe({
      next: (socios) => {
        this.socios = socios;

        // Precompute fixed posicion across the entire padrón by saldo desc (tie-breaker: apellido asc, nombre asc)
        const rankingOrdenado = [...this.socios].sort((a, b) => {
          const diffSaldo = b.saldo - a.saldo;
          if (diffSaldo !== 0) {
            return diffSaldo;
          }
          const diffApellido = a.apellido.localeCompare(b.apellido, 'es');
          if (diffApellido !== 0) {
            return diffApellido;
          }
          return a.nombre.localeCompare(b.nombre, 'es');
        });

        rankingOrdenado.forEach((socio, index) => {
          socio.posicion = index + 1;
        });

        this.subcomisiones = [
          ...new Set(this.socios.map((s) => s.subcomision).filter(Boolean))
        ].sort((a, b) => a.localeCompare(b, 'es'));

        const gruposUnicos = [
          ...new Set(
            this.socios
              .map((s) => s.grupo)
              .filter((g): g is string => !!g && g.trim() !== '' && g !== 'Sin grupo')
          )
        ];
        this.grupos = gruposUnicos.sort((a, b) => {
          const numA = parseInt(a.replace(/\D/g, '') || '0', 10);
          const numB = parseInt(b.replace(/\D/g, '') || '0', 10);
          return numA - numB;
        });

        this.cargando = false;
      },
      error: () => {
        this.socios = [];
        this.subcomisiones = [];
        this.grupos = [];
        this.error = 'No se pudo cargar el ranking. Intentá nuevamente.';
        this.notifications.error(this.error);
        this.cargando = false;
      }
    });
  }

  onFiltroChange(texto: string): void {
    this.filtroTexto = texto;
    this.paginaActual = 1;
  }

  limpiarFiltros(): void {
    this.filtroTexto = '';
    this.filtroCategoria = '';
    this.filtroSubcomision = '';
    this.filtroGrupo = '';
    this.paginaActual = 1;
  }

  get ordenSaldo(): 'asc' | 'desc' | null {
    return this.sortKey === 'saldo' ? this.sortDir : null;
  }

  set ordenSaldo(val: 'asc' | 'desc' | null) {
    if (val) {
      this.sortKey = 'saldo';
      this.sortDir = val;
    } else {
      if (this.sortKey === 'saldo') {
        this.sortKey = null;
      }
    }
  }

  alternarOrden(columna: RankingColumnaOrden): void {
    if (this.sortKey !== columna) {
      this.sortKey = columna;
      this.sortDir = columna === 'saldo' ? 'desc' : 'asc';
    } else {
      if (columna === 'saldo') {
        if (this.sortDir === 'desc') {
          this.sortDir = 'asc';
        } else {
          this.sortKey = null;
          this.sortDir = 'asc';
        }
      } else {
        if (this.sortDir === 'asc') {
          this.sortDir = 'desc';
        } else {
          this.sortKey = null;
          this.sortDir = 'asc';
        }
      }
    }
    this.paginaActual = 1;
  }

  alternarOrdenSaldo(): void {
    this.alternarOrden('saldo');
  }

  getIconoOrden(columna: RankingColumnaOrden): string {
    if (this.sortKey !== columna) return 'swap_vert';
    return this.sortDir === 'asc' ? 'arrow_upward' : 'arrow_downward';
  }

  getRowClass(s: RankingSocio): string {
    if (s.saldo <= RANKING_THRESHOLDS.cese) return 'row-cese';
    if (s.saldo <= RANKING_THRESHOLDS.alerta) return 'row-alerta';
    return '';
  }

  getBadgeClase(socio: RankingSocio): string {
    if (socio.saldo <= RANKING_THRESHOLDS.cese) return 'badge-mat-danger';
    if (socio.saldo <= RANKING_THRESHOLDS.alerta) return 'badge-mat-warning';
    return 'badge-mat-success';
  }

  getEstadoDescripcion(socio: RankingSocio): string {
    if (socio.saldo <= RANKING_THRESHOLDS.cese) return 'Límite Crítico: Cese Estatutario';
    if (socio.saldo <= RANKING_THRESHOLDS.alerta) return 'Alerta Preventiva';
    return 'Habilitado Regular';
  }

  setTab(tab: 'general' | 'alertas'): void {
    this.tabActiva = tab;
    this.paginaActual = 1;
  }

  get cantidadSociosEnAlerta(): number {
    return this.socios.filter((s) => s.saldo <= RANKING_THRESHOLDS.alerta).length;
  }

  get sociosOrdenados(): RankingSocio[] {
    let list = [...this.socios];

    if (this.tabActiva === 'alertas') {
      list = list.filter((s) => s.saldo <= RANKING_THRESHOLDS.alerta);
    }

    if (this.filtroCategoria) {
      list = list.filter((s) => s.categoria === this.filtroCategoria);
    }

    if (this.filtroSubcomision) {
      list = list.filter((s) => s.subcomision === this.filtroSubcomision);
    }

    if (this.filtroGrupo) {
      if (this.filtroGrupo === 'SIN_GRUPO') {
        list = list.filter((s) => !s.grupo || s.grupo.trim() === '' || s.grupo === 'Sin grupo');
      } else {
        list = list.filter((s) => s.grupo === this.filtroGrupo);
      }
    }

    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase();
      list = list.filter(
        (s) =>
          s.nombre.toLowerCase().includes(q) ||
          s.apellido.toLowerCase().includes(q) ||
          s.legajo.toLowerCase().includes(q) ||
          (s.subcomision && s.subcomision.toLowerCase().includes(q)) ||
          (s.grupo && s.grupo.toLowerCase().includes(q))
      );
    }

    list.sort((a, b) => {
      let diff = 0;

      if (this.sortKey) {
        switch (this.sortKey) {
          case 'posicion':
            diff = (a.posicion ?? 0) - (b.posicion ?? 0);
            break;
          case 'socio':
            diff =
              a.apellido.localeCompare(b.apellido, 'es') ||
              a.nombre.localeCompare(b.nombre, 'es');
            break;
          case 'legajo': {
            const numA = parseInt(a.legajo.replace(/\D/g, '') || '0', 10);
            const numB = parseInt(b.legajo.replace(/\D/g, '') || '0', 10);
            diff = numA - numB;
            break;
          }
          case 'categoria':
            diff = a.categoria.localeCompare(b.categoria, 'es');
            break;
          case 'grupo': {
            const numA = a.grupo
              ? parseInt(a.grupo.replace(/\D/g, '') || '0', 10)
              : Number.MAX_SAFE_INTEGER;
            const numB = b.grupo
              ? parseInt(b.grupo.replace(/\D/g, '') || '0', 10)
              : Number.MAX_SAFE_INTEGER;
            diff = numA - numB;
            break;
          }
          case 'subcomision':
            diff = (a.subcomision || '').localeCompare(b.subcomision || '', 'es');
            break;
          case 'saldo':
            diff = a.saldo - b.saldo;
            break;
        }

        if (diff !== 0) {
          return this.sortDir === 'desc' ? -diff : diff;
        }
      } else {
        // Default sort: Grupo numeric + Apellido + Nombre
        const numA = a.grupo
          ? parseInt(a.grupo.replace(/\D/g, '') || '0', 10)
          : Number.MAX_SAFE_INTEGER;
        const numB = b.grupo
          ? parseInt(b.grupo.replace(/\D/g, '') || '0', 10)
          : Number.MAX_SAFE_INTEGER;
        if (numA !== numB) {
          return numA - numB;
        }
      }

      // Secondary tie-breaker: Apellido + Nombre
      const diffApellido = a.apellido.localeCompare(b.apellido, 'es');
      if (diffApellido !== 0) {
        return diffApellido;
      }
      return a.nombre.localeCompare(b.nombre, 'es');
    });

    return list;
  }

  get sociosPaginados(): RankingSocio[] {
    if (this.tamanoPagina === 0) {
      return this.sociosOrdenados;
    }
    const inicio = (this.paginaActual - 1) * this.tamanoPagina;
    return this.sociosOrdenados.slice(inicio, inicio + this.tamanoPagina);
  }

  get totalPaginas(): number {
    if (this.tamanoPagina === 0) {
      return 1;
    }
    return Math.max(1, Math.ceil(this.sociosOrdenados.length / this.tamanoPagina));
  }

  cambiarPagina(pagina: number): void {
    if (pagina >= 1 && pagina <= this.totalPaginas) {
      this.paginaActual = pagina;
    }
  }

  irAPrimera(): void {
    this.cambiarPagina(1);
  }

  irAUltima(): void {
    this.cambiarPagina(this.totalPaginas);
  }

  cambiarTamanoPagina(tamano: number): void {
    this.tamanoPagina = Number(tamano);
    this.paginaActual = 1;
  }

  get textoContador(): string {
    const total = this.sociosOrdenados.length;
    if (total === 0) {
      return 'Mostrando 0 de 0 socios';
    }
    if (this.tamanoPagina === 0) {
      return `Mostrando 1–${total} de ${total} socios`;
    }
    const inicio = (this.paginaActual - 1) * this.tamanoPagina + 1;
    const fin = Math.min(this.paginaActual * this.tamanoPagina, total);
    return `Mostrando ${inicio}–${fin} de ${total} socios`;
  }
}
