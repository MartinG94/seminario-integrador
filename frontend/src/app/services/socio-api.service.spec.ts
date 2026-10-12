import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { SocioApiService, SocioLegajoDTO, PaginatedResponse, SocioListItemDTO, SocioIdentitySource } from './socio-api.service';
import { environment } from '../../environments/environment';

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

  const historyEntry = {
    movement_id: 17, applied_points: 2,
    historical_case: { id: 101, number: 'HIST-101', recorded_at: '2026-10-01T12:00:00Z', state: 'emitido' },
    resolution: { id: 201, text: 'VISTO\nCONSIDERANDO\nSE RESUELVE', regulations: ['Art. 93'] },
    managed_case: null
  };

  it('consulta saldo e historial propios juntos sin transmitir identidad (TS77.58)', () => {
    let result: unknown;
    service.getOwnPointsHistory().subscribe(value => result = value);
    const request = httpMock.expectOne(`${environment.apiUrl}/socios/me/points-history/`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.keys()).toEqual([]);
    expect(request.request.body).toBeNull();
    request.flush({ points_balance: 2, entries: [historyEntry] });
    expect(result).toEqual({ points_balance: 2, entries: [historyEntry] });
  });

  it('consulta historial de ficha con el namespace explícito y conserva los permisos HTTP (TS77.58)', () => {
    let status: number | undefined;
    service.getPointsHistory(101, 'institutional').subscribe({ error: error => status = error.status });
    const request = httpMock.expectOne(r => r.url === `${environment.apiUrl}/socios/101/points-history/`);
    expect(request.request.params.get('identity_source')).toBe('institutional');
    request.flush({}, { status: 403, statusText: 'Forbidden' });
    expect(status).toBe(403);
  });

  it('concilia importes DECIMAL grandes sin rechazar errores normales de coma flotante (TS77.58)', () => {
    let received = false;
    service.getOwnPointsHistory().subscribe(() => received = true);
    httpMock.expectOne(`${environment.apiUrl}/socios/me/points-history/`).flush({
      points_balance: 99999999.98,
      entries: [
        { ...historyEntry, movement_id: 1, applied_points: 99999999.99 },
        { ...historyEntry, movement_id: 2, applied_points: 99999999.98 },
        { ...historyEntry, movement_id: 3, applied_points: -99999999.99 }
      ]
    });
    expect(received).toBeTrue();
  });

  const invalidHistories: readonly unknown[] = [
    {}, null, { points_balance: '2', entries: [] }, { points_balance: Number.NaN, entries: [] },
    { points_balance: 0, entries: null }, { points_balance: 2, entries: [] },
    { points_balance: 2, entries: [{ ...historyEntry, movement_id: 0 }] },
    { points_balance: 2, entries: [{ ...historyEntry, applied_points: '2' }] },
    { points_balance: 2, entries: [{ ...historyEntry, applied_points: Number.POSITIVE_INFINITY }] },
    { points_balance: 2, entries: [{ ...historyEntry, historical_case: { ...historyEntry.historical_case, state: 'creado' } }] },
    { points_balance: 2, entries: [{ ...historyEntry, historical_case: { ...historyEntry.historical_case, recorded_at: 'invalid' } }] },
    { points_balance: 2, entries: [{ ...historyEntry, historical_case: { ...historyEntry.historical_case, recorded_at: '0' } }] },
    { points_balance: 2, entries: [{ ...historyEntry, resolution: null }] },
    { points_balance: 2, entries: [{ ...historyEntry, resolution: { ...historyEntry.resolution, text: '' } }] },
    { points_balance: 2, entries: [{ ...historyEntry, resolution: { ...historyEntry.resolution, regulations: [17] } }] },
    { points_balance: 2, entries: [{ ...historyEntry, resolution: { ...historyEntry.resolution, regulations: [] } }] },
    { points_balance: 2, entries: [{ ...historyEntry, applied_points: 2.001 }] },
    { points_balance: 2, entries: [{ ...historyEntry, managed_case: { id: 0, number: 'EXP-1', state: 'emitido' } }] },
    { points_balance: 2, entries: [{ ...historyEntry, managed_case: { id: 81, number: 'EXP-1', state: 'revision_resolucion' } }] },
    { points_balance: 4, entries: [historyEntry, historyEntry] }
  ];
  invalidHistories.forEach((response, index) => {
    it(`rechaza el historial malformado ${index} sin confirmar puntos parciales (TS77.58)`, () => {
      let received = false;
      let rejected = false;
      service.getOwnPointsHistory().subscribe({ next: () => received = true, error: () => rejected = true });
      httpMock.expectOne(`${environment.apiUrl}/socios/me/points-history/`).flush(response);
      expect(received).toBeFalse();
      expect(rejected).toBeTrue();
    });
  });

  it('consulta el saldo propio sin transmitir un identificador de socio (TS77.49)', () => {
    let points: number | undefined;
    service.getOwnPointsBalance().subscribe(result => points = result.points_balance);
    const request = httpMock.expectOne(`${environment.apiUrl}/socios/me/points-balance/`);
    expect(request.request.method).toBe('GET');
    expect(request.request.params.keys()).toEqual([]);
    expect(request.request.body).toBeNull();
    request.flush({ points_balance: 2 });
    expect(points).toBe(2);
  });

  it('propaga un error de saldo propio sin reemplazarlo por cero (TS77.49)', () => {
    let points: number | undefined;
    let status: number | undefined;
    service.getOwnPointsBalance().subscribe({
      next: result => points = result.points_balance,
      error: error => status = error.status
    });
    httpMock.expectOne(`${environment.apiUrl}/socios/me/points-balance/`)
      .flush({}, { status: 403, statusText: 'Forbidden' });
    expect(status).toBe(403);
    expect(points).toBeUndefined();
  });

  const invalidBalanceResponses: readonly unknown[] = [
    {}, null, { points_balance: null }, { points_balance: '2' },
    { points_balance: Number.NaN }, { points_balance: Number.POSITIVE_INFINITY }
  ];
  invalidBalanceResponses.forEach((response, index) => {
    it(`rechaza una respuesta de saldo propio malformada ${index} sin confirmar puntos (TS77.51)`, () => {
      let points: number | undefined;
      let rejected = false;
      service.getOwnPointsBalance().subscribe({
        next: result => points = result?.points_balance,
        error: () => rejected = true
      });
      httpMock.expectOne(`${environment.apiUrl}/socios/me/points-balance/`).flush(response);
      expect(points).toBeUndefined();
      expect(rejected).toBeTrue();
    });
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
