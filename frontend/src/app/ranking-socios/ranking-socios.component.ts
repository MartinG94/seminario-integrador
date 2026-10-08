import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { RankingService } from '../services/ranking.service';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';
import { RankingSocio } from './ranking-socio.model';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog/socio-legajo-dialog.component';

@Component({
  selector: 'app-ranking-socios',
  templateUrl: './ranking-socios.component.html',
  styleUrls: ['./ranking-socios.component.scss']
})
export class RankingSociosComponent implements OnInit, OnDestroy {
  socios: RankingSocio[] = [];
  criterioOrden: 'merito' | 'sancion' = 'merito';
  filtroTexto = '';
  filtroCategoria: 'ACTIVO' | 'PASIVO' | '' = '';
  filtroSubcomision = '';
  subcomisiones: string[] = [];
  paginaActual = 1;
  tamanoPagina = 10;
  cargando = false;
  error: string | null = null;
  private subs: Subscription[] = [];

  constructor(
    public rankingService: RankingService,
    public dataService: TribunalDataService,
    public dialog: MatDialog
  ) {}

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

  onRowKeyDown(event: KeyboardEvent, socio: RankingSocio): void {
    if (!event) return;

    if (event.key === 'Enter' || event.key === ' ' || event.key === 'Spacebar') {
      event.preventDefault();
      this.abrirLegajoSocio(socio);
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

    // 1. Cargar ranking desde servicio API backend
    this.rankingService.obtenerRanking().subscribe({
      next: (socios) => {
        this.socios = socios;
        this.sincronizarConStoreLocal(this.dataService.getSociosSnapshot());
        this.cargando = false;
      },
      error: () => {
        // Fallback reactivo directo a TribunalDataService si la API REST no responde
        this.sincronizarConStoreLocal(this.dataService.getSociosSnapshot(), true);
        this.cargando = false;
      }
    });

    // 2. Suscribirse reactivamente a socios$ para actualizar saldos en vivo al firmarse resoluciones
    const sub = this.dataService.socios$.subscribe(sociosStore => {
      this.sincronizarConStoreLocal(sociosStore);
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  private sincronizarConStoreLocal(sociosStore: Socio[], forzarFallback: boolean = false): void {
    if (!sociosStore || sociosStore.length === 0) return;

    if (this.socios.length === 0 || forzarFallback) {
      this.socios = sociosStore.map(s => {
        const partes = s.nombre.split(' ');
        const nombre = partes[0] || '';
        const apellido = partes.slice(1).join(' ') || '';
        return {
          id: s.id,
          legajo: s.legajo,
          nombre,
          apellido,
          categoria: (s.estado === 'CESE_ESTATUTARIO' ? 'PASIVO' : 'ACTIVO') as 'ACTIVO' | 'PASIVO',
          subcomision: s.subcomision,
          saldo: s.saldo
        };
      });
      this.error = null;
    } else {
      this.socios = this.socios.map(socioRanking => {
        const matching = sociosStore.find(s => 
          s.legajo === socioRanking.legajo || 
          s.nombre.toLowerCase() === `${socioRanking.nombre} ${socioRanking.apellido}`.trim().toLowerCase()
        );
        if (matching) {
          return {
            ...socioRanking,
            saldo: matching.saldo,
            categoria: (matching.estado === 'CESE_ESTATUTARIO' ? 'PASIVO' : socioRanking.categoria) as 'ACTIVO' | 'PASIVO'
          };
        }
        return socioRanking;
      });
    }

    this.subcomisiones = [...new Set(this.socios.map(s => s.subcomision))].sort();
  }

  onFiltroChange(texto: string): void {
    this.filtroTexto = texto;
    this.paginaActual = 1;
  }

  get sociosOrdenados(): RankingSocio[] {
    let list = [...this.socios];

    if (this.filtroCategoria) {
      list = list.filter(s => s.categoria === this.filtroCategoria);
    }

    if (this.filtroSubcomision) {
      list = list.filter(s => s.subcomision === this.filtroSubcomision);
    }
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase();
      list = list.filter(s => 
        s.nombre.toLowerCase().includes(q) ||
        s.apellido.toLowerCase().includes(q) ||
        s.legajo.toLowerCase().includes(q) ||
        s.subcomision.toLowerCase().includes(q)
      );
    }

    list.sort((a, b) => {
      const diferenciaSaldo = this.criterioOrden === 'merito'
        ? b.saldo - a.saldo
        : a.saldo - b.saldo;

      if (diferenciaSaldo !== 0) {
        return diferenciaSaldo;
      }

      const diferenciaApellido = a.apellido.localeCompare(b.apellido);
      if (diferenciaApellido !== 0) {
        return diferenciaApellido;
      }

      return a.nombre.localeCompare(b.nombre);
    });

    return list;
  }

  get sociosPaginados(): RankingSocio[] {
    const inicio = (this.paginaActual - 1) * this.tamanoPagina;
    return this.sociosOrdenados.slice(inicio, inicio + this.tamanoPagina);
  }

  get totalPaginas(): number {
    return Math.max(1, Math.ceil(this.sociosOrdenados.length / this.tamanoPagina));
  }

  cambiarPagina(pagina: number): void {
    if (pagina >= 1 && pagina <= this.totalPaginas) {
      this.paginaActual = pagina;
    }
  }

  setOrden(criterio: 'merito' | 'sancion'): void {
    this.criterioOrden = criterio;
    this.paginaActual = 1;
  }

  getBadgeClase(socio: RankingSocio): string {
    if (socio.saldo <= -10.0) return 'badge-mat-danger';
    if (socio.saldo <= -7.0) return 'badge-mat-warning';
    return 'badge-mat-success';
  }

  getEstadoDescripcion(socio: RankingSocio): string {
    if (socio.saldo <= -10.0) return 'Límite Crítico: Cese Estatutario';
    if (socio.saldo <= -7.0) return 'Alerta Preventiva';
    return 'Habilitado Regular';
  }
}
