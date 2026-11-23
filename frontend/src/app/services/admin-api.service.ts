import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export type CategoriaParametro = 'PLAZOS' | 'UMBRALES' | 'CORREOS' | 'ADJUNTOS';
export type TipoParametro = 'INTEGER' | 'DECIMAL' | 'BOOLEAN' | 'EMAIL';
export type ValorParametro = number | string | boolean | null;

export interface ParametroSistemaDTO {
  clave: string;
  categoria: CategoriaParametro;
  etiqueta: string;
  descripcion: string;
  tipo: TipoParametro;
  unidad: string;
  editable: boolean;
  minimo: string | null;
  maximo: string | null;
  valor: ValorParametro;
  valor_inicial: ValorParametro;
  actualizado_at: string | null;
  actualizado_por: string;
}

export interface CambioParametroDTO {
  valor: ValorParametro;
  valor_anterior: ValorParametro;
  autor: string;
  created_at: string;
}

export interface MiembroTribunalDTO {
  id: number;
  numero_socio: number | null;
  legajo: string;
  last_name: string;
  first_name: string;
  social_year: number;
  email: string;
  subcomision: string | null;
}

export interface CandidatoTribunalDTO {
  id: number;
  numero_socio: number | null;
  last_name: string;
  first_name: string;
  social_year: number;
  subcomision: string | null;
}

export interface LimitesAdjuntosDTO {
  tamano_maximo_mb: number;
  cantidad_maxima: number;
}

@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly adminUrl = `${environment.apiUrl}/admin`;
  private readonly parametrosUrl = `${environment.apiUrl}/parametros`;

  constructor(private http: HttpClient) {}

  listarParametros(): Observable<ParametroSistemaDTO[]> {
    return this.http.get<ParametroSistemaDTO[]>(`${this.adminUrl}/parametros/`);
  }

  actualizarParametro(clave: string, valor: ValorParametro): Observable<ParametroSistemaDTO> {
    return this.http.put<ParametroSistemaDTO>(`${this.adminUrl}/parametros/${clave}/`, { valor });
  }

  historialParametro(clave: string): Observable<CambioParametroDTO[]> {
    return this.http.get<CambioParametroDTO[]>(`${this.adminUrl}/parametros/${clave}/historial/`);
  }

  listarMiembrosTribunal(): Observable<MiembroTribunalDTO[]> {
    return this.http.get<MiembroTribunalDTO[]>(`${this.adminUrl}/usuarios-td/`);
  }

  buscarCandidatosTribunal(termino: string): Observable<CandidatoTribunalDTO[]> {
    return this.http.get<CandidatoTribunalDTO[]>(`${this.adminUrl}/usuarios-td/candidatos/`, {
      params: new HttpParams().set('search', termino)
    });
  }

  asignarMiembroTribunal(socioId: number): Observable<MiembroTribunalDTO> {
    return this.http.post<MiembroTribunalDTO>(`${this.adminUrl}/usuarios-td/`, { socio_id: socioId });
  }

  revocarMiembroTribunal(socioId: number): Observable<void> {
    return this.http.delete<void>(`${this.adminUrl}/usuarios-td/${socioId}/`);
  }

  obtenerLimitesAdjuntos(): Observable<LimitesAdjuntosDTO> {
    return this.http.get<LimitesAdjuntosDTO>(`${this.parametrosUrl}/adjuntos/`);
  }
}
