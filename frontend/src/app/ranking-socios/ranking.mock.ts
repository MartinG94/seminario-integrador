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
  },
  {
    id: 'mock-13', legajo: 'FICT-013', nombre: 'Mara', apellido: 'Campoclaro',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: 6.5,
    saldoHistorico: 6.5, saldoPuntajeGeneral: 6.5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-14', legajo: 'FICT-014', nombre: 'Nicolás', apellido: 'Estrellar',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: -4,
    saldoHistorico: -4, saldoPuntajeGeneral: -3.5, diferencia: -0.5, reconciliado: false
  },
  {
    id: 'mock-15', legajo: 'FICT-015', nombre: 'Olivia', apellido: 'Fuenteazul',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 2,
    saldoHistorico: 2, saldoPuntajeGeneral: 2, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-16', legajo: 'FICT-016', nombre: 'Pablo', apellido: 'Granlago',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: 10,
    saldoHistorico: 10, saldoPuntajeGeneral: 9, diferencia: 1, reconciliado: false
  },
  {
    id: 'mock-17', legajo: 'FICT-017', nombre: 'Renata', apellido: 'Horizonte',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: -1,
    saldoHistorico: -1, saldoPuntajeGeneral: -1, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-18', legajo: 'FICT-018', nombre: 'Santiago', apellido: 'Islaclara',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: 4,
    saldoHistorico: 4, saldoPuntajeGeneral: 3.5, diferencia: 0.5, reconciliado: false
  },
  {
    id: 'mock-19', legajo: 'FICT-019', nombre: 'Teresa', apellido: 'Jardínsur',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: -6,
    saldoHistorico: -6, saldoPuntajeGeneral: -6, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-20', legajo: 'FICT-020', nombre: 'Ulises', apellido: 'Lagoverde',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: 7,
    saldoHistorico: 7, saldoPuntajeGeneral: 6, diferencia: 1, reconciliado: false
  },
  {
    id: 'mock-21', legajo: 'FICT-021', nombre: 'Valentina', apellido: 'Monteclaro',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: 0,
    saldoHistorico: 0, saldoPuntajeGeneral: 0, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-22', legajo: 'FICT-022', nombre: 'Walter', apellido: 'Norteluz',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: -8.5,
    saldoHistorico: -8.5, saldoPuntajeGeneral: -8, diferencia: -0.5, reconciliado: false
  },
  {
    id: 'mock-23', legajo: 'FICT-023', nombre: 'Ximena', apellido: 'Olaviento',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 5,
    saldoHistorico: 5, saldoPuntajeGeneral: 5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-24', legajo: 'FICT-024', nombre: 'Yago', apellido: 'Piedraluna',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: 12,
    saldoHistorico: 12, saldoPuntajeGeneral: 11.5, diferencia: 0.5, reconciliado: false
  },
  {
    id: 'mock-25', legajo: 'FICT-025', nombre: 'Zoe', apellido: 'Ríoverde',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: -5,
    saldoHistorico: -5, saldoPuntajeGeneral: -5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-26', legajo: 'FICT-026', nombre: 'Ariel', apellido: 'Senderoclaro',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: 3,
    saldoHistorico: 3, saldoPuntajeGeneral: 2.5, diferencia: 0.5, reconciliado: false
  },
  {
    id: 'mock-27', legajo: 'FICT-027', nombre: 'Bianca', apellido: 'Tierraluz',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 9,
    saldoHistorico: 9, saldoPuntajeGeneral: 9, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-28', legajo: 'FICT-028', nombre: 'Camilo', apellido: 'Umbraverde',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: -9,
    saldoHistorico: -9, saldoPuntajeGeneral: -8, diferencia: -1, reconciliado: false
  },
  {
    id: 'mock-29', legajo: 'FICT-029', nombre: 'Delfina', apellido: 'Valleclaro',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: 4.5,
    saldoHistorico: 4.5, saldoPuntajeGeneral: 4.5, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-30', legajo: 'FICT-030', nombre: 'Emilio', apellido: 'Bosquesur',
    categoria: 'ACTIVO', subcomision: 'Deportes', saldo: -2.5,
    saldoHistorico: -2.5, saldoPuntajeGeneral: -2, diferencia: -0.5, reconciliado: false
  },
  {
    id: 'mock-31', legajo: 'FICT-031', nombre: 'Florencia', apellido: 'Cielonorte',
    categoria: 'PASIVO', subcomision: 'Cómputos', saldo: 11,
    saldoHistorico: 11, saldoPuntajeGeneral: 11, diferencia: 0, reconciliado: true
  },
  {
    id: 'mock-32', legajo: 'FICT-032', nombre: 'Gabriel', apellido: 'Doradoluz',
    categoria: 'ACTIVO', subcomision: 'Eventos', saldo: 1,
    saldoHistorico: 1, saldoPuntajeGeneral: 0.5, diferencia: 0.5, reconciliado: false
  },
  {
    id: 'mock-33', legajo: 'FICT-033', nombre: 'Helena', apellido: 'Estelamar',
    categoria: 'PASIVO', subcomision: 'Cultura', saldo: -11,
    saldoHistorico: -11, saldoPuntajeGeneral: -11, diferencia: 0, reconciliado: true
  }
];
