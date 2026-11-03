import { parseReglamentoCite, parseReglamentosList } from './reglamento-format.util';
import { ArticuloReglamentoDTO } from '../services/expediente-api.service';

describe('reglamento-format.util', () => {
  it('debe devolver valores por defecto seguros para string vacio', () => {
    const res = parseReglamentoCite('');
    expect(res.raw).toBe('');
    expect(res.documento).toBe('Normativa');
    expect(res.articulo).toBe('-');
    expect(res.inciso).toBe('-');
    expect(res.citaCorta).toBe('Sin especificar');
    expect(res.cuerpo).toBe('');
  });

  it('debe parsear formato estandar con articulo e inciso', () => {
    const raw = 'Estatuto - Art. 14 Inc. a: Obligacion de asistir a las asambleas ordinarias.';
    const res = parseReglamentoCite(raw);
    expect(res.documento).toBe('Estatuto');
    expect(res.articulo).toBe('14');
    expect(res.inciso).toBe('a');
    expect(res.cuerpo).toBe('Obligacion de asistir a las asambleas ordinarias.');
    expect(res.citaCorta).toBe('Estatuto · Art. 14 Inc. a');
  });

  it('debe parsear formato estandar sin inciso', () => {
    const raw = 'Reglamento Interno - Art. 8: Respeto mutuo y trato cordial.';
    const res = parseReglamentoCite(raw);
    expect(res.documento).toBe('Reglamento Interno');
    expect(res.articulo).toBe('8');
    expect(res.inciso).toBe('-');
    expect(res.cuerpo).toBe('Respeto mutuo y trato cordial.');
    expect(res.citaCorta).toBe('Reglamento Interno · Art. 8');
  });

  it('debe priorizar coincidencia en el catalogo si se suministra', () => {
    const catalogo: ArticuloReglamentoDTO[] = [
      {
        id: 1,
        reglamento: 1,
        titulo: 'Estatuto',
        articulo: 2,
        inciso: 'b',
        cuerpo: 'Texto oficial del catalogo para el art 2 inc b',
        cita_corta: 'Estatuto - Art. 2 Inc. b',
        cita_completa: 'Estatuto - Art. 2 Inc. b: Texto oficial del catalogo para el art 2 inc b'
      }
    ];

    const res = parseReglamentoCite('Estatuto - Art. 2 Inc. b', catalogo);
    expect(res.documento).toBe('Estatuto');
    expect(res.articulo).toBe('2');
    expect(res.inciso).toBe('b');
    expect(res.cuerpo).toBe('Texto oficial del catalogo para el art 2 inc b');
  });

  it('debe procesar lista de reglamentos con parseReglamentosList', () => {
    const lista = [
      'Estatuto - Art. 1: Denominacion AVEIT',
      'Reglamento Interno - Art. 3 Inc. c: Deberes'
    ];
    const res = parseReglamentosList(lista);
    expect(res.length).toBe(2);
    expect(res[0].articulo).toBe('1');
    expect(res[0].inciso).toBe('-');
    expect(res[1].articulo).toBe('3');
    expect(res[1].inciso).toBe('c');
  });
});
