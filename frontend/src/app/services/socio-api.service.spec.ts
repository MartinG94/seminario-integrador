import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SocioApiService, SocioLegajoDTO, PaginatedResponse, SocioListItemDTO, SocioIdentitySource } from './socio-api.service';

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
          category: 'SENIOR',
          category_display: 'Senior',
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
      category: 'SENIOR',
      category_display: 'Senior',
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

  const identitySources: SocioIdentitySource[] = ['local', 'institutional'];
  identitySources.forEach(identitySource => {
    it(`consulta el namespace ${identitySource} sin cambiar ruta ni respuesta (TS77.35)`, () => {
      let result: SocioLegajoDTO | undefined;
      service.getLegajo(41, identitySource).subscribe(legajo => result = legajo);

      const request = httpMock.expectOne(r => r.url.endsWith('/socios/41/legajo/'));
      expect(request.request.params.get('identity_source')).toBe(identitySource);
      request.flush({
        id: 41, legajo: identitySource === 'institutional' ? null : '74907',
        first_name: 'Lucas', last_name: 'Gastiaburu',
        email: '74907@aveit.test', role: 'SOCIO', category: 'EX_TRAVELER',
        category_display: 'Exviajero', subcomision: 'Cómputos', social_year: null,
        is_enabled: true, points_balance: -2
      });
      expect(result?.category).toBe('EX_TRAVELER');
      expect(result?.legajo).toBe(identitySource === 'institutional' ? null : '74907');
      expect(result?.social_year).toBeNull();
      expect(result?.is_enabled).toBeTrue();
      expect(result?.points_balance).toBe(-2);
    });
  });

  it('conserva llamadas anteriores sin indicar namespace (TS77.35)', () => {
    service.getLegajo(41).subscribe();
    const request = httpMock.expectOne(r => r.url.endsWith('/socios/41/legajo/'));
    expect(request.request.params.has('identity_source')).toBeFalse();
    request.flush({});
  });

  it('propaga la ausencia institucional sin consultar otra identidad (TS77.35)', () => {
    let status = 0;
    service.getLegajo(41, 'institutional').subscribe({ error: error => status = error.status });
    httpMock.expectOne(r => r.url.endsWith('/socios/41/legajo/'))
      .flush({}, { status: 404, statusText: 'Not Found' });
    expect(status).toBe(404);
    httpMock.expectNone(r => r.url.endsWith('/socios/41/legajo/'));
  });
});
