import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { RankingSocio } from '../ranking-socios/ranking-socio.model';
import { PaginatedResponse, RankingPaginationParams } from '../models/paginated-response.model';
import { environment } from '../../environments/environment';

/**
 * Servicio que centraliza el acceso a los datos del ranking oficial reconciliado.
 * Soporta paginación server-side, ordenamiento y filtros (SCRUM-118 / T-87.10).
 */
@Injectable({ providedIn: 'root' })
export class RankingService {
  private readonly apiUrl = `${environment.apiUrl}/ranking/`;

  constructor(private http: HttpClient) {}

  /**
   * Obtiene la nómina de socios paginada o completa según los parámetros solicitados.
   * Si el backend o un mock devuelve un array plano, lo adapta automáticamente a PaginatedResponse.
   */
  obtenerRanking(params?: RankingPaginationParams): Observable<PaginatedResponse<RankingSocio>> {
    let httpParams = new HttpParams();

    if (params) {
      if (params.page !== undefined && params.page !== null) {
        httpParams = httpParams.set('page', params.page.toString());
      }
      if (params.page_size !== undefined && params.page_size !== null) {
        httpParams = httpParams.set('page_size', params.page_size.toString());
      }
      if (params.ordering) {
        httpParams = httpParams.set('ordering', params.ordering);
      }
      if (params.search) {
        httpParams = httpParams.set('search', params.search);
      }
      if (params.categoria) {
        httpParams = httpParams.set('categoria', params.categoria);
      }
      if (params.subcomision) {
        httpParams = httpParams.set('subcomision', params.subcomision);
      }
      if (params.grupo) {
        httpParams = httpParams.set('grupo', params.grupo);
      }
      if (params.reconciliado !== undefined && params.reconciliado !== null) {
        httpParams = httpParams.set('reconciliado', params.reconciliado.toString());
      }
      if (params.solo_alertas) {
        httpParams = httpParams.set('solo_alertas', 'true');
      }
      if (params.all) {
        httpParams = httpParams.set('all', 'true');
      }
    }

    return this.http
      .get<PaginatedResponse<RankingSocio> | RankingSocio[]>(this.apiUrl, { params: httpParams })
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

  obtenerRankingPaginado(params?: RankingPaginationParams): Observable<PaginatedResponse<RankingSocio>> {
    return this.obtenerRanking(params);
  }
}
