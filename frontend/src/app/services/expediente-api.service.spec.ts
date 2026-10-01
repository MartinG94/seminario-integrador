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
});
