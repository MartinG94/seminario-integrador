import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { PadronApiService } from './padron-api.service';

describe('PadronApiService', () => {
  let service: PadronApiService;
  let http: HttpTestingController;
  const socio = (id: number) => ({
    socio_id: id,
    legajo: `${id}`,
    first_name: `Nombre${id}`,
    last_name: `Apellido${id}`,
    subcomision: null,
    is_active: true
  });

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(PadronApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('recorre páginas activas y combina socios sin duplicarlos', () => {
    let result: unknown;
    service.listarSocios().subscribe(socios => result = socios);

    const first = http.expectOne(request => request.url === `${environment.apiUrl}/padron/socios/`);
    expect(first.request.params.get('page')).toBe('1');
    expect(first.request.params.get('page_size')).toBe('100');
    expect(first.request.params.get('is_active')).toBe('true');
    first.flush({ count: 101, page: 1, page_size: 100, results: [socio(1), socio(2)] });

    const second = http.expectOne(request => request.url === `${environment.apiUrl}/padron/socios/`);
    expect(second.request.params.get('page')).toBe('2');
    expect(second.request.params.get('is_active')).toBe('true');
    second.flush({ count: 101, page: 2, page_size: 100, results: [socio(2), socio(3)] });

    expect(result).toEqual([socio(1), socio(2), socio(3)]);
  });
});
