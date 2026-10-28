import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import {
  ReportesService,
  MetricasT01DTO,
  MetricasReunionesDTO,
  MetricasSubcomisionDTO,
  HistoricoRecordsDTO,
  SubcomisionItemDTO
} from '../services/reportes.service';

@Component({
  selector: 'app-reportes',
  templateUrl: './reportes.component.html',
  styleUrls: ['./reportes.component.scss']
})
export class ReportesComponent implements OnInit, OnDestroy {
  public Math = Math;

  tabActiva: 't01' | 'reuniones' | 'subcomision' | 'historico' = 't01';

  subcomisiones: SubcomisionItemDTO[] = [];
  filtroSubcomisionId: number | null = null;
  selectedSubcomisionId: number = 6; // Gestión Social y Ambiental por defecto

  cargando: boolean = false;
  errorMensaje: string | null = null;

  metricasT01: MetricasT01DTO | null = null;
  metricasReuniones: MetricasReunionesDTO | null = null;
  metricasSubcomision: MetricasSubcomisionDTO | null = null;
  historicoRecords: HistoricoRecordsDTO | null = null;

  private subs: Subscription[] = [];

  constructor(private reportesService: ReportesService) {}

  ngOnInit(): void {
    this.cargarSubcomisiones();
    this.cargarDatosTabActiva();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  cambiarTab(tab: 't01' | 'reuniones' | 'subcomision' | 'historico'): void {
    if (this.tabActiva === tab) return;
    this.tabActiva = tab;
    this.cargarDatosTabActiva();
  }

  cargarSubcomisiones(): void {
    const sub = this.reportesService.getSubcomisiones().subscribe({
      next: data => {
        this.subcomisiones = data;
        const gsa = data.find(s => s.nombre.toLowerCase().includes('social'));
        if (gsa) {
          this.selectedSubcomisionId = gsa.id;
        }
      },
      error: () => {
        // Fallback lista representativa
        this.subcomisiones = [
          { id: 6, nombre: 'Gestión Social y Ambiental' },
          { id: 9, nombre: 'Comisión Directiva' },
          { id: 2, nombre: 'Recursos Humanos' },
          { id: 4, nombre: 'Prensa y Difusión' },
          { id: 7, nombre: 'Organización y Eventos' },
          { id: 3, nombre: 'Relaciones Institucionales' },
          { id: 1, nombre: 'Cómputos' },
          { id: 10, nombre: 'Tribunal de Disciplina' },
          { id: 8, nombre: 'Comisión Rifaria' },
          { id: 5, nombre: 'Mantenimiento' },
          { id: 12, nombre: 'Grupo de Viaje y Permanencia' }
        ];
      }
    });
    this.subs.push(sub);
  }

  cargarDatosTabActiva(): void {
    this.cargando = true;
    this.errorMensaje = null;

    if (this.tabActiva === 't01') {
      const sub = this.reportesService.getMetricasT01(this.filtroSubcomisionId || undefined).subscribe({
        next: data => {
          this.metricasT01 = data;
          this.cargando = false;
        },
        error: err => {
          console.error('Error al cargar métricas T01:', err);
          this.cargando = false;
          this.errorMensaje = 'No se pudieron cargar los datos de Gestión por T01.';
        }
      });
      this.subs.push(sub);
    } else if (this.tabActiva === 'reuniones') {
      const sub = this.reportesService.getMetricasReuniones(this.filtroSubcomisionId || undefined).subscribe({
        next: data => {
          this.metricasReuniones = data;
          this.cargando = false;
        },
        error: err => {
          console.error('Error al cargar métricas Reuniones:', err);
          this.cargando = false;
          this.errorMensaje = 'No se pudieron cargar los datos de Gestión por Reuniones.';
        }
      });
      this.subs.push(sub);
    } else if (this.tabActiva === 'subcomision') {
      const sub = this.reportesService.getMetricasSubcomision(this.selectedSubcomisionId).subscribe({
        next: data => {
          this.metricasSubcomision = data;
          this.cargando = false;
        },
        error: err => {
          console.error('Error al cargar métricas de Subcomisión:', err);
          this.cargando = false;
          this.errorMensaje = 'No se pudieron cargar los datos de la Subcomisión.';
        }
      });
      this.subs.push(sub);
    } else if (this.tabActiva === 'historico') {
      const sub = this.reportesService.getHistoricoYRecords().subscribe({
        next: data => {
          this.historicoRecords = data;
          this.cargando = false;
        },
        error: err => {
          console.error('Error al cargar Histórico y Récords:', err);
          this.cargando = false;
          this.errorMensaje = 'No se pudieron cargar los registros históricos.';
        }
      });
      this.subs.push(sub);
    }
  }

  onFiltroSubcomisionChange(id: any): void {
    this.filtroSubcomisionId = id ? Number(id) : null;
    this.cargarDatosTabActiva();
  }

  onSubcomisionSelect(id: any): void {
    this.selectedSubcomisionId = Number(id);
    this.cargarDatosTabActiva();
  }

  limpiarFiltros(): void {
    this.filtroSubcomisionId = null;
    this.cargarDatosTabActiva();
  }

  imprimir(): void {
    window.print();
  }

  // --- Funciones de escalado para gráficos visuales SVG/HTML ---

  getMaxClasificacion(): number {
    if (!this.metricasT01?.expedientes_por_clasificacion?.length) return 50;
    return Math.max(...this.metricasT01.expedientes_por_clasificacion.map(c => c.cantidad), 10);
  }

  getMaxPuntosT01(): number {
    if (!this.metricasT01?.distribucion_puntos?.length) return 70;
    return Math.max(...this.metricasT01.distribucion_puntos.map(p => p.cantidad), 10);
  }

  getMaxCategoriasReuniones(): number {
    if (!this.metricasReuniones?.expedientes_por_categoria?.length) return 30;
    return Math.max(...this.metricasReuniones.expedientes_por_categoria.map(c => c.cantidad), 10);
  }

  getMaxSociosGrupo(): number {
    if (!this.metricasReuniones?.socios_por_grupo?.length) return 90;
    return Math.max(...this.metricasReuniones.socios_por_grupo.map(g => g.cantidad), 10);
  }

  getMaxPuntosSubcom(): number {
    if (!this.metricasSubcomision?.distribucion_puntos?.length) return 10;
    return Math.max(...this.metricasSubcomision.distribucion_puntos.map(p => p.cantidad), 5);
  }

  getMaxSerieAnual(): number {
    if (!this.historicoRecords?.serie_anual?.length) return 600;
    return Math.max(...this.historicoRecords.serie_anual.map(s => s.cantidad), 100);
  }

  getMaxPuntosHistorico(): number {
    if (!this.historicoRecords?.distribucion_historica_puntos?.length) return 600;
    return Math.max(...this.historicoRecords.distribucion_historica_puntos.map(p => p.cantidad), 100);
  }

  // Gradiente de color semafórico para tabla de socios
  getGradientePuntos(puntos: number): string {
    if (puntos >= 20) return 'rgba(40, 167, 69, 0.85)'; // Verde oscuro destacado
    if (puntos >= 10) return 'rgba(40, 167, 69, 0.65)'; // Verde medio
    if (puntos >= 4) return 'rgba(76, 175, 80, 0.45)';  // Verde claro
    if (puntos >= 2) return 'rgba(139, 195, 74, 0.35)'; // Verde tenue
    if (puntos >= 0) return 'rgba(255, 235, 59, 0.3)';  // Amarillo neutro
    return 'rgba(244, 67, 54, 0.25)';                  // Rojizo para saldo negativo
  }

  // --- Exportación a CSV compatible con Excel en UTF-8 puro con BOM ---

  exportarCSV(): void {
    let csvContent = '\uFEFF'; // BOM para que Excel respete caracteres UTF-8 (tildes, eñes)
    let nombreArchivo = `reporte_aveit_${this.tabActiva}`;

    if (this.tabActiva === 't01' && this.metricasT01) {
      csvContent += 'GESTIÓN DE EXPEDIENTES POR T01 - A.V.E.I.T.\r\n\r\n';
      csvContent += `Expedientes Generados;${this.metricasT01.kpis.expedientes_generados}\r\n`;
      csvContent += `Socios Alcanzados;${this.metricasT01.kpis.socios_alcanzados}\r\n`;
      csvContent += `Puntos Aprobados Positivos;${this.metricasT01.kpis.puntos_aprobados_positivos}\r\n`;
      csvContent += `Puntos Aprobados Negativos;${this.metricasT01.kpis.puntos_aprobados_negativos}\r\n`;
      csvContent += `Tiempo de Vida Promedio (días);${this.metricasT01.kpis.tiempo_vida_promedio_dias}\r\n\r\n`;

      csvContent += 'EXPEDIENTES POR CLASIFICACIÓN / CONCEPTO\r\n';
      csvContent += 'Clasificación;Concepto / Área;Cantidad\r\n';
      for (const item of this.metricasT01.expedientes_por_clasificacion) {
        csvContent += `${item.clasificacion};${item.label};${item.cantidad}\r\n`;
      }

      csvContent += '\r\nDISTRIBUCIÓN POR GRUPO SOCIAL\r\n';
      csvContent += 'Grupo;Porcentaje (%);Cantidad Estimada\r\n';
      for (const item of this.metricasT01.distribucion_por_grupo) {
        csvContent += `Grupo ${item.grupo};${item.porcentaje}%;${item.cantidad}\r\n`;
      }

      csvContent += '\r\nDISTRIBUCIÓN DE ASIGNACIÓN DE PUNTOS\r\n';
      csvContent += 'Puntaje;Cantidad de Expedientes\r\n';
      for (const item of this.metricasT01.distribucion_puntos) {
        csvContent += `${item.puntaje};${item.cantidad}\r\n`;
      }
    } else if (this.tabActiva === 'reuniones' && this.metricasReuniones) {
      csvContent += 'GESTIÓN DE EXPEDIENTES POR REUNIONES / INASISTENCIAS - A.V.E.I.T.\r\n\r\n';
      csvContent += `Expedientes Generados;${this.metricasReuniones.kpis.expedientes_generados}\r\n`;
      csvContent += `Socios Alcanzados;${this.metricasReuniones.kpis.socios_alcanzados}\r\n`;
      csvContent += `Puntos por Inasistencias;${this.metricasReuniones.kpis.puntos_por_inasistencias}\r\n\r\n`;

      csvContent += 'EXPEDIENTES POR CATEGORÍA DE EVENTO\r\n';
      csvContent += 'Categoría;Cantidad\r\n';
      for (const item of this.metricasReuniones.expedientes_por_categoria) {
        csvContent += `${item.categoria};${item.cantidad}\r\n`;
      }

      csvContent += '\r\nPROPORCIÓN DE APROBACIÓN\r\n';
      csvContent += 'Dictamen / Resolución;Porcentaje;Cantidad\r\n';
      for (const item of this.metricasReuniones.proporcion_aprobacion) {
        csvContent += `${item.tipo};${item.porcentaje}%;${item.cantidad}\r\n`;
      }
    } else if (this.tabActiva === 'subcomision' && this.metricasSubcomision) {
      const sub = this.metricasSubcomision.subcomision;
      csvContent += `BALANCE DE SUBCOMISIÓN: ${sub.nombre.toUpperCase()} - A.V.E.I.T.\r\n\r\n`;
      csvContent += `Puntaje Ciclo 2026 T01;${this.metricasSubcomision.kpis.puntaje_ciclo_t01}\r\n`;
      csvContent += `Total de Socios Nómina;${this.metricasSubcomision.kpis.total_socios}\r\n\r\n`;

      csvContent += 'ANÁLISIS INTRA VS INTER SUBCOMISIÓN\r\n';
      csvContent += 'Ámbito;Cantidad;Porcentaje (%)\r\n';
      for (const b of this.metricasSubcomision.intra_vs_inter) {
        csvContent += `${b.tipo};${b.cantidad};${b.porcentaje}%\r\n`;
      }

      csvContent += '\r\nNÓMINA DE SOCIOS Y PUNTOS\r\n';
      csvContent += 'Posición;Legajo;Apellido;Nombre;Grupo;Puntos Asignados 2026;Puntos Totales\r\n';
      for (const s of this.metricasSubcomision.tabla_socios) {
        csvContent += `${s.posicion};${s.legajo};${s.apellido};${s.nombre};${s.grupo};${s.puntos_asignados_ciclo};${s.puntos_totales}\r\n`;
      }
      nombreArchivo = `subcomision_${sub.nombre.toLowerCase().replace(/\\s+/g, '_')}`;
    } else if (this.tabActiva === 'historico' && this.historicoRecords) {
      const rec = this.historicoRecords.record_absoluto;
      csvContent += 'CUADRO DE HONOR Y RÉCORDS HISTÓRICOS - A.V.E.I.T.\r\n\r\n';
      csvContent += `RÉCORD HISTÓRICO ABSOLUTO:;${rec.nombre_completo} (Socio #${rec.socio_numero} - Legajo ${rec.legajo})\r\n`;
      csvContent += `Puntaje Máximo Histórico:;${rec.puntaje_maximo} pts\r\n`;
      csvContent += `Subcomisión:;${rec.subcomision}\r\n`;
      csvContent += `Período:;${rec.periodo}\r\n\r\n`;

      csvContent += 'TOP 10 HISTÓRICO GENERAL DE PUNTOS\r\n';
      csvContent += 'Posición;Nro Socio;Nombre y Apellido;Subcomisión;Puntaje Histórico\r\n';
      for (const t of this.historicoRecords.top_historico) {
        csvContent += `${t.posicion};${t.socio_numero};${t.nombre_completo};${t.subcomision};${t.puntaje_historico}\r\n`;
      }

      csvContent += '\r\nEVOLUCIÓN ANUAL DE EXPEDIENTES (2013 - 2026)\r\n';
      csvContent += 'Año;Cantidad de Expedientes\r\n';
      for (const a of this.historicoRecords.serie_anual) {
        csvContent += `${a.anio};${a.cantidad}\r\n`;
      }
    }

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `${nombreArchivo}_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
