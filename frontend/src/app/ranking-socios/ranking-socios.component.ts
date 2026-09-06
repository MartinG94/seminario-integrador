import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-ranking-socios',
  templateUrl: './ranking-socios.component.html',
  styleUrls: ['./ranking-socios.component.scss']
})
export class RankingSociosComponent implements OnInit, OnDestroy {
  socios: Socio[] = [];
  criterioOrden: 'merito' | 'sancion' = 'merito';
  filtroTexto = '';

  private subs: Subscription[] = [];

  constructor(public dataService: TribunalDataService) {}

  ngOnInit(): void {
    const sub = this.dataService.socios$.subscribe(list => {
      this.socios = list;
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  get sociosOrdenados(): Socio[] {
    let list = [...this.socios];
    if (this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase();
      list = list.filter(s => 
        s.nombre.toLowerCase().includes(q) ||
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
