import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export type InstitutionalMembershipCategory = 'JUNIOR' | 'SENIOR' | 'EX_TRAVELER' | 'UNKNOWN';
export type SocioIdentitySource = 'local' | 'institutional';

export interface OwnPointsBalanceDTO {
  points_balance: number;
}

export interface AppliedPointsEntryDTO {
  movement_id: number;
  applied_points: number;
  historical_case: { id: number; number: string; recorded_at: string | null; state: 'emitido' };
  resolution: { id: number; text: string; regulations: string[] };
  managed_case: { id: number; number: string; state: 'emitido' } | null;
}

export interface OwnPointsHistoryDTO extends OwnPointsBalanceDTO {
  entries: AppliedPointsEntryDTO[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isPositiveId(value: unknown): value is number {
  return typeof value === 'number' && Number.isSafeInteger(value) && value > 0;
}

function isNonemptyText(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function pointsInCents(value: unknown): number | null {
  if (typeof value !== 'number' || !Number.isFinite(value)) { return null; }
  const cents = Math.round(value * 100);
  const tolerance = Number.EPSILON * Math.max(1, Math.abs(value)) * 4;
  return Number.isSafeInteger(cents) && Math.abs(value - cents / 100) <= tolerance ? cents : null;
}

function isRecordedDate(value: unknown): boolean {
  return value === null || (isNonemptyText(value)
    && /^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})?)?$/.test(value)
    && Number.isFinite(Date.parse(value)));
}

function isEmittedCase(value: unknown): value is { id: number; number: string; state: 'emitido' } {
  return isRecord(value) && isPositiveId(value['id']) && isNonemptyText(value['number']) && value['state'] === 'emitido';
}

function isAppliedEntry(value: unknown): value is AppliedPointsEntryDTO {
  if (!isRecord(value)) { return false; }
  const historical = value['historical_case'];
  const resolution = value['resolution'];
  const points = value['applied_points'];
  if (!isEmittedCase(historical) || !isRecord(resolution)) { return false; }
  const recordedAt = (historical as Record<string, unknown>)['recorded_at'];
  const regulations = resolution['regulations'];
  return isPositiveId(value['movement_id'])
    && pointsInCents(points) !== null
    && isRecordedDate(recordedAt)
    && isPositiveId(resolution['id']) && isNonemptyText(resolution['text'])
    && Array.isArray(regulations) && regulations.length > 0 && regulations.every(isNonemptyText)
    && (value['managed_case'] === null || isEmittedCase(value['managed_case']));
}

function parseOwnPointsHistory(response: unknown): OwnPointsHistoryDTO {
  if (!isRecord(response)) { throw new Error('No se pudo confirmar el historial de puntos.'); }
  const points = response['points_balance'];
  const entries = response['entries'];
  const balanceCents = pointsInCents(points);
  if (typeof points !== 'number' || balanceCents === null || !Array.isArray(entries) || !entries.every(isAppliedEntry)) {
    throw new Error('No se pudo confirmar el historial de puntos.');
  }
  const totalCents = entries.reduce((sum, entry) => sum + pointsInCents(entry.applied_points)!, 0);
  if (!Number.isSafeInteger(totalCents) || totalCents !== balanceCents || new Set(entries.map(entry => entry.movement_id)).size !== entries.length) {
    throw new Error('No se pudo confirmar el historial de puntos.');
  }
  return { points_balance: points, entries };
}

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
  points_balance?: number | null;
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

  /** Saldo y resoluciones provienen de una misma lectura del libro mayor. */
  getOwnPointsHistory(): Observable<OwnPointsHistoryDTO> {
    return this.http.get<unknown>(`${this.baseUrl}/me/points-history/`).pipe(map(parseOwnPointsHistory));
  }

  getPointsHistory(socioId: number | string, identitySource?: SocioIdentitySource): Observable<OwnPointsHistoryDTO> {
    const params = identitySource ? new HttpParams().set('identity_source', identitySource) : new HttpParams();
    return this.http.get<unknown>(`${this.baseUrl}/${socioId}/points-history/`, { params }).pipe(map(parseOwnPointsHistory));
  }

  /** El servidor identifica al socio a partir de la sesión autenticada. */
  getOwnPointsBalance(): Observable<OwnPointsBalanceDTO> {
    return this.http.get<unknown>(`${this.baseUrl}/me/points-balance/`).pipe(
      map((response: unknown): OwnPointsBalanceDTO => {
        const points = response && typeof response === 'object'
          ? (response as Record<string, unknown>)['points_balance']
          : undefined;
        if (typeof points !== 'number' || !Number.isFinite(points)) {
          throw new Error('No se pudo confirmar el saldo de puntos.');
        }
        return { points_balance: points };
      })
    );
  }

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
