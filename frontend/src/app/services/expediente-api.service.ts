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
  grupo?: string | null;
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

export interface ExpedienteRankingDetalle {
  id: number;
  numero: string;
  titulo?: string;
  motivo: string;
  puntos: number | string;
  estado: string;
  urgencia: string;
  urgencia_display: string;
  created_at: string;
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

export type OperacionDescargo = 'PRESENTADO' | 'CORREGIDO' | 'RETIRADO';

/** Versión inmutable de un descargo, tal como la devuelve el historial del backend. */
export interface DescargoVersionDto {
  id: number;
  numero: number;
  operacion: OperacionDescargo;
  operacion_display: string;
  tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
  causal: string;
  texto: string;
  archivo: string;
  evidencias: Partial<EvidenciaMetadata>[];
  actor: string;
  socio_id: number;
  socio_legajo: string;
  socio_nombre: string;
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
  socio_first_name?: string;
  socio_last_name?: string;
  tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
  causal: string;
  texto: string;
  presentado_at: string | null;
  evidencias: EvidenciaMetadata[];
  regla_sugerida?: DecisionCausal;
  decisiones_causal?: DecisionCausalDTO[];
  leido?: boolean;
  puntaje_ratificado?: number | null;
}

export interface SocioInvolucradoDetalleDTO {
  id: number;
  legajo: string;
  nombre: string;
  first_name?: string;
  last_name?: string;
  grupo?: string;
  estado?: string;
}


export interface ResponsableTdDTO {
  titulo: string;
  legajo: string;
  nombre: string;
  grupo: string;
  es_suplente?: boolean;
  display: string;
}

export interface EvidenciaVisorDTO {
  id: string;
  nombre_original: string;
  extension: string;
  mime_type: string;
  tamanio_bytes: number;
  sha256_hash: string;
  sha256_valido: boolean;
  archivo_danado: boolean;
  es_vigente: boolean;
  created_at: string;
}

export interface DescargoVisorDTO {
  id: number;
  socio_id: number;
  socio_legajo: string;
  socio_nombre: string;
  tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
  tipo_display: string;
  causal: string;
  texto: string;
  archivo: string;
  presentado_at: string | null;
  contiene_datos_medicos?: boolean;
  datos_medicos_restringidos?: boolean;
  evidencias: EvidenciaVisorDTO[];
  regla_sugerida?: DecisionCausal;
  decisiones_causal?: DecisionCausalDTO[];
}

export interface InvolucradoVisorDTO {
  id: number;
  legajo: string;
  nombre: string;
  first_name?: string;
  last_name?: string;
  grupo?: string;
  estado?: string;
  tiene_descargo: boolean;
  estado_descargo: 'PRESENTADO' | 'PLAZO_VENCIDO_SIN_DESCARGO' | 'PENDIENTE' | 'NO_INICIADO';
  estado_descargo_display: string;
  descargo?: DescargoVisorDTO | null;
}

export interface TimelineHitoDTO {
  id: string | number;
  fecha_hora: string;
  tipo: string;
  tipo_display: string;
  titulo: string;
  descripcion: string;
  actor: string;
  icono?: string;
  color?: string;
  es_secundario?: boolean;
}

export interface ExpedienteVisorData {
  id: number;
  numero: string;
  anio: number;
  titulo: string;
  motivo: string;
  razon: string;
  causal: string;
  reglamento_asociado: string;
  reglamentos_respaldantes: string[];
  puntos: number | string;
  estado: string;
  estado_display: string;
  urgencia: NivelUrgencia;
  urgencia_display: string;
  fecha_solicitud: string;
  created_at: string;
  solicitante: {
    legajo: string;
    nombre: string;
    grupo?: string;
    display: string;
  };
  anexo: {
    anexo_fecha: string | null;
    anexo_lugar: string;
    anexo_relato: string;
    anexo_testigos: string;
  };
  plazo_inicio_at: string | null;
  plazo_limite_at: string | null;
  esta_en_plazo: boolean;
  horas_restantes: number;
  responsables_td: ResponsableTdDTO[];
  involucrados: InvolucradoVisorDTO[];
  timeline: TimelineHitoDTO[];
  puede_resolver_causal?: boolean;
  puede_dictar_resolucion?: boolean;
}

export interface ExpedienteDetalleDTO {
  id: number;
  numero: string;
  estado: string;
  socios?: SocioInvolucradoDetalleDTO[];
  descargos: DescargoDetalleDTO[];
  reglamentos_respaldantes?: string[];
}

// --- Apelación y adecuación del T01 (PB-02, Spec 008) ---

export interface SocioT01DTO {
  id: number;
  legajo: string;
  nombre: string;
}

export interface PeriodoApelacionDTO {
  socio_id: number;
  socio: string;
  origen: 'APERTURA' | 'ADECUACION';
  dias_habiles: number;
  inicio_at: string;
  limite_at: string;
  abierto: boolean;
}

export interface ApelacionT01DTO {
  socio_id: number;
  socio: string;
  numero: number;
  texto: string;
  created_at: string;
}

export interface AdecuacionT01DTO {
  version: number;
  puntos_anteriores: string;
  puntos_nuevos: string;
  socios_anteriores: SocioT01DTO[];
  socios_nuevos: SocioT01DTO[];
  motivos: string;
  reabre_plazo: boolean;
  socios_con_nuevo_plazo: number[];
  autor_legajo: string;
  created_at: string;
}

export interface HistorialT01DTO {
  es_t01: boolean;
  estado: string;
  plazo_dias_vigente: number;
  puntos_vigentes: string;
  involucrados: SocioT01DTO[];
  original: {
    numero_t01: string;
    tipo_accion: 'SANCTION' | 'MERIT';
    emitido_at: string | null;
    solicitante: string;
    snapshot: { puntos?: string; titulo?: string } | null;
  } | null;
  periodos: PeriodoApelacionDTO[];
  apelaciones: ApelacionT01DTO[];
  adecuaciones: AdecuacionT01DTO[];
}

export interface AdecuarT01Payload {
  puntos: number;
  socios: number[];
  motivos: string;
  reabrir_plazo: boolean;
}

export interface PlazoApelacionDTO {
  dias_habiles: number;
  actualizado_at: string | null;
  actualizado_por: string;
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

