import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

import { AdminApiService } from './admin-api.service';

describe('AdminApiService', () => {
  let service: AdminApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(AdminApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('consulta y actualiza parámetros', () => {
    service.listarParametros().subscribe();
    http.expectOne({ method: 'GET', url: '/api/v1/admin/parametros/' }).flush([]);

    service.actualizarParametro('plazo_descargo_dias_habiles', 7).subscribe();
    const put = http.expectOne({ method: 'PUT', url: '/api/v1/admin/parametros/plazo_descargo_dias_habiles/' });
    expect(put.request.body).toEqual({ valor: 7 });
    put.flush({});

    service.historialParametro('umbral_preventivo').subscribe();
    http.expectOne({ method: 'GET', url: '/api/v1/admin/parametros/umbral_preventivo/historial/' }).flush([]);
  });

  it('gestiona miembros del Tribunal', () => {
    service.listarMiembrosTribunal().subscribe();
    http.expectOne({ method: 'GET', url: '/api/v1/admin/usuarios-td/' }).flush([]);

    service.asignarMiembroTribunal(12).subscribe();
    const post = http.expectOne({ method: 'POST', url: '/api/v1/admin/usuarios-td/' });
    expect(post.request.body).toEqual({ socio_id: 12 });
    post.flush({});

    service.revocarMiembroTribunal(12).subscribe();
    http.expectOne({ method: 'DELETE', url: '/api/v1/admin/usuarios-td/12/' }).flush(null);
  });

  it('lee los límites de adjuntos', () => {
    service.obtenerLimitesAdjuntos().subscribe(l => expect(l.cantidad_maxima).toBe(4));
    http.expectOne('/api/v1/parametros/adjuntos/').flush({ tamano_maximo_mb: 8, cantidad_maxima: 4 });
  });
});
