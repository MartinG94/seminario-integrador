import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Subject, Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { SocioApiService, SocioListItemDTO } from '../services/socio-api.service';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog/socio-legajo-dialog.component';

@Component({
  selector: 'app-ranking-socios',
  templateUrl: './ranking-socios.component.html',
  styleUrls: ['./ranking-socios.component.scss']
})
export class RankingSociosComponent implements OnInit, OnDestroy {
  socios: Socio[] = [];
  criterioOrden: 'merito' | 'sancion' = 'merito';
  filtroTexto = '';

  private searchSubject = new Subject<string>();
  private rankingMock: Map<string, Socio> = new Map();
  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private socioApiService: SocioApiService,
    private dialog: MatDialog
  ) {}

  abrirLegajoSocio(socio: Socio): void {
    if (!socio) return;
    this.dialog.open(SocioLegajoDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: {
        socioId: socio.id,
        nombreSocio: socio.nombre,
        saldo: socio.saldo
      }
    });
  }

  onRowKeyDown(event: KeyboardEvent, socio: Socio): void {
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
    const subTribunal = this.dataService.socios$.subscribe(mockList => {
      this.rankingMock = new Map((mockList || []).map(s => [s.legajo, s]));
    });
    this.subs.push(subTribunal);

    const searchSub = this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(query => this.socioApiService.searchSocios(query))
    ).subscribe({
      next: (res) => {
        this.mapearResultados(res.results);
      },
      error: (err) => {
        console.error('Error al consultar el padrón:', err);
      }
    });
    this.subs.push(searchSub);

    this.buscar(this.filtroTexto);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  onFiltroChange(texto: string): void {
    this.filtroTexto = texto;
    this.searchSubject.next(texto);
  }

  buscar(query?: string): void {
    const q = query !== undefined ? query : this.filtroTexto;
    this.socioApiService.searchSocios(q).subscribe({
      next: (res) => this.mapearResultados(res.results),
      error: (err) => console.error('Error al consultar el padrón:', err)
    });
  }

  private mapearResultados(items: SocioListItemDTO[]): void {
    this.socios = (items || []).map(item => {
      const match = this.rankingMock.get(item.legajo);
      return {
        id: item.id.toString(),
        nombre: `${item.first_name} ${item.last_name}`.trim(),
        legajo: item.legajo,
        email: item.email,
        subcomision: item.subcomision || 'Sin Asignar',
        saldo: match ? match.saldo : 0,
        estado: match ? match.estado : 'HABILITADO',
        felicitaciones: match ? match.felicitaciones : 0,
        sanciones: match ? match.sanciones : 0
      };
    });
  }

  get sociosOrdenados(): Socio[] {
    const list = [...this.socios];
    if (this.criterioOrden === 'merito') {
      list.sort((a, b) => b.saldo - a.saldo);
    } else {
      list.sort((a, b) => a.saldo - b.saldo);
    }
    return list;
  }

  setOrden(criterio: 'merito' | 'sancion'): void {
    this.criterioOrden = criterio;
  }

  getBadgeClase(socio: Socio): string {
    if (socio.saldo <= -10.0) return 'badge-mat-danger';
    if (socio.saldo <= -7.0) return 'badge-mat-warning';
    return 'badge-mat-success';
  }

  getEstadoDescripcion(socio: Socio): string {
    if (socio.saldo <= -10.0) return 'Límite Crítico: Cese Estatutario';
    if (socio.saldo <= -7.0) return 'Alerta Preventiva';
    return 'Habilitado Regular';
  }
}