  listarPorLegajo(legajo: string): Observable<ExpedienteRankingDetalle[]> {
    const params = new HttpParams().set('legajo', legajo);
    return this.http.get<ExpedienteRankingDetalle[]>(
      `${this.apiUrl}/gestion/`,
      { params }
    );
  }

  listarPorSocio(legajo: string): Observable<ExpedienteRankingDetalle[]> {
    const params = new HttpParams().set('legajo', legajo);
    return this.http.get<ExpedienteRankingDetalle[]>(`${this.apiUrl}/por-socio/`, { params });
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

  // --- Endpoints de Eventos, Asistencias y Apercibimientos (Spec 005) ---

  getEventos(params?: Record<string, string>): Observable<any[]> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(k => {
        if (params[k]) {
          httpParams = httpParams.set(k, params[k]);
        }
      });
    }
    return this.http.get<any[]>(`${this.apiUrl}/eventos/`, { params: httpParams });
  }

  getEvento(id: number | string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/eventos/${id}/`);
  }

  crearEvento(payload: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/eventos/`, payload);
  }

  reportarAsistencia(eventoId: number | string, payload: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/eventos/${eventoId}/reportar-asistencia/`, payload);
  }

  obtenerApercibimientosSocio(socioId: number | string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/socios/${socioId}/apercibimientos/`);
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

  descargarEvidencia(expedienteId: number | string, evidenciaId: string, accion: 'descarga' | 'ver' = 'descarga'): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/${expedienteId}/evidencia/${evidenciaId}/`, {
      params: { accion },
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

  obtenerVersionesDescargo(expedienteId: number | string): Observable<DescargoVersionDto[]> {
    return this.http.get<DescargoVersionDto[]>(`${this.apiUrl}/${expedienteId}/descargo/versiones/`);
  }
  obtenerHistorialT01(expedienteId: number | string): Observable<HistorialT01DTO> {
    return this.http.get<HistorialT01DTO>(`${this.apiUrl}/${expedienteId}/t01/historial/`);
  }

  apelarT01(expedienteId: number | string, texto: string): Observable<HistorialT01DTO> {
    return this.http.post<HistorialT01DTO>(`${this.apiUrl}/${expedienteId}/apelacion/`, { texto });
  }

  adecuarT01(expedienteId: number | string, payload: AdecuarT01Payload): Observable<HistorialT01DTO> {
    return this.http.post<HistorialT01DTO>(`${this.apiUrl}/${expedienteId}/adecuaciones/`, payload);
  }

  obtenerPlazoApelacion(): Observable<PlazoApelacionDTO> {
    return this.http.get<PlazoApelacionDTO>(`${this.apiUrl}/parametros/plazo-apelacion/`);
  }

  actualizarPlazoApelacion(diasHabiles: number): Observable<PlazoApelacionDTO> {
    return this.http.put<PlazoApelacionDTO>(`${this.apiUrl}/parametros/plazo-apelacion/`, {
      dias_habiles: diasHabiles
    });
  }

  obtenerVisorExpediente(expedienteId: number | string): Observable<ExpedienteVisorData> {
    return this.http.get<ExpedienteVisorData>(`${this.apiUrl}/${expedienteId}/visor/`);
  }
}
