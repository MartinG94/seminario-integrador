import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';
import { ReportesComponent } from './reportes.component';
import {
  ExpedienteApiService,
  ReporteResumenResponseDTO
} from '../services/expediente-api.service';
import { NotificationService } from '../services/notification.service';

describe('ReportesComponent', () => {
  let component: ReportesComponent;
  let fixture: ComponentFixture<ReportesComponent>;
  let apiServiceSpy: jasmine.SpyObj<ExpedienteApiService>;
  let notificationServiceSpy: jasmine.SpyObj<NotificationService>;

  const mockReporte: ReporteResumenResponseDTO = {
    filtros_aplicados: {
      anio: 2026,
      cuatrimestre: 'anual',
      fecha_desde: null,
      fecha_hasta: null,
      subcomision_id: null,
      concepto: null
    },
    kpis_resumen: {
      tiempo_vida_promedio_dias: 4.5,
      total_emitidos_evaluados: 12,
      total_expedientes: 18,
      en_tramite: 6,
      emitidos: 12,
      sanciones: 10,
      meritos: 8,
      sin_clasificar_concepto: 2,
      backlog_urgencia: {
        total_abiertos: 6,
        baja: 1,
        normal: 3,
        urgente: 2,
        por_estado: { creado: 2, justificando: 4 }
      },
      descargos_resumen: {
        total_imputaciones: 20,
        total_descargos: 16,
        descargos_t02: 10,
        descargos_t03: 6,
        tasa_presentacion_pct: 80.0,
        decisiones_t02_total: 10,
        decisiones_t02_aceptadas: 8,
        decisiones_t02_rechazadas: 2,
        tasa_aceptacion_t02_pct: 80.0,
        apelaciones_t01: 3,
        adecuaciones_t01: 2
      },
      puntos_y_riesgo: {
        puntos_positivos: 25.0,
        puntos_negativos: -15.0,
        saldo_neto: 10.0,
        llamados_atencion_total: 4,
        felicitaciones_total: 6,
        socios_alerta_preventiva: 2,
        socios_riesgo_estatutario: 1
      },
      eventos_resumen: {
        total_eventos: 8,
        eventos_finalizados: 7,
        total_convocatorias: 70,
        total_presentes: 63,
        tasa_asistencia_pct: 90.0,
        eventos_no_sancionables: 1,
        pct_no_sancionables: 12.5
      }
    },
    pedidos_por_subcomision: [
      {
        subcomision_id: 1,
        subcomision_nombre: 'Gestión Social y Ambiental',
        total_expedientes: 5,
        expedientes_intra: 3,
        expedientes_inter: 2,
        imputaciones_intra: 4,
        imputaciones_inter: 3,
        desglose_por_concepto: { GSA: 4, EVENTOS: 1 }
      }
    ],
    agrupacion_por_concepto: [
      {
        concepto: 'GSA',
        nombre: 'Gestión Social y Ambiental',
        total: 4,
        sanciones: 3,
        meritos: 1,
        en_tramite: 1,
        emitidos: 3
      },
      {
        concepto: 'SIN_CLASIFICAR',
        nombre: 'Sin clasificar por el TD',
        total: 2,
        sanciones: 1,
        meritos: 1,
        en_tramite: 2,
        emitidos: 0
      }
    ],
    pedidos_por_autoridad: [
      {
        socio_id: 10,
        nombre_completo: 'Perez, Juan',
        legajo: '70123',
        subcomision: 'Gestión Social y Ambiental',
        rol_display: 'Secretario',
        total_pedidos: 4,
        sanciones: 3,
        meritos: 1,
        en_tramite: 1,
        emitidos: 3,
        tasa_emision_pct: 75.0
      }
    ],
    balance_subcomisiones_y_categorias: [
      {
        subcomision_id: 1,
        subcomision_nombre: 'Gestión Social y Ambiental',
        total_socios: 25,
        puntos_positivos: 15.0,
        puntos_negativos: -5.0,
        saldo_neto: 10.0,
        socios_alerta_preventiva: 1,
        socios_riesgo_estatutario: 0,
        desglose_categorias: {
          pasivo: { total_socios: 15, saldo_neto: 4.0, alerta_preventiva: 1, riesgo_estatutario: 0 },
          activo: { total_socios: 10, saldo_neto: 6.0, alerta_preventiva: 0, riesgo_estatutario: 0 }
        }
      }
    ],
    catalogo_conceptos: [
      { codigo: 'GSA', nombre: 'GSA — Gestión Social y Ambiental' },
      { codigo: 'TD', nombre: 'TD — Tribunal de Disciplina' }
    ],
    catalogo_subcomisiones: [
      { id: 1, nombre: 'Gestión Social y Ambiental' },
      { id: 2, nombre: 'Relaciones Institucionales' }
    ]
  };

  beforeEach(async () => {
    apiServiceSpy = jasmine.createSpyObj('ExpedienteApiService', [
      'obtenerResumenReportes',
      'descargarReporteCsv'
    ]);
    notificationServiceSpy = jasmine.createSpyObj('NotificationService', [
      'success',
      'error',
      'warning',
      'info'
    ]);

    apiServiceSpy.obtenerResumenReportes.and.returnValue(of(mockReporte));

    await TestBed.configureTestingModule({
      declarations: [ReportesComponent],
      imports: [FormsModule],
      providers: [
        { provide: ExpedienteApiService, useValue: apiServiceSpy },
        { provide: NotificationService, useValue: notificationServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ReportesComponent);
    component = fixture.componentInstance;
  });

  it('debe crearse e invocar la carga inicial de reportes', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(apiServiceSpy.obtenerResumenReportes).toHaveBeenCalled();
    expect(component.reporte).toEqual(mockReporte);
    expect(component.catalogoConceptos.length).toBe(2);
    expect(component.catalogoSubcomisiones.length).toBe(2);
  });

  it('renderiza las 5 tarjetas de KPI con formato tabular-nums', () => {
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const tabularElements = compiled.querySelectorAll('.tabular-nums');
    expect(tabularElements.length).toBeGreaterThanOrEqual(5);

    const textContent = compiled.textContent || '';
    expect(textContent).toContain('4.5');
    expect(textContent).toContain('6');
    expect(textContent).toContain('80%');
    expect(textContent).toContain('90%');
  });

  it('permite alternar entre las 3 pestañas estructuradas (role="tablist")', () => {
    fixture.detectChanges();
    expect(component.tabActiva).toBe('subcomisiones');

    component.seleccionarTab('autoridades');
    fixture.detectChanges();
    expect(component.tabActiva).toBe('autoridades');
    let compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#tab-autoridades')).toBeTruthy();
    expect(compiled.textContent).toContain('Perez, Juan');

    component.seleccionarTab('balance');
    fixture.detectChanges();
    expect(component.tabActiva).toBe('balance');
    compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#tab-balance')).toBeTruthy();
    expect(compiled.textContent).toContain('Eficacia de Descargos y Garantías');
  });

  it('actualiza los filtros reactivamente al modificar valores', () => {
    fixture.detectChanges();
    apiServiceSpy.obtenerResumenReportes.calls.reset();

    component.anioSeleccionado = 2025;
    component.cuatrimestreSeleccionado = '1';
    component.subcomisionSeleccionada = 1;
    component.conceptoSeleccionado = 'GSA';
    component.onFiltroChange();

    expect(apiServiceSpy.obtenerResumenReportes).toHaveBeenCalledWith({
      anio: 2025,
      cuatrimestre: '1',
      subcomision_id: 1,
      concepto: 'GSA'
    });
  });

  it('admite rango personalizado de fechas al seleccionar cuatrimestre personalizado', () => {
    fixture.detectChanges();
    apiServiceSpy.obtenerResumenReportes.calls.reset();

    component.cuatrimestreSeleccionado = 'personalizado';
    component.fechaDesde = '2026-03-01';
    component.fechaHasta = '2026-06-30';
    component.onFiltroChange();

    expect(apiServiceSpy.obtenerResumenReportes).toHaveBeenCalledWith({
      anio: 2026,
      fecha_desde: '2026-03-01',
      fecha_hasta: '2026-06-30'
    });
  });

  it('restablece los filtros a sus valores predeterminados y notifica', () => {
    fixture.detectChanges();
    component.anioSeleccionado = 2024;
    component.cuatrimestreSeleccionado = '2';
    component.conceptoSeleccionado = 'TD';

    component.limpiarFiltros();

    expect(component.anioSeleccionado).toBe(2026);
    expect(component.cuatrimestreSeleccionado).toBe('anual');
    expect(component.conceptoSeleccionado).toBe('');
    expect(notificationServiceSpy.info).toHaveBeenCalledWith(
      'Filtros restablecidos a valores por defecto.'
    );
  });

  it('exporta el CSV de la sección indicada y muestra notificación de éxito', fakeAsync(() => {
    const mockBlob = new Blob(['Subcomision,Total\nGSA,5'], { type: 'text/csv' });
    apiServiceSpy.descargarReporteCsv.and.returnValue(of(mockBlob));
    spyOn(window.URL, 'createObjectURL').and.returnValue('blob:mock-url');
    spyOn(window.URL, 'revokeObjectURL');

    component.exportarCSV('autoridades');
    tick();

    expect(apiServiceSpy.descargarReporteCsv).toHaveBeenCalledWith(
      jasmine.any(Object),
      'autoridades'
    );
    expect(notificationServiceSpy.success).toHaveBeenCalledWith(
      'Reporte CSV de autoridades descargado exitosamente.'
    );
  }));

  it('notifica error cuando la descarga CSV falla', fakeAsync(() => {
    apiServiceSpy.descargarReporteCsv.and.returnValue(
      throwError(() => new Error('Error de red'))
    );

    component.exportarCSV('subcomisiones');
    tick();

    expect(component.exportando).toBeFalse();
    expect(notificationServiceSpy.error).toHaveBeenCalledWith(
      'Error al generar la exportación en CSV.'
    );
  }));

  it('maneja el error de carga inicial y permite reintentar', () => {
    apiServiceSpy.obtenerResumenReportes.and.returnValue(
      throwError(() => new Error('Error al conectar'))
    );

    component.cargarReporte();
    fixture.detectChanges();

    expect(component.cargando).toBeFalse();
    expect(component.errorCarga).toBeTruthy();
    expect(notificationServiceSpy.error).toHaveBeenCalled();

    // Reintentar con éxito
    apiServiceSpy.obtenerResumenReportes.and.returnValue(of(mockReporte));
    component.cargarReporte();
    fixture.detectChanges();

    expect(component.errorCarga).toBeNull();
    expect(component.reporte).toEqual(mockReporte);
  });

  it('muestra estado vacío si no hay datos que coincidan', () => {
    const reporteSinDatos: ReporteResumenResponseDTO = {
      ...mockReporte,
      kpis_resumen: {
        ...mockReporte.kpis_resumen,
        total_expedientes: 0
      },
      pedidos_por_subcomision: [],
      pedidos_por_autoridad: [],
      balance_subcomisiones_y_categorias: []
    };
    apiServiceSpy.obtenerResumenReportes.and.returnValue(of(reporteSinDatos));

    component.cargarReporte();
    fixture.detectChanges();

    expect(component.tieneDatos).toBeFalse();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-card')).toBeTruthy();
    expect(compiled.textContent).toContain('No se encontraron datos');
  });

  it('formatea el resumen de conceptos auxiliares correctamente', () => {
    expect(component.obtenerResumenConceptos({ GSA: 3, TD: 1 })).toBe('GSA (3), TD (1)');
    expect(component.obtenerResumenConceptos({})).toBe('—');
  });

  it('dispara la acción de impresión / PDF', () => {
    spyOn(window, 'print');
    component.imprimirPDF();
    expect(window.print).toHaveBeenCalled();
  });
});
