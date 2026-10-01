import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export type TipoAccionT01 = 'SANCTION' | 'MERIT';
export type EstadoT01 = 'DRAFT' | 'ISSUED';

export interface SolicitudT01 {
  id: string;
  estado: EstadoT01;
  solicitante: number;
  destinatario_socio_id: number | null;
  tipo_accion: TipoAccionT01;
  titulo: string;
  causal: string;
  puntos: number | null;
  motivo: string;
  razon: string;
  reglamentos_respaldantes: string[];
  anexo_fecha: string | null;
  anexo_lugar: string;
  anexo_relato: string;
  anexo_testigos: string;
  snapshot_destinatario: unknown;
  snapshot_emitido: unknown;
  numero_expediente: string | null;
  created_at: string;
  updated_at: string;
  issued_at: string | null;
}

export interface SolicitudT01Payload {
  destinatario_socio_id?: number | null;
  tipo_accion: TipoAccionT01;
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
}
