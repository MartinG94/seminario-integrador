import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { CalendarioApiService, CalcularPlazoRequest, CreateCalendarioVersionRequest } from './calendario-api.service';

describe('CalendarioApiService', () => {
  let service: CalendarioApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(CalendarioApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('obtiene la lista de versiones de calendario', () => {
    service.getVersiones().subscribe(versiones => {
      expect(versiones.length).toBe(1);
      expect(versiones[0].version).toBe(1);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/calendario/versiones/`);
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, version: 1, nombre: 'Calendario Oficial 2026', activa: true, feriados_count: 16 }]);
  });

  it('obtiene el detalle de una versión con sus feriados', () => {
    service.getVersionDetail(1).subscribe(version => {
      expect(version.version).toBe(1);
      expect(version.feriados?.length).toBe(1);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/calendario/versiones/1/`);
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 1,
      version: 1,
      nombre: 'Calendario Oficial 2026',
      activa: true,
      feriados: [{ fecha: '2026-01-01', descripcion: 'Año Nuevo', tipo: 'NACIONAL', es_laborable: false }]
    });
  });

  it('crea una nueva versión auditada de calendario', () => {
    const payload: CreateCalendarioVersionRequest = {
      nombre: 'Calendario v2',
      vigencia_desde: '2026-06-01',
      motivo_cambio: 'Actualización de invierno',
      clonar_de_version_id: 1
    };

    service.createVersion(payload).subscribe(res => {
      expect(res.version).toBe(2);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/calendario/versiones/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: 2, version: 2, nombre: 'Calendario v2', activa: true });
  });

  it('obtiene feriados con filtros de query params', () => {
    service.getFeriados(1, 2026).subscribe(feriados => {
      expect(feriados.length).toBe(1);
    });

    const req = http.expectOne(
      r => r.url === `${environment.apiUrl}/expedientes/calendario/feriados/` &&
           r.params.get('version_id') === '1' &&
           r.params.get('year') === '2026'
    );
    expect(req.request.method).toBe('GET');
    req.flush([{ fecha: '2026-10-12', descripcion: 'Diversidad Cultural', tipo: 'NACIONAL', es_laborable: false }]);
  });

  it('ejecuta el cálculo de plazos en días hábiles', () => {
    const payload: CalcularPlazoRequest = {
      start_at: '2026-10-08T10:00:00-03:00',
      business_days: 5
    };

    service.calcularPlazo(payload).subscribe(res => {
      expect(res.deadline).toContain('2026-10-16');
      expect(res.dias_habiles_computados.length).toBe(5);
    });

    const req = http.expectOne(`${environment.apiUrl}/expedientes/calendario/calcular-plazo/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({
      start_at: payload.start_at,
      business_days: 5,
      deadline: '2026-10-16T10:00:00-03:00',
      dias_habiles_computados: [
        { day_number: 1, date: '2026-10-09', weekday: 'Viernes' },
        { day_number: 2, date: '2026-10-13', weekday: 'Martes' },
        { day_number: 3, date: '2026-10-14', weekday: 'Miércoles' },
        { day_number: 4, date: '2026-10-15', weekday: 'Jueves' },
        { day_number: 5, date: '2026-10-16', weekday: 'Viernes' }
      ],
      dias_excluidos: [{ date: '2026-10-10', reason: 'Sábado' }]
    });
  });
});
