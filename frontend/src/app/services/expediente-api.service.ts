import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import type { NivelUrgencia } from './tribunal-data.service';

export type TipoAccionT01 = 'SANCTION' | 'MERIT';
export type EstadoT01 = 'DRAFT' | 'ISSUED';

export interface SocioInvolucrado {
  socio_id?: number;
  legajo?: string;
  first_name?: string;
  last_name?: string;
  subcomision?: string;
}

export interface ResolucionFinalInfo {
  emitido: boolean;
  fecha?: string;
  dictamen?: string;
}

export interface SolicitudMonitoreo {
  id: string;
  numero: string;
  numero_expediente: string | null;
  fecha: string;
  estado: EstadoT01;
  tipo_accion: TipoAccionT01;
  puntos: number | null;
  titulo: string;
  motivo: string;
  causal: string;
  razon: string;
  reglamentos_respaldantes: string[];
  anexo_fecha: string | null;
  anexo_lugar: string;
  anexo_relato: string;
  anexo_testigos: string;
  destinatarios_socios_ids: number[];
  estado_procesal: string;
  estado_procesal_display: string;
  urgencia?: NivelUrgencia;
  urgencia_display?: string;
  involucrados: SocioInvolucrado[];
  resolucion_final: ResolucionFinalInfo | null;
  created_at: string;
  issued_at: string | null;
}

export interface SolicitudT01 {
  id: string;
  estado: EstadoT01;
  solicitante: number;
  destinatario_socio_id: number | null;
  destinatarios_socios_ids: number[];
  tipo_accion: TipoAccionT01;
  urgencia?: NivelUrgencia;
  titulo: string;
  causal: string;
  puntos: number | string | null;
  motivo: string;
  razon: string;
  reglamentos_respaldantes: string[];
  anexo_fecha: string | null;
  anexo_lugar: string;
  anexo_relato: string;
  anexo_testigos: string;
  snapshot_destinatario: unknown;
  snapshots_destinatarios: unknown[];
  snapshot_emitido: unknown;
  numero_expediente: string | null;
  created_at: string;
  updated_at: string;
  issued_at: string | null;
}

export interface SolicitudT01Payload {
  destinatario_socio_id?: number | null;
  destinatarios_socios_ids?: number[];
  tipo_accion: TipoAccionT01;
  urgencia?: NivelUrgencia;
  titulo?: string;
  causal?: string;
  puntos?: number | null;
  motivo?: string;
  razon?: string;
  reglamentos_respaldantes?: string[];
  anexo_fecha?: string | null;
  anexo_lugar?: string;
  anexo_relato?: string;
  anexo_testigos?: string;
}

type T01MonitoringResponse = Omit<SolicitudMonitoreo, 'puntos'> & Pick<SolicitudT01, 'puntos'>;

@Injectable({ providedIn: 'root' })
export class ExpedienteApiService {
  private readonly apiUrl = `${environment.apiUrl}/expedientes`;

  constructor(private http: HttpClient) {}

  crearBorrador(payload: SolicitudT01Payload): Observable<SolicitudT01> {
    return this.http.post<SolicitudT01>(`${this.apiUrl}/`, payload);
  }

  actualizarBorrador(id: string, payload: Partial<SolicitudT01Payload>): Observable<SolicitudT01> {
    return this.http.patch<SolicitudT01>(`${this.apiUrl}/${id}/`, payload);
  }

  emitir(id: string): Observable<SolicitudT01> {
    return this.http.post<SolicitudT01>(`${this.apiUrl}/${id}/emitir/`, {});
  }

  obtener(id: string): Observable<SolicitudT01> {
    return this.http.get<SolicitudT01>(`${this.apiUrl}/${id}/`);
  }

  listarReglamentos(): Observable<{ reglamentos: string[] }> {
    return this.http.get<{ reglamentos: string[] }>(`${this.apiUrl}/reglamentos/`);
  }

  listarMisSolicitudes(params?: { search?: string; estado?: string }): Observable<SolicitudMonitoreo[]> {
    let httpParams = new HttpParams();
    if (params?.search) {
      httpParams = httpParams.set('search', params.search);
    }
    if (params?.estado) {
      httpParams = httpParams.set('estado', params.estado);
    }
    return this.http.get<T01MonitoringResponse[]>(`${this.apiUrl}/mis-solicitudes/`, { params: httpParams }).pipe(
      map(solicitudes => solicitudes.map(solicitud => ({
        ...solicitud,
        puntos: solicitud.puntos == null ? null : Number(solicitud.puntos)
      })))
    );
  }

  eliminarBorrador(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}/`);
  }
}
