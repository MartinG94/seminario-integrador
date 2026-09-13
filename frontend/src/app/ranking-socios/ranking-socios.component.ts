import { Component, OnInit } from '@angular/core';
import { RankingService } from '../services/ranking.service';
import { RankingSocio } from './ranking-socio.model';

@Component({
  selector: 'app-ranking-socios',
  templateUrl: './ranking-socios.component.html',
  styleUrls: ['./ranking-socios.component.scss']
})
export class RankingSociosComponent implements OnInit {
  socios: RankingSocio[] = [];
  criterioOrden: 'merito' | 'sancion' = 'merito';
  filtroTexto = '';
  filtroCategoria: 'ACTIVO' | 'PASIVO' | '' = '';
  filtroSubcomision = '';
  subcomisiones: string[] = [];
  paginaActual = 1;
  tamanoPagina = 10;

  constructor(public rankingService: RankingService) {}

  ngOnInit(): void {
    this.socios = this.rankingService.obtenerRanking();
    this.subcomisiones = [...new Set(this.socios.map(s => s.subcomision))].sort();
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
