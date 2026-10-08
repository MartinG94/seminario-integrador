import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export type TipoFeriado = 'NACIONAL' | 'PROVINCIAL' | 'INSTITUCIONAL' | 'EXCEPCION';

export interface FeriadoExcepcionDto {
  id?: number;
  calendario_version?: number;
  fecha: string;
  descripcion: string;
  tipo: TipoFeriado;
  tipo_display?: string;
  es_laborable: boolean;
  created_at?: string;
}

export interface CalendarioVersionDto {
  id: number;
  version: number;
  nombre: string;
  vigencia_desde: string;
  vigencia_hasta: string | null;
  activa: boolean;
  motivo_cambio: string;
  creado_por?: number | null;
  creado_por_nombre?: string;
  feriados_count: number;
  created_at: string;
  feriados?: FeriadoExcepcionDto[];
}

export interface CreateCalendarioVersionRequest {
  nombre: string;
  vigencia_desde: string;
  vigencia_hasta?: string | null;
  activa?: boolean;
  motivo_cambio: string;
  clonar_de_version_id?: number | null;
  feriados?: {
    fecha: string;
    descripcion: string;
    tipo?: TipoFeriado;
    es_laborable?: boolean;
  }[];
}

export interface CalcularPlazoRequest {
  start_at: string;
  business_days: number;
  version_id?: number | null;
}

export interface DiaExcluido {
  date: string;
  reason: string;
}

export interface DiaHabilComputado {
  day_number: number;
  date: string;
  weekday: string;
}

export interface CalcularPlazoResponse {
  start_at: string;
  business_days: number;
  deadline: string;
  calendario_version: {
    id: number;
    version: number;
    nombre: string;
    activa?: boolean;
  } | null;
  dias_habiles_computados: DiaHabilComputado[];
  dias_excluidos: DiaExcluido[];
}

@Injectable({
  providedIn: 'root'
})
export class CalendarioApiService {
  private readonly baseUrl = `${environment.apiUrl}/expedientes/calendario`;

  constructor(private http: HttpClient) {}

  getVersiones(): Observable<CalendarioVersionDto[]> {
    return this.http.get<CalendarioVersionDto[]>(`${this.baseUrl}/versiones/`);
  }

  getVersionDetail(id: number): Observable<CalendarioVersionDto> {
    return this.http.get<CalendarioVersionDto>(`${this.baseUrl}/versiones/${id}/`);
  }

  createVersion(payload: CreateCalendarioVersionRequest): Observable<CalendarioVersionDto> {
    return this.http.post<CalendarioVersionDto>(`${this.baseUrl}/versiones/`, payload);
  }

  getFeriados(versionId?: number, year?: number): Observable<FeriadoExcepcionDto[]> {
    let params = new HttpParams();
    if (versionId != null) {
      params = params.set('version_id', versionId.toString());
    }
    if (year != null) {
      params = params.set('year', year.toString());
    }
    return this.http.get<FeriadoExcepcionDto[]>(`${this.baseUrl}/feriados/`, { params });
  }

  addFeriado(payload: Partial<FeriadoExcepcionDto> & { version_id?: number }): Observable<FeriadoExcepcionDto> {
    return this.http.post<FeriadoExcepcionDto>(`${this.baseUrl}/feriados/`, payload);
  }

  calcularPlazo(payload: CalcularPlazoRequest): Observable<CalcularPlazoResponse> {
    return this.http.post<CalcularPlazoResponse>(`${this.baseUrl}/calcular-plazo/`, payload);
  }
}
