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

  describe('Tribunal de la causa (S4-04)', () => {
    const base = `${environment.apiUrl}/expedientes/12`;

    it('consulta la composición de la causa', () => {
      service.obtenerComposicionTribunal(12).subscribe(c => expect(c.asientos.length).toBe(3));
      const req = http.expectOne(`${base}/composicion/`);
      expect(req.request.method).toBe('GET');
      req.flush({ asientos: [{}, {}, {}] });
    });

    it('registra la Resolución por Asamblea con el acta en PDF', () => {
      const acta = new File(['%PDF-1.4'], 'acta.pdf', { type: 'application/pdf' });
      service.registrarResolucionAsamblea(12, acta).subscribe();
      const req = http.expectOne(`${base}/resolucion-asamblea/`);
      expect(req.request.method).toBe('POST');
      expect((req.request.body as FormData).get('acta')).toBe(acta);
      req.flush({});
    });

    it('descarga el acta de la Asamblea', () => {
      service.descargarActaAsamblea(12).subscribe(blob => expect(blob.size).toBe(3));
      const req = http.expectOne(`${base}/resolucion-asamblea/`);
      expect(req.request.method).toBe('GET');
      expect(req.request.responseType).toBe('blob');
      req.flush(new Blob(['pdf']));
    });
  });
});
