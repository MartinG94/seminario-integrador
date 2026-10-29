import { ComponentFixture, TestBed } from '@angular/core/testing';
import { of } from 'rxjs';
import { FormsModule } from '@angular/forms';
import { ReportesComponent } from './reportes.component';
import {
  ReportesService,
  MetricasT01DTO,
  MetricasReunionesDTO,
  MetricasSubcomisionDTO,
  HistoricoRecordsDTO,
} from '../services/reportes.service';

describe('ReportesComponent (SCRUM-63)', () => {
  let component: ReportesComponent;
  let fixture: ComponentFixture<ReportesComponent>;
  let mockReportesService: jasmine.SpyObj<ReportesService>;

  const mockT01Data: MetricasT01DTO = {
    kpis: {
      expedientes_generados: 238,
      socios_alcanzados: 230,
      puntos_aprobados_positivos: 366,
      puntos_aprobados_negativos: -164,
      tiempo_vida_promedio_dias: 3.8,
    },
    expedientes_por_clasificacion: [
      { clasificacion: 'CD', label: 'Comisión Directiva', cantidad: 42 },
      { clasificacion: 'GSA', label: 'Gestión Social y Ambiental', cantidad: 23 },
    ],
    distribucion_por_grupo: [
      { grupo: '58', porcentaje: 31.1, cantidad: 74 },
      { grupo: '59', porcentaje: 26.9, cantidad: 64 },
    ],
    distribucion_puntos: [
      { puntaje: -1.0, cantidad: 14 },
      { puntaje: 0.5, cantidad: 68 },
    ],
  };

  const mockReunionesData: MetricasReunionesDTO = {
    kpis: {
      expedientes_generados: 90,
      socios_alcanzados: 263,
      puntos_por_inasistencias: -463,
    },
    expedientes_por_categoria: [
      { categoria: 'CDS', cantidad: 28 },
      { categoria: 'Reunión Subcomisión', cantidad: 27 },
    ],
    proporcion_aprobacion: [
      { tipo: 'Aprobado por TD', porcentaje: 51.2, cantidad: 46 },
    ],
    socios_por_grupo: [
      { grupo: '61', cantidad: 83 },
    ],
  };

  const mockSubcomisionData: MetricasSubcomisionDTO = {
    subcomision: {
      id: 6,
      nombre: 'Gestión Social y Ambiental',
      color_hex: '#28a745',
    },
    kpis: {
      puntaje_ciclo_t01: 64.2,
      total_socios: 8,
    },
    distribucion_puntos: [
      { puntaje: 0.5, cantidad: 4 },
    ],
    intra_vs_inter: [
      { tipo: 'Intra-Subcomisión', cantidad: 13, porcentaje: 46.0, color: '#28a745' },
      { tipo: 'Inter-Subcomisiones', cantidad: 15, porcentaje: 54.0, color: '#007bff' },
    ],
    participacion_otras_subcomisiones: [
      { subcomision: 'Gestión Social y Ambiental', porcentaje: 46.0, color: '#28a745' },
    ],
    tabla_socios: [
      {
        posicion: 1,
        legajo: '87414',
        apellido: 'Sanchez Turu Michel',
        nombre: 'Diego Gabriel',
        grupo: '58',
        puntos_asignados_ciclo: 3.5,
        puntos_totales: 25.16,
      },
    ],
  };

  const mockHistoricoData: HistoricoRecordsDTO = {
    record_absoluto: {
      socio_numero: 11779,
      nombre_completo: 'Diego Gabriel Sánchez Turu Michel',
      legajo: '87414',
      subcomision: 'Gestión Social y Ambiental',
      grupo: '58',
      puntaje_maximo: 25.0,
      periodo: 'Ciclo 2021 - 2026',
      distincion: 'Récord Histórico Absoluto',
    },
    top_historico: [
      {
        posicion: 1,
        socio_numero: 11779,
        nombre_completo: 'Diego Gabriel Sánchez Turu Michel',
        subcomision: 'Gestión Social y Ambiental',
        puntaje_historico: 25.0,
        record_destacado: true,
      },
    ],
    kpis: {
      total_expedientes_historicos: 2640,
      anios_registrados: '2013 - 2026',
    },
    serie_anual: [
      { anio: 2025, cantidad: 480 },
      { anio: 2026, cantidad: 349 },
    ],
    distribucion_historica_puntos: [
      { puntaje: -1.0, cantidad: 548 },
      { puntaje: 0.5, cantidad: 249 },
    ],
  };

  beforeEach(async () => {
    mockReportesService = jasmine.createSpyObj('ReportesService', [
      'getMetricasT01',
      'getMetricasReuniones',
      'getSubcomisiones',
      'getMetricasSubcomision',
      'getHistoricoYRecords',
    ]);

    mockReportesService.getSubcomisiones.and.returnValue(
      of([
        { id: 6, nombre: 'Gestión Social y Ambiental' },
        { id: 9, nombre: 'Comisión Directiva' },
      ])
    );
    mockReportesService.getMetricasT01.and.returnValue(of(mockT01Data));
    mockReportesService.getMetricasReuniones.and.returnValue(of(mockReunionesData));
    mockReportesService.getMetricasSubcomision.and.returnValue(of(mockSubcomisionData));
    mockReportesService.getHistoricoYRecords.and.returnValue(of(mockHistoricoData));

    await TestBed.configureTestingModule({
      declarations: [ReportesComponent],
      imports: [FormsModule],
      providers: [{ provide: ReportesService, useValue: mockReportesService }],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente el componente', () => {
    expect(component).toBeTruthy();
  });

  it('debe inicializar en la pestaña t01 y cargar sus métricas', () => {
    expect(component.tabActiva).toBe('t01');
    expect(mockReportesService.getMetricasT01).toHaveBeenCalled();
    expect(component.metricasT01?.kpis.tiempo_vida_promedio_dias).toBe(3.8);
    expect(component.metricasT01?.kpis.expedientes_generados).toBe(238);
  });

  it('debe cambiar de pestaña y cargar los datos correspondientes', () => {
    component.cambiarTab('reuniones');
    expect(component.tabActiva).toBe('reuniones');
    expect(mockReportesService.getMetricasReuniones).toHaveBeenCalled();

    component.cambiarTab('subcomision');
    expect(component.tabActiva).toBe('subcomision');
    expect(mockReportesService.getMetricasSubcomision).toHaveBeenCalled();

    component.cambiarTab('historico');
    expect(component.tabActiva).toBe('historico');
    expect(mockReportesService.getHistoricoYRecords).toHaveBeenCalled();
  });

  it('debe contener el Récord Histórico Absoluto de Diego Sánchez #11779 en 25 pts', () => {
    component.cambiarTab('historico');
    expect(component.historicoRecords?.record_absoluto.socio_numero).toBe(11779);
    expect(component.historicoRecords?.record_absoluto.puntaje_maximo).toBe(25.0);
    expect(component.historicoRecords?.record_absoluto.nombre_completo).toContain('Diego');
  });

  it('debe limpiar filtros y recargar datos al invocar limpiarFiltros', () => {
    component.filtroSubcomisionId = 6;
    component.limpiarFiltros();
    expect(component.filtroSubcomisionId).toBeNull();
  });

  it('debe invocar window.print al hacer clic en imprimir', () => {
    spyOn(window, 'print');
    component.imprimir();
    expect(window.print).toHaveBeenCalled();
  });

  it('debe exportar CSV sin arrojar excepciones', () => {
    spyOn(document, 'createElement').and.callThrough();
    expect(() => component.exportarCSV()).not.toThrow();
  });
});
