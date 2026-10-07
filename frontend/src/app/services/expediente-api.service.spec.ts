import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { ExpedienteApiService } from './expediente-api.service';

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

  it('elimina un borrador existente mediante DELETE', () => {
    let completed = false;
    service.eliminarBorrador('draft-123').subscribe(() => {
      completed = true;
    });

    const req = http.expectOne({ method: 'DELETE', url: `${environment.apiUrl}/expedientes/draft-123/` });
    req.flush(null);
    expect(completed).toBeTrue();
  });
});
