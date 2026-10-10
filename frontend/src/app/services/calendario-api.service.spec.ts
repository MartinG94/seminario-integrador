import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { CalendarioApiService, HolidayDto } from './calendario-api.service';

describe('CalendarioApiService', () => {
  let service: CalendarioApiService;
  let http: HttpTestingController;
  const base = `${environment.apiUrl}/expedientes/calendario`;
  const holiday: HolidayDto = {
    id: 1, fecha: '2026-10-13', descripcion: 'Asueto',
    creado_por: 7, creado_por_nombre: 'Ana Pérez (ana)',
    created_at: '2026-10-10T12:30:45-03:00'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(CalendarioApiService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => http.verify());

  it('consulta el calendario directamente sin inicializar versiones', () => {
    service.getFeriados().subscribe(items => expect(items).toEqual([holiday]));
    const req = http.expectOne(`${base}/feriados/`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.keys()).toEqual([]);
    req.flush([holiday]);
  });

  it('envía únicamente filtros Año, Mes y orden Fecha', () => {
    service.getFeriados(2026, 10, '-fecha').subscribe();
    const req = http.expectOne(request => request.url === `${base}/feriados/`);
    expect(req.request.params.keys().sort()).toEqual(['month', 'ordering', 'year']);
    expect(req.request.params.get('year')).toBe('2026');
    expect(req.request.params.get('month')).toBe('10');
    expect(req.request.params.get('ordering')).toBe('-fecha');
    req.flush([holiday]);
  });

  it('crea un feriado con fecha y denominación y recibe auditoría del servidor', () => {
    const payload = { fecha: holiday.fecha, descripcion: holiday.descripcion };
    service.addFeriado(payload).subscribe(item => expect(item.creado_por_nombre).toContain('Ana Pérez'));
    const req = http.expectOne(`${base}/feriados/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(holiday);
  });

  it('simula sin selección de versión', () => {
    const payload = { start_at: '2026-10-12T14:30:00-03:00', business_days: 1 };
    service.calcularPlazo(payload).subscribe(result => expect(result.deadline).toBe('2026-10-14T14:30:00-03:00'));
    const req = http.expectOne(`${base}/calcular-plazo/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({
      start_at: payload.start_at, business_days: 1, deadline: '2026-10-14T14:30:00-03:00',
      dias_habiles_computados: [{ day_number: 1, date: '2026-10-14', weekday: 'Miércoles' }],
      dias_excluidos: [{ date: '2026-10-13', reason: 'Feriado: Asueto' }]
    });
  });
});
