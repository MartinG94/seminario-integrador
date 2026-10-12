import { RANKING_SOCIOS_MOCK } from './ranking.mock';

describe('Ranking de demostración: clasificación vigente', () => {
  it('declara las cuatro situaciones sin aliases de clasificación antigua', () => {
    expect(new Set(RANKING_SOCIOS_MOCK.map(socio => socio.categoria)))
      .toEqual(new Set(['JUNIOR', 'SENIOR', 'EX_TRAVELER', 'UNKNOWN']));
  });

  it('usa Senior en el caso sintético de tercer año y conserva sus datos de puntos', () => {
    const thirdYear = RANKING_SOCIOS_MOCK.find(socio => socio.legajo === 'FICT-006');
    expect(thirdYear.categoria).toBe('SENIOR');
    expect(thirdYear.id).toBe('mock-06');
    expect(thirdYear.saldo).toBe(5);
    expect(thirdYear.diferencia).toBe(1);
    expect(thirdYear.reconciliado).toBeFalse();
  });
});
