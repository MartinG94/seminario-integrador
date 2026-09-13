import { Injectable } from '@angular/core';
import { RankingSocio } from '../ranking-socios/ranking-socio.model';
import { RANKING_SOCIOS_MOCK } from '../ranking-socios/ranking.mock';

/**
 * Servicio de SCRUM-38 que centraliza el acceso a los datos del ranking.
 * Actualmente usa mocks; posteriormente será el punto de integración
 * con GET /api/v1/ranking/.
 */
@Injectable({ providedIn: 'root' })
export class RankingService {
  obtenerRanking(): RankingSocio[] {
    return [...RANKING_SOCIOS_MOCK];
  }
}
