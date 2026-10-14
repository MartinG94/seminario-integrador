import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  AsistenciaEvento,
  CrearEventoPayload,
  EventoFiltros,
  EventoInstitucional,
  RegistroApercibimiento,
  ReportarAsistenciaPayload,
  ReportarAsistenciaResponse
} from '../models/evento.model';

@Injectable({
  providedIn: 'root'
})
export class EventoService {
  private readonly baseUrl = `${environment.apiUrl}/expedientes/eventos`;
  private readonly sociosUrl = `${environment.apiUrl}/expedientes/socios`;

  constructor(private http: HttpClient) {}

  /**
   * Obtiene la lista de eventos institucionales con filtros opcionales.
   */
  getEventos(filtros?: EventoFiltros): Observable<EventoInstitucional[]> {
    let params = new HttpParams();
    if (filtros) {
      if (filtros.categoria) {
        params = params.set('categoria', filtros.categoria);
      }
      if (filtros.tipo) {
        params = params.set('tipo', filtros.tipo);
      }
      if (filtros.estado) {
        params = params.set('estado', filtros.estado);
      }
      if (filtros.modo_convocatoria) {
        params = params.set('modo_convocatoria', filtros.modo_convocatoria);
      }
      if (filtros.search) {
        params = params.set('search', filtros.search.trim());
      }
      if (filtros.page != null) {
        params = params.set('page', filtros.page.toString());
      }
    }
    return this.http.get<EventoInstitucional[]>(`${this.baseUrl}/`, { params });
  }

  /**
   * Obtiene un evento institucional por su identificador único.
   */
  getEventoById(id: number | string): Observable<EventoInstitucional> {
    return this.http.get<EventoInstitucional>(`${this.baseUrl}/${id}/`);
  }

  /**
   * Crea y publica un nuevo evento o reunión institucional.
   */
  crearEvento(payload: CrearEventoPayload): Observable<EventoInstitucional> {
    return this.http.post<EventoInstitucional>(`${this.baseUrl}/`, payload);
  }

  /**
   * Obtiene la nómina de asistencias y convocados de un evento.
   */
  getAsistencias(eventoId: number | string): Observable<AsistenciaEvento[]> {
    return this.http.get<AsistenciaEvento[]>(`${this.baseUrl}/${eventoId}/asistencias/`);
  }

  /**
   * Guarda o actualiza masivamente las asistencias de un evento (con motivos circunstanciados).
   */
  registrarAsistenciasBulk(
    eventoId: number | string,
    payload: ReportarAsistenciaPayload
  ): Observable<ReportarAsistenciaResponse> {
    return this.http.post<ReportarAsistenciaResponse>(
      `${this.baseUrl}/${eventoId}/reportar-asistencia/`,
      payload
    );
  }

  /**
   * Procesa las asistencias y efectúa el cierre disciplinario del evento (emite expedientes y apercibimientos).
   */
  procesarAsistencias(
    eventoId: number | string,
    payload?: Partial<ReportarAsistenciaPayload>
  ): Observable<ReportarAsistenciaResponse> {
    const body: ReportarAsistenciaPayload = {
      estrategia: payload?.estrategia || 'MANUAL',
      asistencias: payload?.asistencias || [],
      cerrar_evento: true
    };
    return this.http.post<ReportarAsistenciaResponse>(
      `${this.baseUrl}/${eventoId}/reportar-asistencia/`,
      body
    );
  }

  /**
   * Consulta el libro mayor de apercibimientos de un socio (CA4).
   */
  getApercibimientos(socioId: number | string): Observable<RegistroApercibimiento[]> {
    return this.http.get<RegistroApercibimiento[]>(
      `${this.sociosUrl}/${socioId}/apercibimientos/`
    );
  }
}
