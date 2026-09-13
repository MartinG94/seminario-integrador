/**
 * Datos exclusivamente ficticios para desarrollar SCRUM-38 mientras no esté
 * disponible GET /api/v1/ranking/. Deberán reemplazarse por la integración HTTP.
 * Se simula saldo = saldoHistorico mientras SCRUM-34 define la fuente definitiva.
 */
import { RankingSocio } from './ranking-socio.model';

export const RANKING_SOCIOS_MOCK: RankingSocio[] = [
  {
    id: 'mock-01', legajo: 'FICT-001', nombre: 'Alma', apellido: 'Brisalta',
    categoria: 'ACTIVO', subcomision: 'Cultura', saldo: 5,
    saldoHistorico: 5, saldoPuntajeGeneral: 5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-02', legajo: 'FICT-002', nombre: 'Bruno', apellido: 'Lunaverde',
    categoria: 'PASIVO', subcomision: 'Deportes', saldo: -2,
    saldoHistorico: -2, saldoPuntajeGeneral: -1.5, diferencia: -0.5, reconciliado: false
  },
  {
    id: 'mock-03', legajo: 'FICT-003', nombre: 'Celia', apellido: 'Nubeclara',
    categoria: 'ACTIVO', subcomision: 'Cómputos', saldo: 0,
    saldoHistorico: 0, saldoPuntajeGeneral: 0, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-04', legajo: 'FICT-004', nombre: 'Dante', apellido: 'Ríoluz',
    categoria: 'PASIVO', subcomision: 'Eventos', saldo: 3.5,
    saldoHistorico: 3.5, saldoPuntajeGeneral: 3, diferencia: 0.5, reconciliado: false
  },
  {
    id: 'mock-05', legajo: 'FICT-005', nombre: 'Eva', apellido: 'Solbruma',
    categoria: 'ACTIVO', subcomision: 'Cultura', saldo: -7,
    saldoHistorico: -7, saldoPuntajeGeneral: -7, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-06', legajo: 'FICT-006', nombre: 'Felipe', apellido: 'Valleazul',
    categoria: 'PASIVO', subcomision: 'Deportes', saldo: 5,
    saldoHistorico: 5, saldoPuntajeGeneral: 4, diferencia: 1, reconciliado: false
  },
  {
    id: 'mock-07', legajo: 'FICT-007', nombre: 'Gala', apellido: 'Brisalta',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 5,
    saldoHistorico: 5, saldoPuntajeGeneral: 5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-08', legajo: 'FICT-008', nombre: 'Hugo', apellido: 'Montenube',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: -10.5,
    saldoHistorico: -10.5, saldoPuntajeGeneral: -9.5, diferencia: -1, reconciliado: false
  },
  {
    id: 'mock-09', legajo: 'FICT-009', nombre: 'Iris', apellido: 'Pradoluna',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: 1.5,
    saldoHistorico: 1.5, saldoPuntajeGeneral: 1.5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-10', legajo: 'FICT-010', nombre: 'Julián', apellido: 'Vientoclaro',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: -0.5,
    saldoHistorico: -0.5, saldoPuntajeGeneral: 0, diferencia: -0.5, reconciliado: false
  },
  {
    id: 'mock-11', legajo: 'FICT-011', nombre: 'Kiara', apellido: 'Marsereno',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 8,
    saldoHistorico: 8, saldoPuntajeGeneral: 8, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-12', legajo: 'FICT-012', nombre: 'León', apellido: 'Bosqueluz',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: -3,
    saldoHistorico: -3, saldoPuntajeGeneral: -4, diferencia: 1, reconciliado: false
  }
];
