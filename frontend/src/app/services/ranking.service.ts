import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { RankingSocio } from '../ranking-socios/ranking-socio.model';

/**
 * Servicio de SCRUM-38 que centraliza el acceso a los datos del ranking.
 * Consume el endpoint real del backend.
 */
@Injectable({ providedIn: 'root' })
export class RankingService {
  private readonly apiUrl = 'http://127.0.0.1:8000/api/v1/ranking/';

  constructor(private http: HttpClient) {}

  obtenerRanking(): Observable<RankingSocio[]> {
    return this.http.get<RankingSocio[]>(this.apiUrl);
  }
}