import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { RankingService } from './ranking.service';
import { RankingSocio } from '../ranking-socios/ranking-socio.model';
import { PaginatedResponse, RankingPaginationParams } from '../models/paginated-response.model';
import { environment } from '../../environments/environment';

describe('RankingService (T-87.10 / SCRUM-118)', () => {
  let service: RankingService;
  let httpMock: HttpTestingController;
  const apiUrl = `${environment.apiUrl}/ranking/`;

  const mockSocios: RankingSocio[] = [
    {
      id: '1',
      posicion: 1,
      legajo: '54321',
      nombre: 'Carlos',
      apellido: 'Alonso',
      categoria: 'ACTIVO',
      subcomision: 'Cómputos',
      grupo: 'G1',
      saldo: 15.5,
      saldoHistorico: 15.5,
      saldoPuntajeGeneral: 15.5,
      diferencia: 0,
      reconciliado: true,
    },
  ];

  const mockPaginatedResponse: PaginatedResponse<RankingSocio> = {
    count: 25,
    total_pages: 2,
    current_page: 1,
    page_size: 20,
    next: 'http://localhost:8000/api/v1/ranking/?page=2',
    previous: null,
    results: mockSocios,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [RankingService],
    });
    service = TestBed.inject(RankingService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debería instanciar el servicio correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('debería consultar el ranking sin parámetros y retornar PaginatedResponse', () => {
    service.obtenerRanking().subscribe((res) => {
      expect(res).toEqual(mockPaginatedResponse);
      expect(res.results.length).toBe(1);
      expect(res.count).toBe(25);
    });

    const req = httpMock.expectOne(apiUrl);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys().length).toBe(0);
    req.flush(mockPaginatedResponse);
  });

  it('debería enviar parámetros page, page_size, ordering y filtros en query params', () => {
    const params: RankingPaginationParams = {
      page: 2,
      page_size: 10,
      ordering: '-saldo',
      search: 'Carlos',
      categoria: 'ACTIVO',
      subcomision: 'Cómputos',
      reconciliado: true,
    };

    service.obtenerRanking(params).subscribe((res) => {
      expect(res.current_page).toBe(2);
      expect(res.page_size).toBe(10);
    });

    const req = httpMock.expectOne((r) => r.url === apiUrl);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('page_size')).toBe('10');
    expect(req.request.params.get('ordering')).toBe('-saldo');
    expect(req.request.params.get('search')).toBe('Carlos');
    expect(req.request.params.get('categoria')).toBe('ACTIVO');
    expect(req.request.params.get('subcomision')).toBe('Cómputos');
    expect(req.request.params.get('reconciliado')).toBe('true');

    req.flush({ ...mockPaginatedResponse, current_page: 2, page_size: 10 });
  });

  it('debería envolver automáticamente una respuesta plana de tipo array en PaginatedResponse', () => {
    service.obtenerRanking().subscribe((res) => {
      expect(res.count).toBe(1);
      expect(res.total_pages).toBe(1);
      expect(res.current_page).toBe(1);
      expect(res.results).toEqual(mockSocios);
    });

    const req = httpMock.expectOne(apiUrl);
    req.flush(mockSocios);
  });
});
