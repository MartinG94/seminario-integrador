/**
 * Modelo del Ranking Oficial de SCRUM-38.
 * `saldo` representa por ahora el saldo oficial utilizado por el frontend.
 * Los campos saldoHistorico, saldoPuntajeGeneral, diferencia y reconciliado
 * son provisionales: SCRUM-38 exige reconciliación, pero todavía no está
 * definido cómo GET /api/v1/ranking/ expondrá esa información.
 * Estos cuatro campos deberán revisarse cuando se cierre el contrato del backend.
 */
export interface RankingSocio {
  id: string;
  legajo: string;
  nombre: string;
  apellido: string;
  categoria: 'ACTIVO' | 'PASIVO';
  subcomision: string;
  saldo: number;

  saldoHistorico?: number;
  saldoPuntajeGeneral?: number;
  diferencia?: number;
  reconciliado?: boolean;
}
