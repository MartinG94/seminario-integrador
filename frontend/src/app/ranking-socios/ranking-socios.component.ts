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

  constructor(public rankingService: RankingService) {}

  ngOnInit(): void {
    this.socios = this.rankingService.obtenerRanking();
  }

  get sociosOrdenados(): RankingSocio[] {
    let list = [...this.socios];
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase();
      list = list.filter(s => 
        s.nombre.toLowerCase().includes(q) ||
        s.apellido.toLowerCase().includes(q) ||
        s.legajo.toLowerCase().includes(q) ||
        s.subcomision.toLowerCase().includes(q)
      );
    }

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
