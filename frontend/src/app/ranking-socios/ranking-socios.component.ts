import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { PageEvent } from '@angular/material/paginator';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged, takeUntil } from 'rxjs/operators';
import { RankingService } from '../services/ranking.service';
import { NotificationService } from '../services/notification.service';
import { RankingSocio } from './ranking-socio.model';
import { RANKING_THRESHOLDS } from './ranking-thresholds';
import { TrackByUtils } from '../utils/track-by.util';
import { PaginatedResponse, RankingPaginationParams } from '../models/paginated-response.model';
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
  styleUrls: ['./ranking-socios.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RankingSociosComponent implements OnInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();
  private readonly search$ = new Subject<string>();
  private searchDebounceSubInitialized = false;
  private subcomisionesAcumuladas = new Set<string>();
  private gruposAcumulados = new Set<string>();

  private _socios: RankingSocio[] = [];
  get socios(): RankingSocio[] {
    return this._socios;
  }
  set socios(val: RankingSocio[]) {
    this._socios = val;
    this.markDirty();
  }

  private _sortKey: RankingColumnaOrden | null = null;
  get sortKey(): RankingColumnaOrden | null {
    return this._sortKey;
  }
  set sortKey(val: RankingColumnaOrden | null) {
    this._sortKey = val;
    this.markDirty();
  }

  private _sortDir: 'asc' | 'desc' = 'asc';
  get sortDir(): 'asc' | 'desc' {
    return this._sortDir;
  }
  set sortDir(val: 'asc' | 'desc') {
    this._sortDir = val;
    this.markDirty();
  }

  private _filtroTexto = '';
  get filtroTexto(): string {
    return this._filtroTexto;
  }
  set filtroTexto(val: string) {
    this._filtroTexto = val;
    this.markDirty();
  }

  private _filtroCategoria: 'ACTIVO' | 'PASIVO' | '' = '';
  get filtroCategoria(): 'ACTIVO' | 'PASIVO' | '' {
    return this._filtroCategoria;
  }
  set filtroCategoria(val: 'ACTIVO' | 'PASIVO' | '') {
    this._filtroCategoria = val;
    this.markDirty();
  }

  private _filtroSubcomision = '';
  get filtroSubcomision(): string {
    return this._filtroSubcomision;
  }
  set filtroSubcomision(val: string) {
    this._filtroSubcomision = val;
    this.markDirty();
  }

  private _filtroGrupo = '';
  get filtroGrupo(): string {
    return this._filtroGrupo;
  }
  set filtroGrupo(val: string) {
    this._filtroGrupo = val;
    this.markDirty();
  }

  subcomisiones: string[] = [];
  grupos: string[] = [];

  private _paginaActual = 1;
  get paginaActual(): number {
    return this._paginaActual;
  }
  set paginaActual(val: number) {
    this._paginaActual = val;
    this._sociosPaginadosCache = null;
    this.cdr.markForCheck();
  }

  private _tamanoPagina = 10;
  get tamanoPagina(): number {
    return this._tamanoPagina;
  }
  set tamanoPagina(val: number) {
    this._tamanoPagina = val;
    this.markDirty();
  }

  opcionesTamano = [10, 20, 50, 100, 0];
  readonly pageSizeOptions = [10, 20, 50, 100];
  totalRegistros = 0;
  serverPaginated = false;
  private hadServerPagination = false;

  private _soloAlertas = false;
  get soloAlertas(): boolean {
    return this._soloAlertas;
  }
  set soloAlertas(val: boolean) {
    this._soloAlertas = val;
    this.markDirty();
  }

  get tabActiva(): 'general' | 'alertas' {
    return this.soloAlertas ? 'alertas' : 'general';
  }
  set tabActiva(val: 'general' | 'alertas') {
    this.soloAlertas = val === 'alertas';
  }

  cargando = false;
  error: string | null = null;

  // Cached filtered and paginated arrays to avoid layout thrashing and pure getters
  private _sociosOrdenadosCache: RankingSocio[] | null = null;
  private _sociosPaginadosCache: RankingSocio[] | null = null;

  readonly trackBySocioId = (index: number, item: RankingSocio): string =>
    TrackByUtils.bySocio(index, item);

  readonly trackByValue = (_index: number, item: string): string => item;

  constructor(
    public rankingService: RankingService,
    public dialog: MatDialog,
    private notifications: NotificationService,
    private cdr: ChangeDetectorRef
  ) {}

  private markDirty(): void {
    this._sociosOrdenadosCache = null;
    this._sociosPaginadosCache = null;
    this.cdr?.markForCheck();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

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
    if (!this.searchDebounceSubInitialized) {
      this.searchDebounceSubInitialized = true;
      this.search$
        .pipe(debounceTime(300), distinctUntilChanged(), takeUntil(this.destroy$))
        .subscribe(() => {
          this.paginaActual = 1;
          this.cargarRanking();
        });
    }
    this.cargarRanking();
  }

  private buildServerOrdering(): string {
    if (!this.sortKey) {
      return 'grupo,apellido,nombre';
    }
    const prefix = this.sortDir === 'desc' ? '-' : '';
    switch (this.sortKey) {
      case 'posicion':
        return this.sortDir === 'desc' ? 'saldo' : '-saldo';
      case 'socio':
        return `${prefix}apellido,${prefix}nombre`;
      case 'legajo':
        return `${prefix}legajo`;
      case 'categoria':
        return `${prefix}categoria`;
      case 'grupo':
        return `${prefix}grupo`;
      case 'subcomision':
        return `${prefix}subcomision`;
      case 'saldo':
        return `${prefix}saldo`;
      default:
        return 'grupo,apellido,nombre';
    }
  }

  cargarRanking(): void {
    this.cargando = true;
    this.error = null;
    this.cdr?.markForCheck();

    const params: RankingPaginationParams = {
      ordering: this.buildServerOrdering(),
      search: this.filtroTexto.trim() || undefined,
      categoria: this.filtroCategoria || undefined,
      subcomision: this.filtroSubcomision || undefined,
      grupo: this.filtroGrupo || undefined,
      solo_alertas: this.soloAlertas ? true : undefined,
    };
    if (this.tamanoPagina === 0) {
      params.all = true;
    } else {
      params.page = this.paginaActual;
      params.page_size = this.tamanoPagina;
    }

    this.rankingService
      .obtenerRanking(params)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          const socios = Array.isArray(response) ? response : (response?.results ?? []);
          const countVal =
            !Array.isArray(response) && typeof response?.count === 'number'
              ? response.count
              : socios.length;

          this.totalRegistros = countVal;
          const esParcialServidor =
            !Array.isArray(response) &&
            (socios.length < countVal || (response?.current_page ?? 1) > 1);
          this.serverPaginated = esParcialServidor;
          if (esParcialServidor) {
            this.hadServerPagination = true;
          }

          if (!esParcialServidor && !this.hadServerPagination) {
            // Precompute fixed posicion across the full client list by saldo desc (tie-breaker: apellido asc, nombre asc)
            const rankingOrdenado = [...socios].sort((a, b) => {
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
          } else {
            const offset =
              this.tamanoPagina > 0 ? (this.paginaActual - 1) * this.tamanoPagina : 0;
            socios.forEach((socio, index) => {
              if (socio.posicion === undefined || socio.posicion === null) {
                socio.posicion = offset + index + 1;
              }
            });
          }

          this.socios = socios;

          // Refrescar catálogos manteniendo opciones vistas en páginas previas cuando hay paginación servidor
          if (!this.hadServerPagination) {
            this.subcomisionesAcumuladas.clear();
            this.gruposAcumulados.clear();
          }
          socios.forEach((s) => {
            if (s.subcomision && s.subcomision !== 'Sin Subcomisión') {
              this.subcomisionesAcumuladas.add(s.subcomision);
            }
            if (s.grupo && s.grupo.trim() !== '' && s.grupo !== 'Sin grupo') {
              this.gruposAcumulados.add(s.grupo);
            }
          });
          if (!this.hadServerPagination) {
            socios.forEach((s) => {
              if (s.subcomision) this.subcomisionesAcumuladas.add(s.subcomision);
            });
          }

          this.subcomisiones = [...this.subcomisionesAcumuladas].sort((a, b) =>
            a.localeCompare(b, 'es')
          );
          this.grupos = [...this.gruposAcumulados].sort((a, b) => {
            const numA = parseInt(a.replace(/\D/g, '') || '0', 10);
            const numB = parseInt(b.replace(/\D/g, '') || '0', 10);
            return numA - numB;
          });

          this.cargando = false;
          this.markDirty();
        },
        error: () => {
          this.socios = [];
          this.totalRegistros = 0;
          if (!this.hadServerPagination) {
            this.subcomisiones = [];
            this.grupos = [];
          }
          this.error = 'No se pudo cargar el ranking. Intentá nuevamente.';
          this.notifications.error(this.error);
          this.cargando = false;
          this.markDirty();
        }
      });
  }

  onFiltroSelectChange(): void {
    this.paginaActual = 1;
    this.cargarRanking();
  }

  onFiltroChange(texto: string): void {
    this.filtroTexto = texto;
    this.paginaActual = 1;
    this.search$.next(texto);
  }

  limpiarFiltros(): void {
    this.filtroTexto = '';
    this.filtroCategoria = '';
    this.filtroSubcomision = '';
    this.filtroGrupo = '';
    this.soloAlertas = false;
    this.paginaActual = 1;
    if (this.serverPaginated || this.hadServerPagination) {
      this.cargarRanking();
    } else {
      this.markDirty();
    }
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
    if (this.serverPaginated || this.hadServerPagination) {
      this.cargarRanking();
    }
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

  toggleFiltroAlerta(): void {
    this.soloAlertas = !this.soloAlertas;
    this.paginaActual = 1;
    if (this.serverPaginated || this.hadServerPagination) {
      this.cargarRanking();
    }
  }

  setTab(tab: 'general' | 'alertas'): void {
    this.soloAlertas = tab === 'alertas';
    this.paginaActual = 1;
    if (this.serverPaginated || this.hadServerPagination) {
      this.cargarRanking();
    }
  }

  get cantidadSociosEnAlerta(): number {
    return this.socios.filter((s) => s.saldo <= RANKING_THRESHOLDS.alerta).length;
  }

  get sociosOrdenados(): RankingSocio[] {
    if (this.serverPaginated) {
      return this.socios;
    }
    if (this._sociosOrdenadosCache) {
      return this._sociosOrdenadosCache;
    }

    let list = [...this.socios];

    if (this.soloAlertas) {
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

    this._sociosOrdenadosCache = list;
    return list;
  }

  get sociosPaginados(): RankingSocio[] {
    if (this.serverPaginated) {
      return this.socios;
    }
    if (this._sociosPaginadosCache) {
      return this._sociosPaginadosCache;
    }
    if (this.tamanoPagina === 0) {
      this._sociosPaginadosCache = this.sociosOrdenados;
      return this._sociosPaginadosCache;
    }
    const inicio = (this.paginaActual - 1) * this.tamanoPagina;
    this._sociosPaginadosCache = this.sociosOrdenados.slice(inicio, inicio + this.tamanoPagina);
    return this._sociosPaginadosCache;
  }

  get totalPaginas(): number {
    if (this.tamanoPagina === 0) {
      return 1;
    }
    const total = this.serverPaginated ? this.totalRegistros : this.sociosOrdenados.length;
    return Math.max(1, Math.ceil(total / this.tamanoPagina));
  }

  onMatPageChange(event: PageEvent): void {
    const sizeChanged = event.pageSize !== this.tamanoPagina;
    this.tamanoPagina = event.pageSize;
    this.paginaActual = sizeChanged ? 1 : event.pageIndex + 1;
    if (this.serverPaginated || this.hadServerPagination || this.totalRegistros > this.socios.length) {
      this.cargarRanking();
    }
  }

  cambiarPagina(pagina: number): void {
    if (pagina >= 1 && pagina <= this.totalPaginas) {
      this.paginaActual = pagina;
      if (this.serverPaginated) {
        this.cargarRanking();
      }
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
    if (this.serverPaginated || this.hadServerPagination) {
      this.cargarRanking();
    }
  }

  get textoContador(): string {
    const total = this.serverPaginated ? this.totalRegistros : this.sociosOrdenados.length;
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
