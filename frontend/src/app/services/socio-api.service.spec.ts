import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SocioApiService, SocioLegajoDTO, PaginatedResponse, SocioListItemDTO } from './socio-api.service';

describe('SocioApiService', () => {
  let service: SocioApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [SocioApiService]
    });
    service = TestBed.inject(SocioApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('searchSocios() debe consultar GET /api/v1/socios/ con query y paginación (CA1 / CA3)', () => {
    const mockRes: PaginatedResponse<SocioListItemDTO> = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 5,
          legajo: '74907',
          first_name: 'Lucas',
          last_name: 'Gastiaburu',
          email: '74907@aveit.test',
          role: 'SOCIO',
          category: 'ACTIVE',
          category_display: 'Activo',
          subcomision: 'Cómputos'
        }
      ]
    };

    service.searchSocios('gastiaburu', 1).subscribe((data) => {
      expect(data.count).toBe(1);
      expect(data.results[0].legajo).toBe('74907');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/socios/') && r.params.get('search') === 'gastiaburu' && r.params.get('page') === '1');
    expect(req.request.method).toBe('GET');
    req.flush(mockRes);
  });

  it('getLegajo() debe consultar GET /api/v1/socios/<id>/legajo/ (T7 / CA2)', () => {
    const mockLegajo: SocioLegajoDTO = {
      id: 5,
      legajo: '74907',
      first_name: 'Lucas',
      last_name: 'Gastiaburu',
      email: '74907@aveit.test',
      role: 'SOCIO',
      category: 'ACTIVE',
      category_display: 'Activo',
      subcomision: 'Cómputos',
      social_year: 4,
      is_enabled: true
    };

    service.getLegajo(5).subscribe((legajo) => {
      expect(legajo.legajo).toBe('74907');
      expect(legajo.first_name).toBe('Lucas');
      expect(legajo.subcomision).toBe('Cómputos');
    });

    const req = httpMock.expectOne((r) => r.url.endsWith('/socios/5/legajo/'));
    expect(req.request.method).toBe('GET');
    req.flush(mockLegajo);
  });
});
