import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TribunalDataService } from './tribunal-data.service';
import { environment } from '../../environments/environment';
import { PaginatedResponse } from '../models/paginated-response.model';

describe('TribunalDataService (T-87.13 / SCRUM-118)', () => {
  let service: TribunalDataService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [TribunalDataService],
    });
    service = TestBed.inject(TribunalDataService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debería solicitar expedientes paginados con page y page_size', () => {
    const mockResponse: PaginatedResponse<any> = {
      count: 45,
      total_pages: 3,
      current_page: 2,
      page_size: 20,
      next: 'http://testserver/api/v1/expedientes/gestion/?page=3',
      previous: 'http://testserver/api/v1/expedientes/gestion/?page=1',
      results: [
        {
          id: 10,
          numero: 'EXP-0010/2026',
          motivo: 'Falta disciplinaria',
          socio_nombre: 'Martín Pérez',
          socio_legajo: '85194',
          subcomision: 'Cómputos',
          estado: 'creado',
          estado_display: 'Expediente Creado',
          puntos: -1.0,
          created_at: '2026-03-01T10:00:00Z',
          plazo_limite_at: null,
        },
      ],
    };

    service.listarExpedientes({ page: 2, page_size: 20 }).subscribe((res) => {
      expect(res.count).toBe(45);
      expect(res.total_pages).toBe(3);
      expect(res.current_page).toBe(2);
      expect(res.results.length).toBe(1);
      expect(res.results[0].numero).toBe('EXP-0010/2026');
      expect(res.results[0].socio).toBe('Martín Pérez');
    });

    const req = httpMock.expectOne(
      (r) =>
        r.url === `${environment.apiUrl}/expedientes/gestion/` &&
        r.params.get('page') === '2' &&
        r.params.get('page_size') === '20'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });

  it('debería envolver automáticamente una respuesta array plana en PaginatedResponse', () => {
    const mockFlatArray = [
      {
        id: 1,
        numero: 'EXP-0001/2026',
        motivo: 'Mérito extraordinario',
        socio_nombre: 'Ana Gómez',
        socio_legajo: '74907',
        subcomision: 'Cómputos',
        estado: 'emitido',
        estado_display: 'Emitido',
        puntos: 1.0,
        created_at: '2026-02-15T10:00:00Z',
        plazo_limite_at: null,
      },
    ];

    service.listarExpedientes().subscribe((res) => {
      expect(res.count).toBe(1);
      expect(res.total_pages).toBe(1);
      expect(res.current_page).toBe(1);
      expect(res.results.length).toBe(1);
      expect(res.results[0].numero).toBe('EXP-0001/2026');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/expedientes/gestion/`);
    expect(req.request.method).toBe('GET');
    req.flush(mockFlatArray);
  });
});
