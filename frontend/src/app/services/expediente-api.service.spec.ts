import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { DescargoVersionDto, ExpedienteApiService } from './expediente-api.service';

describe('ExpedienteApiService', () => {
  let service: ExpedienteApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(ExpedienteApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('usa el endpoint de expedientes para crear, actualizar, emitir y obtener', () => {
    const payload = { tipo_accion: 'SANCTION' as const, puntos: -1, motivo: 'Motivo' };
    service.crearBorrador(payload).subscribe();
    http.expectOne({ method: 'POST', url: `${environment.apiUrl}/expedientes/` }).flush({});
    service.actualizarBorrador('abc', payload).subscribe();
    http.expectOne({ method: 'PATCH', url: `${environment.apiUrl}/expedientes/abc/` }).flush({});
    service.emitir('abc').subscribe();
    http.expectOne({ method: 'POST', url: `${environment.apiUrl}/expedientes/abc/emitir/` }).flush({});
    service.obtener('abc').subscribe();
    http.expectOne({ method: 'GET', url: `${environment.apiUrl}/expedientes/abc/` }).flush({});
  });

  it('lista los reglamentos respaldantes disponibles', () => {
    service.listarReglamentos().subscribe(res => {
      expect(res.reglamentos).toEqual(['Reglamento General']);
    });
    const req = http.expectOne({ method: 'GET', url: `${environment.apiUrl}/expedientes/reglamentos/` });
    req.flush({ reglamentos: ['Reglamento General'] });
  });

  it('lista mis solicitudes sin parámetros adicionales', () => {
    service.listarMisSolicitudes().subscribe(solicitudes => {
      expect(solicitudes.length).toBe(1);
      expect(solicitudes[0].numero).toBe('T01-001');
    });

    const req = http.expectOne(r => r.url === `${environment.apiUrl}/expedientes/mis-solicitudes/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush([{ id: 'uuid-1', numero: 'T01-001', estado: 'DRAFT', titulo: 'Test' }]);
  });

  it('lista mis solicitudes enviando search y estado como query params', () => {
    service.listarMisSolicitudes({ search: 'inconducta', estado: 'DRAFT' }).subscribe(solicitudes => {
      expect(solicitudes.length).toBe(1);
      expect(solicitudes[0].titulo).toBe('Inconducta');
    });

    const req = http.expectOne(
      r => r.url === `${environment.apiUrl}/expedientes/mis-solicitudes/` &&
           r.params.get('search') === 'inconducta' &&
           r.params.get('estado') === 'DRAFT'
    );
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 'uuid-2', numero: 'T01-002', estado: 'DRAFT', titulo: 'Inconducta' }]);
  });

  it('normaliza los puntos decimales del monitoreo para retomar borradores sin perder la selección', () => {
    service.listarMisSolicitudes().subscribe(solicitudes => {
      expect(solicitudes.map(solicitud => solicitud.puntos)).toEqual([-0.5, 2, 2, null]);
      expect(solicitudes[0].urgencia).toBe('urgente');
    });
    http.expectOne(`${environment.apiUrl}/expedientes/mis-solicitudes/`).flush([
      { id: 'draft-1', puntos: '-0.50', urgencia: 'urgente' },
      { id: 'draft-2', puntos: '2.00' },
      { id: 'draft-3', puntos: 2 },
      { id: 'draft-4', puntos: null }
    ]);
  });

  it('consulta las causas de un socio filtrando por legajo', () => {
    service.listarPorLegajo('74907').subscribe(expedientes => {
      expect(expedientes.length).toBe(1);
      expect(expedientes[0].numero).toBe('EXP-0001/2026');
    });

    const req = http.expectOne(
      r =>
        r.url === `${environment.apiUrl}/expedientes/gestion/` &&
        r.params.get('legajo') === '74907'
    );

    expect(req.request.method).toBe('GET');

    req.flush([
      {
        id: 1,
        numero: 'EXP-0001/2026',
        motivo: 'Motivo de prueba',
        puntos: '-2.00',
        estado: 'creado',
        urgencia: 'normal',
        urgencia_display: 'Normal',
        created_at: '2026-10-11T08:00:00Z'
      }
    ]);
  });

  it('elimina un borrador existente mediante DELETE', () => {
    let completed = false;
    service.eliminarBorrador('draft-123').subscribe(() => {
      completed = true;
    });

    const req = http.expectOne({ method: 'DELETE', url: `${environment.apiUrl}/expedientes/draft-123/` });
    req.flush(null);
    expect(completed).toBeTrue();
  });
  it('registra la decisión sobre una causal T02 con su fundamento', () => {
    service.registrarDecisionCausal(12, 5, { decision: 'REJECTED', fundamento: 'El certificado no acredita la fecha.' })
      .subscribe(decision => {
        expect(decision.version).toBe(2);
      });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/12/descargos/5/decisiones/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ decision: 'REJECTED', fundamento: 'El certificado no acredita la fecha.' });
    req.flush({ id: 9, descargo: 5, version: 2, decision: 'REJECTED' });
  });

  it('lista el historial de decisiones de una causal', () => {
    service.listarDecisionesCausal(12, 5).subscribe(decisiones => {
      expect(decisiones.map(d => d.version)).toEqual([2, 1]);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/12/descargos/5/decisiones/`);
    expect(req.request.method).toBe('GET');
    req.flush([{ version: 2 }, { version: 1 }]);
  });

  it('obtiene el detalle del expediente con sus descargos', () => {
    service.obtenerDetalleExpediente(12).subscribe(detalle => {
      expect(detalle.descargos.length).toBe(1);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/12/`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 12, numero: 'EXP-0012/2026', estado: 'revision_resolucion', descargos: [{ id: 5 }] });
    });

  it('consulta el historial inmutable de versiones del descargo de un expediente', () => {
    let versiones: DescargoVersionDto[] = [];
    service.obtenerVersionesDescargo(42).subscribe(v => (versiones = v));

    const req = http.expectOne({ method: 'GET', url: `${environment.apiUrl}/expedientes/42/descargo/versiones/` });
    req.flush([{ id: 1, numero: 1, operacion: 'PRESENTADO' }]);
    expect(versiones.length).toBe(1);
    expect(versiones[0].numero).toBe(1);
  });

  describe('apelación y adecuación del T01 (PB-02)', () => {
    const base = `${environment.apiUrl}/expedientes`;

    it('consulta el historial del T01', () => {
      service.obtenerHistorialT01(7).subscribe(h => expect(h.es_t01).toBeTrue());
      const req = http.expectOne(`${base}/7/t01/historial/`);
      expect(req.request.method).toBe('GET');
      req.flush({ es_t01: true });
    });

    it('presenta la apelación del socio', () => {
      service.apelarT01(7, 'No estuve presente en el lugar del hecho.').subscribe();
      const req = http.expectOne(`${base}/7/apelacion/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual({ texto: 'No estuve presente en el lugar del hecho.' });
      req.flush({});
    });

    it('registra la adecuación del TD', () => {
      const payload = { puntos: -1.5, socios: [3, 4], motivos: 'Motivos del debate del Tribunal.', reabrir_plazo: true };
      service.adecuarT01(7, payload).subscribe();
      const req = http.expectOne(`${base}/7/adecuaciones/`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(payload);
      req.flush({});
    });

    it('consulta y actualiza el plazo de apelación', () => {
      service.obtenerPlazoApelacion().subscribe(p => expect(p.dias_habiles).toBe(5));
      http.expectOne(`${base}/parametros/plazo-apelacion/`).flush({ dias_habiles: 5 });

      service.actualizarPlazoApelacion(7).subscribe(p => expect(p.dias_habiles).toBe(7));
      const req = http.expectOne(`${base}/parametros/plazo-apelacion/`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual({ dias_habiles: 7 });
      req.flush({ dias_habiles: 7 });
    });
  });

  it('actualiza el concepto del expediente mediante PATCH', () => {
    service.actualizarConceptoExpediente(123, 'GSA').subscribe(res => {
      expect(res.concepto).toBe('GSA');
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/123/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ concepto: 'GSA' });
    req.flush({ id: 123, concepto: 'GSA', concepto_display: 'GSA — Gestión Social y Ambiental' });
  });

  describe('reportes e informes analíticos (SCRUM-63)', () => {
    const reportesBaseUrl = `${environment.apiUrl}/expedientes/reportes/resumen/`;
    const exportarBaseUrl = `${environment.apiUrl}/expedientes/reportes/exportar-csv/`;

    it('obtiene el resumen de reportes sin filtros', () => {
      service.obtenerResumenReportes().subscribe(res => {
        expect(res.kpis_resumen.total_expedientes).toBe(10);
        expect(res.kpis_resumen.tiempo_vida_promedio_dias).toBe(4.5);
      });

      const req = http.expectOne(r => r.url === reportesBaseUrl);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.keys().length).toBe(0);
      req.flush({
        filtros_aplicados: { anio: null, cuatrimestre: null, fecha_desde: null, fecha_hasta: null, subcomision_id: null, concepto: null },
        kpis_resumen: {
          tiempo_vida_promedio_dias: 4.5,
          total_emitidos_evaluados: 6,
          total_expedientes: 10,
          en_tramite: 4,
          emitidos: 6,
          sanciones: 7,
          meritos: 3,
          sin_clasificar_concepto: 1,
          backlog_urgencia: { total_abiertos: 4, baja: 1, normal: 2, urgente: 1, por_estado: {} },
          descargos_resumen: { total_imputaciones: 10, total_descargos: 8, descargos_t02: 5, descargos_t03: 3, tasa_presentacion_pct: 80, decisiones_t02_total: 5, decisiones_t02_aceptadas: 4, decisiones_t02_rechazadas: 1, tasa_aceptacion_t02_pct: 80, apelaciones_t01: 1, adecuaciones_t01: 1 },
          puntos_y_riesgo: { puntos_positivos: 15, puntos_negativos: -20, saldo_neto: -5, llamados_atencion_total: 2, felicitaciones_total: 4, socios_alerta_preventiva: 3, socios_riesgo_estatutario: 1 },
          eventos_resumen: { total_eventos: 5, eventos_finalizados: 4, total_convocatorias: 40, total_presentes: 35, tasa_asistencia_pct: 87.5, eventos_no_sancionables: 1, pct_no_sancionables: 20 }
        },
        pedidos_por_subcomision: [],
        agrupacion_por_concepto: [],
        pedidos_por_autoridad: [],
        balance_subcomisiones_y_categorias: [],
        catalogo_conceptos: [],
        catalogo_subcomisiones: []
      });
    });

    it('obtiene el resumen de reportes aplicando todos los filtros', () => {
      service.obtenerResumenReportes({
        anio: 2026,
        cuatrimestre: '1',
        fecha_desde: '2026-03-01',
        fecha_hasta: '2026-06-30',
        subcomision_id: 2,
        concepto: 'GSA'
      }).subscribe(res => {
        expect(res.filtros_aplicados.anio).toBe(2026);
      });

      const req = http.expectOne(r =>
        r.url === reportesBaseUrl &&
        r.params.get('anio') === '2026' &&
        r.params.get('cuatrimestre') === '1' &&
        r.params.get('fecha_desde') === '2026-03-01' &&
        r.params.get('fecha_hasta') === '2026-06-30' &&
        r.params.get('subcomision_id') === '2' &&
        r.params.get('concepto') === 'GSA'
      );
      expect(req.request.method).toBe('GET');
      req.flush({ filtros_aplicados: { anio: 2026 } });
    });

    it('descarga el reporte en formato CSV como Blob', () => {
      const mockBlob = new Blob(['Subcomision,Total\nGSA,5'], { type: 'text/csv' });
      service.descargarReporteCsv({ anio: 2026 }, 'autoridades').subscribe(blob => {
        expect(blob.size).toBeGreaterThan(0);
      });

      const req = http.expectOne(r =>
        r.url === exportarBaseUrl &&
        r.params.get('seccion') === 'autoridades' &&
        r.params.get('anio') === '2026'
      );
      expect(req.request.method).toBe('GET');
      expect(req.request.responseType).toBe('blob');
      req.flush(mockBlob);
    });
  });
});

