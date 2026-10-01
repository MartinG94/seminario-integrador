import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { EMPTY, Observable } from 'rxjs';
import { expand, map, reduce } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export interface PadronSocio {
  socio_id: number;
  legajo: string | null;
  first_name: string;
  last_name: string;
  subcomision: { id: number; name: string } | null;
  is_active: boolean;
}

export interface PadronSociosResponse {
  count: number;
  page: number;
  page_size: number;
  results: PadronSocio[];
}

@Injectable({ providedIn: 'root' })
export class PadronApiService {
  private readonly apiUrl = `${environment.apiUrl}/padron/socios/`;

  constructor(private http: HttpClient) {}

  listarSocios(): Observable<PadronSocio[]> {
    const pageSize = 100;
    const cargarPagina = (page: number): Observable<PadronSociosResponse> => {
      const params = new HttpParams()
        .set('page', page.toString())
        .set('page_size', pageSize.toString())
        .set('is_active', 'true');
      return this.http.get<PadronSociosResponse>(this.apiUrl, { params });
    };

    return cargarPagina(1).pipe(
      expand(response => {
        const nextPage = response.page + 1;
        return response.page * response.page_size < response.count
          ? cargarPagina(nextPage)
          : EMPTY;
      }),
      reduce((socios, response) => socios.concat(response.results), [] as PadronSocio[]),
      map(socios => Array.from(new Map(socios.map(socio => [socio.socio_id, socio])).values()))
    );
  }
}
