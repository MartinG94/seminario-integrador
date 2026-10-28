import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { ReportesService } from './reportes.service';
import { environment } from '../../environments/environment';

describe('ReportesService', () => {
  let service: ReportesService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [ReportesService],
    });
    service = TestBed.inject(ReportesService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse el servicio correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('debe consultar métricas T01', () => {
    service.getMetricasT01(6).subscribe((data) => {
      expect(data).toBeTruthy();
    });

    const req = httpMock.expectOne(
      (r) => r.url === `${environment.apiUrl}/expedientes/reportes/t01/` && r.params.get('subcomision_id') === '6'
    );
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('debe consultar métricas de reuniones', () => {
    service.getMetricasReuniones().subscribe((data) => {
      expect(data).toBeTruthy();
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/expedientes/reportes/reuniones/`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('debe consultar subcomisiones para el selector', () => {
    service.getSubcomisiones().subscribe((data) => {
      expect(data).toBeTruthy();
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/expedientes/reportes/subcomisiones/`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('debe consultar métricas de una subcomisión', () => {
    service.getMetricasSubcomision(6).subscribe((data) => {
      expect(data).toBeTruthy();
    });

    const req = httpMock.expectOne(
      (r) => r.url === `${environment.apiUrl}/expedientes/reportes/subcomision/` && r.params.get('subcomision_id') === '6'
    );
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('debe consultar histórico y récords', () => {
    service.getHistoricoYRecords().subscribe((data) => {
      expect(data).toBeTruthy();
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/expedientes/reportes/historico-records/`);
    expect(req.request.method).toBe('GET');
    req.flush({});
  });

  it('debe permitir actualizar clasificación de un expediente por TD', () => {
    service.actualizarClasificacion(123, 'CD').subscribe((res) => {
      expect(res).toBeTruthy();
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/expedientes/123/clasificacion/`);
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ clasificacion: 'CD' });
    req.flush({ status: 'ok' });
  });
});
