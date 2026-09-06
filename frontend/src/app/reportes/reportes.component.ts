import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Expediente, SubcomisionReporte } from '../services/tribunal-data.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-reportes',
  templateUrl: './reportes.component.html',
  styleUrls: ['./reportes.component.scss']
})
export class ReportesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  reporteSubcomisiones: SubcomisionReporte[] = [];

  totalExpedientes = 0;
  enTramite = 0;
  reconocimientos = 0;
  sanciones = 0;

  // Comparativa Juniors vs Seniors
  cumplimientoJuniors = 84;
  cumplimientoSeniors = 96;

  private subs: Subscription[] = [];

  constructor(public dataService: TribunalDataService) {}

  ngOnInit(): void {
    const sub = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
      this.totalExpedientes = list.length;
      this.enTramite = list.filter(e => e.estado !== 'emitido').length;
      this.reconocimientos = list.filter(e => e.tipo === 'merito').length;
      this.sanciones = list.filter(e => e.tipo === 'falta').length;
      this.reporteSubcomisiones = this.dataService.obtenerBalancePorSubcomision();
    });
    this.subs.push(sub);
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  descargarExcel(): void {
    const datosExportar = this.reporteSubcomisiones.map(r => ({
      Subcomision: r.nombre,
      Total_Expedientes: r.totalExpedientes,
      Sanciones: r.sanciones,
      Reconocimientos: r.reconocimientos,
      Saldo_Neto_Puntos: r.saldoNeto,
      Indice_Cumplimiento_Porc: `${r.cumplimiento}%`
    }));
    this.dataService.exportarCSV('balance_cuatrimestral_aveit_2026', datosExportar);
  }

  imprimirPDF(): void {
    window.print();
  }
}
