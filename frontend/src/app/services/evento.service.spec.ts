import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { EventoService } from './evento.service';
import { environment } from '../../environments/environment';
import {
  CrearEventoPayload,
  EventoInstitucional,
  ReportarAsistenciaPayload
} from '../models/evento.model';

describe('EventoService', () => {
  let service: EventoService;
  let httpMock: HttpTestingController;
  const baseUrl = `${environment.apiUrl}/expedientes/eventos`;
  const sociosUrl = `${environment.apiUrl}/expedientes/socios`;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [EventoService]
    });
    service = TestBed.inject(EventoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('getEventos debe solicitar GET con parámetros de filtro', () => {
    service.getEventos({ categoria: 'REUNION', tipo: 'ORDINARIA', estado: 'EN_CURSO', search: 'Consejo' }).subscribe(res => {
      expect(res.length).toBe(1);
    });

    const req = httpMock.expectOne(request =>
      request.url === `${baseUrl}/` &&
      request.params.get('categoria') === 'REUNION' &&
      request.params.get('tipo') === 'ORDINARIA' &&
      request.params.get('estado') === 'EN_CURSO' &&
      request.params.get('search') === 'Consejo'
    );
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, titulo: 'Reunión Ordinaria', categoria: 'REUNION' }]);
  });

  it('getEventoById debe solicitar GET por id', () => {
    service.getEventoById(42).subscribe(res => {
      expect(res.id).toBe(42);
      expect(res.titulo).toBe('Asamblea General');
    });

    const req = httpMock.expectOne(`${baseUrl}/42/`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 42, titulo: 'Asamblea General' });
  });

  it('crearEvento debe emitir POST con payload', () => {
    const payload: CrearEventoPayload = {
      titulo: 'Nueva Reunión Ordinaria',
      categoria: 'REUNION',
      tipo: 'ORDINARIA',
      modalidad: 'PRESENCIAL_SEDE',
      fecha_programada: '2026-11-01T18:00:00Z',
      fecha_fin: null,
      modo_convocatoria: 'GRUPO',
      grupo_convocado: 'G58'
    };

    service.crearEvento(payload).subscribe(res => {
      expect(res.id).toBe(10);
      expect(res.titulo).toBe('Nueva Reunión Ordinaria');
    });

    const req = httpMock.expectOne(`${baseUrl}/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ id: 10, ...payload });
  });

  it('getAsistencias debe solicitar GET al subrecurso de asistencias', () => {
    service.getAsistencias(15).subscribe(res => {
      expect(res.length).toBe(2);
    });

    const req = httpMock.expectOne(`${baseUrl}/15/asistencias/`);
    expect(req.request.method).toBe('GET');
    req.flush([
      { id: 1, socio_id: 101, estado_asistencia: 'PRESENTE', motivo: 'En sede' },
      { id: 2, socio_id: 102, estado_asistencia: 'AUSENTE_INJUSTIFICADO', motivo: 'Sin aviso' }
    ]);
  });

  it('registrarAsistenciasBulk debe emitir POST con asistencias y motivos circunstanciados', () => {
    const payload: ReportarAsistenciaPayload = {
      estrategia: 'MANUAL',
      cerrar_evento: false,
      asistencias: [
        { socio_id: 101, estado_asistencia: 'PRESENTE', motivo: 'A tiempo' }
      ]
    };

    service.registrarAsistenciasBulk(15, payload).subscribe(res => {
      expect(res.asistencias_procesadas).toBe(1);
    });

    const req = httpMock.expectOne(`${baseUrl}/15/reportar-asistencia/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush({ evento_id: 15, estado_evento: 'EN_CURSO', asistencias_procesadas: 1, expedientes_generados: 0, apercibimientos_generados: 0 });
  });

  it('procesarAsistencias debe emitir POST con cerrar_evento=true', () => {
    service.procesarAsistencias(20, { asistencias: [] }).subscribe(res => {
      expect(res.estado_evento).toBe('CERRADA');
      expect(res.expedientes_generados).toBe(2);
    });

    const req = httpMock.expectOne(`${baseUrl}/20/reportar-asistencia/`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.cerrar_evento).toBe(true);
    req.flush({ evento_id: 20, estado_evento: 'CERRADA', asistencias_procesadas: 0, expedientes_generados: 2, apercibimientos_generados: 1 });
  });

  it('getApercibimientos debe solicitar GET del historial de apercibimientos del socio', () => {
    service.getApercibimientos(88).subscribe(res => {
      expect(res.length).toBe(1);
      expect(res[0].estado).toBe('PENDIENTE');
    });

    const req = httpMock.expectOne(`${sociosUrl}/88/apercibimientos/`);
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, socio_id: 88, origen_tipo: 'REUNION_TARDANZA_LEVE', estado: 'PENDIENTE', motivo: 'Tardanza 20 min' }]);
  });
});
