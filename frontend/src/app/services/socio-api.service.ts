import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export type InstitutionalMembershipCategory = 'JUNIOR' | 'SENIOR' | 'EX_TRAVELER' | 'UNKNOWN';
export type SocioIdentitySource = 'local' | 'institutional';

export interface SocioLegajoDTO {
  id: number;
  legajo: string | null;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  category: InstitutionalMembershipCategory;
  category_display: string;
  subcomision: string | null;
  social_year: number | null;
  is_enabled: boolean;
  points_balance?: number;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface SocioListItemDTO {
  id: number;
  legajo: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  category: InstitutionalMembershipCategory;
  category_display: string;
  subcomision: string | null;
}

@Injectable({
  providedIn: 'root'
})
export class SocioApiService {
  private readonly baseUrl = `${environment.apiUrl}/socios`;

  constructor(private http: HttpClient) {}

  /**
   * Busca socios en el padrón con filtros por texto y soporte para paginación (CA1 / CA3).
   */
  searchSocios(query: string, page = 1): Observable<PaginatedResponse<SocioListItemDTO>> {
    let params = new HttpParams().set('page', page.toString());
    if (query && query.trim()) {
      params = params.set('search', query.trim());
    }
    return this.http.get<PaginatedResponse<SocioListItemDTO>>(`${this.baseUrl}/`, { params });
  }

  /**
   * Obtiene los datos detallados del legajo de un socio (T7 / CA2 / CA4).
   */
  getLegajo(socioId: number | string, identitySource?: SocioIdentitySource): Observable<SocioLegajoDTO> {
    const params = identitySource
      ? new HttpParams().set('identity_source', identitySource)
      : new HttpParams();
    return this.http.get<SocioLegajoDTO>(`${this.baseUrl}/${socioId}/legajo/`, { params });
  }
}
