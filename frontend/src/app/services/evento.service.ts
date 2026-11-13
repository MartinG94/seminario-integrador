import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
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
import { PaginatedResponse } from '../models/paginated-response.model';

@Injectable({
  providedIn: 'root'
})
export class EventoService {
  private readonly baseUrl = `${environment.apiUrl}/expedientes/eventos`;
  private readonly sociosUrl = `${environment.apiUrl}/expedientes/socios`;

  constructor(private http: HttpClient) {}

  /**
   * Obtiene la lista de eventos institucionales con filtros opcionales y envolvente paginada.
   */
  getEventos(filtros?: EventoFiltros): Observable<PaginatedResponse<EventoInstitucional>> {
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
      if (filtros.mis_eventos) {
        params = params.set('mis_eventos', 'true');
      }
      if (filtros.search) {
        params = params.set('search', filtros.search.trim());
      }
      if (filtros.page != null) {
        params = params.set('page', filtros.page.toString());
      }
      if (filtros.page_size != null) {
        params = params.set('page_size', filtros.page_size.toString());
      }
    }
    return this.http
      .get<PaginatedResponse<EventoInstitucional> | EventoInstitucional[]>(`${this.baseUrl}/`, { params })
      .pipe(
        map((response) => {
          if (Array.isArray(response)) {
            return {
              count: response.length,
              total_pages: 1,
              current_page: 1,
              page_size: response.length,
              next: null,
              previous: null,
              results: response,
            };
          }
          return response;
        })
      );
  }

  /**
   * Obtiene la lista de eventos creados por el usuario logueado con paginación server-side.
   */
  getMisEventos(filtros?: EventoFiltros): Observable<PaginatedResponse<EventoInstitucional>> {
    return this.getEventos({ ...filtros, mis_eventos: true });
  }

  /**
   * Obtiene eventos garantizando la interfaz canónica PaginatedResponse.
   */
  getEventosPaginados(filtros?: EventoFiltros): Observable<PaginatedResponse<EventoInstitucional>> {
    return this.getEventos(filtros);
  }

  /**
   * Notifica formalmente un evento en estado CREADO y despacha avisos por correo.
   */
  notificarEvento(id: number | string): Observable<{ detail: string; evento: EventoInstitucional }> {
    return this.http.post<{ detail: string; evento: EventoInstitucional }>(
      `${this.baseUrl}/${id}/notificar/`,
      {}
    );
  }

  /**
   * Anula un evento. Si estaba notificado, despacha aviso formal pidiendo disculpas a convocados.
   */
  anularEvento(
    id: number | string,
    motivo?: string
  ): Observable<{ detail: string; evento: EventoInstitucional }> {
    return this.http.post<{ detail: string; evento: EventoInstitucional }>(
      `${this.baseUrl}/${id}/anular/`,
      { motivo }
    );
  }

  /**
   * Registra la fecha y hora de finalización para eventos en estado ABIERTO o sin fin.
   */
  fijarHoraFin(
    id: number | string,
    fechaFin: string
  ): Observable<{ detail: string; evento: EventoInstitucional }> {
    return this.http.post<{ detail: string; evento: EventoInstitucional }>(
      `${this.baseUrl}/${id}/fijar-hora-fin/`,
      { fecha_fin: fechaFin }
    );
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
    const metodo = payload?.metodo_captura || payload?.estrategia || 'MANUAL';
    const body: ReportarAsistenciaPayload = {
      estrategia: metodo,
      metodo_captura: metodo,
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
