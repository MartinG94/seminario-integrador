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

export interface EvidenciaMetadata {
  id: string;
  nombre_original: string;
  extension: string;
  mime_type: string;
  tamanio_bytes: number;
  sha256_hash: string;
  es_vigente: boolean;
  created_at: string;
}

export interface PresentarDescargoPayload {
  tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
  causal?: string;
  archivo?: string;
  texto?: string;
  evidencia_ids?: string[];
}

export type DecisionCausal = 'ACCEPTED' | 'REJECTED';

export interface EvidenciaValorada {
  id: string;
  nombre_original: string;
  sha256_hash: string;
}

export interface DecisionCausalDTO {
  id: number;
  descargo: number;
  version: number;
  decision: DecisionCausal;
  decision_display: string;
  regla_sugerida: DecisionCausal;
  regla_sugerida_display: string;
  se_aparta_de_regla: boolean;
  fundamento: string;
  evidencias_valoradas: EvidenciaValorada[];
  autor: string;
  autor_legajo: string;
  autor_rol: string;
  created_at: string;
}

export interface RegistrarDecisionCausalPayload {
  decision: DecisionCausal;
  fundamento?: string;
  evidencia_ids?: string[];
}

export interface DescargoDetalleDTO {
  id: number;
  socio_id: number;
  socio_legajo: string;
  socio_nombre: string;
  tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
  causal: string;
  texto: string;
  presentado_at: string | null;
  evidencias: EvidenciaMetadata[];
  regla_sugerida?: DecisionCausal;
  decisiones_causal?: DecisionCausalDTO[];
}

export interface ExpedienteDetalleDTO {
  id: number;
  numero: string;
  estado: string;
  descargos: DescargoDetalleDTO[];
}

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

  subirEvidencias(expedienteId: number | string, files: File[], tipoDescargo?: string): Observable<EvidenciaMetadata[]> {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('archivos', file, file.name);
    });
    if (tipoDescargo) {
      formData.append('tipo_descargo', tipoDescargo);
    }
    return this.http.post<EvidenciaMetadata[]>(`${this.apiUrl}/${expedienteId}/evidencia/`, formData);
  }

  descargarEvidencia(expedienteId: number | string, evidenciaId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${expedienteId}/evidencia/${evidenciaId}/`, {
      responseType: 'blob'
    });
  }

  presentarDescargo(expedienteId: number | string, payload: PresentarDescargoPayload): Observable<any> {
    return this.http.post(`${this.apiUrl}/${expedienteId}/descargo/`, payload);
  }

  listarMisExpedientes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/mis-expedientes/`);
  }

  eliminarDescargo(expedienteId: number | string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/${expedienteId}/descargo/`);
  }

  obtenerDetalleExpediente(expedienteId: number | string): Observable<ExpedienteDetalleDTO> {
    return this.http.get<ExpedienteDetalleDTO>(`${this.apiUrl}/${expedienteId}/`);
  }

  listarDecisionesCausal(expedienteId: number | string, descargoId: number): Observable<DecisionCausalDTO[]> {
    return this.http.get<DecisionCausalDTO[]>(
      `${this.apiUrl}/${expedienteId}/descargos/${descargoId}/decisiones/`
    );
  }

  registrarDecisionCausal(
    expedienteId: number | string,
    descargoId: number,
    payload: RegistrarDecisionCausalPayload
  ): Observable<DecisionCausalDTO> {
    return this.http.post<DecisionCausalDTO>(
      `${this.apiUrl}/${expedienteId}/descargos/${descargoId}/decisiones/`,
      payload
    );
  }
}

