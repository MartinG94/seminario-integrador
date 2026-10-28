import { Component, OnInit, OnDestroy } from '@angular/core';
import { Subscription } from 'rxjs';
import {
  ExpedienteApiService,
  FiltrosReporteDTO,
  ReporteResumenResponseDTO,
  KpisResumenDTO,
  PedidoSubcomisionReporteDTO,
  AgrupacionConceptoReporteDTO,
  PedidoAutoridadReporteDTO,
  BalanceSubcomisionYCategoriasDTO
} from '../services/expediente-api.service';
import { NotificationService } from '../services/notification.service';

export type TabReporte = 'subcomisiones' | 'autoridades' | 'balance';

@Component({
  selector: 'app-reportes',
  templateUrl: './reportes.component.html',
  styleUrls: ['./reportes.component.scss']
})
export class ReportesComponent implements OnInit, OnDestroy {
  tabActiva: TabReporte = 'subcomisiones';
  cargando = false;
  errorCarga: string | null = null;
  exportando = false;

  // Filtros interactivos
  anioSeleccionado: number | null = 2026;
  aniosDisponibles: number[] = [2026, 2025, 2024, 2023];
  cuatrimestreSeleccionado = 'anual';
  fechaDesde = '';
  fechaHasta = '';
  subcomisionSeleccionada: number | null = null;
  conceptoSeleccionado = '';

  // Contenido de datos
  reporte: ReporteResumenResponseDTO | null = null;
  catalogoConceptos: Array<{ codigo: string; nombre: string }> = [];
  catalogoSubcomisiones: Array<{ id: number; nombre: string }> = [];

  private subs: Subscription[] = [];

  constructor(
    private apiService: ExpedienteApiService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.cargarReporte();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  get kpis(): KpisResumenDTO | null {
    return this.reporte ? this.reporte.kpis_resumen : null;
  }

  get pedidosSubcomision(): PedidoSubcomisionReporteDTO[] {
    return this.reporte ? this.reporte.pedidos_por_subcomision : [];
  }

  get agrupacionConceptos(): AgrupacionConceptoReporteDTO[] {
    return this.reporte ? this.reporte.agrupacion_por_concepto : [];
  }

  get pedidosAutoridad(): PedidoAutoridadReporteDTO[] {
    return this.reporte ? this.reporte.pedidos_por_autoridad : [];
  }

  get balanceSubcomisiones(): BalanceSubcomisionYCategoriasDTO[] {
    return this.reporte ? this.reporte.balance_subcomisiones_y_categorias : [];
  }

  get tieneDatos(): boolean {
    if (!this.reporte || !this.reporte.kpis_resumen) {
      return false;
    }
    return (
      this.reporte.kpis_resumen.total_expedientes > 0 ||
      this.pedidosSubcomision.length > 0 ||
      this.pedidosAutoridad.length > 0 ||
      this.balanceSubcomisiones.length > 0
    );
  }

  seleccionarTab(tab: TabReporte): void {
    this.tabActiva = tab;
  }

  onFiltroChange(): void {
    this.cargarReporte();
  }

  limpiarFiltros(): void {
    this.anioSeleccionado = 2026;
    this.cuatrimestreSeleccionado = 'anual';
    this.fechaDesde = '';
    this.fechaHasta = '';
    this.subcomisionSeleccionada = null;
    this.conceptoSeleccionado = '';
    this.cargarReporte();
    this.notificationService.info('Filtros restablecidos a valores por defecto.');
  }

  construirPayloadFiltros(): FiltrosReporteDTO {
    const filtros: FiltrosReporteDTO = {};
    if (this.anioSeleccionado != null) {
      filtros.anio = Number(this.anioSeleccionado);
    }
    if (this.cuatrimestreSeleccionado && this.cuatrimestreSeleccionado !== 'personalizado') {
      filtros.cuatrimestre = this.cuatrimestreSeleccionado;
    }
    if (this.cuatrimestreSeleccionado === 'personalizado') {
      if (this.fechaDesde) {
        filtros.fecha_desde = this.fechaDesde;
      }
      if (this.fechaHasta) {
        filtros.fecha_hasta = this.fechaHasta;
      }
    }
    if (this.subcomisionSeleccionada != null && (this.subcomisionSeleccionada as any) !== '') {
      filtros.subcomision_id = Number(this.subcomisionSeleccionada);
    }
    if (this.conceptoSeleccionado) {
      filtros.concepto = this.conceptoSeleccionado;
    }
    return filtros;
  }

  cargarReporte(): void {
    this.cargando = true;
    this.errorCarga = null;

    const filtros = this.construirPayloadFiltros();
    const sub = this.apiService.obtenerResumenReportes(filtros).subscribe({
      next: data => {
        this.reporte = data;
        if (data.catalogo_conceptos && data.catalogo_conceptos.length > 0) {
          this.catalogoConceptos = data.catalogo_conceptos;
        }
        if (data.catalogo_subcomisiones && data.catalogo_subcomisiones.length > 0) {
          this.catalogoSubcomisiones = data.catalogo_subcomisiones;
        }
        this.cargando = false;
      },
      error: () => {
        this.errorCarga = 'No fue posible cargar el resumen analítico institucional.';
        this.cargando = false;
        this.notificationService.error('Error al obtener los datos del reporte. Verifique la conexión.');
      }
    });
    this.subs.push(sub);
  }

  exportarCSV(seccion?: string): void {
    const sec = seccion || this.tabActiva;
    this.exportando = true;
    const filtros = this.construirPayloadFiltros();

    const sub = this.apiService.descargarReporteCsv(filtros, sec).subscribe({
      next: blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const timestamp = new Date().toISOString().slice(0, 10);
        a.download = `reporte_${sec}_${timestamp}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);

        this.exportando = false;
        this.notificationService.success(`Reporte CSV de ${sec} descargado exitosamente.`);
      },
      error: () => {
        this.exportando = false;
        this.notificationService.error('Error al generar la exportación en CSV.');
      }
    });
    this.subs.push(sub);
  }

  imprimirPDF(): void {
    window.print();
  }

  obtenerResumenConceptos(desglose: Record<string, number>): string {
    if (!desglose || Object.keys(desglose).length === 0) {
      return '—';
    }
    return Object.entries(desglose)
      .map(([k, v]) => `${k} (${v})`)
      .join(', ');
  }
}
