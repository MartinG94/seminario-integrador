import {
  TrackByUtils,
  trackById,
  trackBySocio,
  trackByExpediente,
  trackByValue
} from './track-by.util';

describe('TrackByUtils', () => {
  let instance: TrackByUtils;

  beforeEach(() => {
    instance = new TrackByUtils();
  });

  describe('byId', () => {
    it('debe retornar item.id cuando existe como número o string', () => {
      expect(TrackByUtils.byId(0, { id: 42 })).toBe(42);
      expect(TrackByUtils.byId(1, { id: 'socio-42' })).toBe('socio-42');
    });

    it('debe preservar item.id cuando su valor es 0', () => {
      expect(TrackByUtils.byId(5, { id: 0 })).toBe(0);
    });

    it('debe retornar el índice si item es nulo o indefinido', () => {
      expect(TrackByUtils.byId(2, null)).toBe(2);
      expect(TrackByUtils.byId(3, undefined)).toBe(3);
    });

    it('debe retornar el índice si el objeto no tiene propiedad id o es nula/indefinida', () => {
      expect(TrackByUtils.byId(4, { nombre: 'Test' })).toBe(4);
      expect(TrackByUtils.byId(5, { id: null })).toBe(5);
      expect(TrackByUtils.byId(6, { id: undefined })).toBe(6);
    });

    it('debe retornar el índice si item es un tipo primitivo sin id', () => {
      expect(TrackByUtils.byId(7, 'cadena')).toBe(7);
      expect(TrackByUtils.byId(8, 123)).toBe(8);
    });
  });

  describe('bySocio', () => {
    it('debe priorizar nroSocio sobre id y legajo', () => {
      const socio = { nroSocio: 101, id: 202, legajo: '303' };
      expect(TrackByUtils.bySocio(0, socio)).toBe(101);
    });

    it('debe priorizar nro_socio si nroSocio no está presente', () => {
      const socio = { nro_socio: 105, id: 202, legajo: '303' };
      expect(TrackByUtils.bySocio(0, socio)).toBe(105);
    });

    it('debe retornar id si nroSocio no está definido', () => {
      const socio = { id: 202, legajo: '303' };
      expect(TrackByUtils.bySocio(0, socio)).toBe(202);
    });

    it('debe retornar legajo si nroSocio e id no están definidos', () => {
      const socio = { legajo: '74907' };
      expect(TrackByUtils.bySocio(1, socio)).toBe('74907');
    });

    it('debe soportar valores numéricos iguales a 0', () => {
      expect(TrackByUtils.bySocio(2, { nroSocio: 0 })).toBe(0);
      expect(TrackByUtils.bySocio(3, { id: 0 })).toBe(0);
    });

    it('debe retornar el índice si item es nulo o indefinido', () => {
      expect(TrackByUtils.bySocio(4, null)).toBe(4);
      expect(TrackByUtils.bySocio(5, undefined)).toBe(5);
    });

    it('debe retornar el índice si ninguna propiedad identificadora está presente', () => {
      expect(TrackByUtils.bySocio(6, { nombre: 'Juan' })).toBe(6);
      expect(TrackByUtils.bySocio(7, 'socio-primitivo')).toBe(7);
    });
  });

  describe('byExpediente', () => {
    it('debe priorizar numero sobre id y numero_expediente', () => {
      const exp = { numero: 'EXP-001/2026', id: 50, numero_expediente: 'EXP-OLD' };
      expect(TrackByUtils.byExpediente(0, exp)).toBe('EXP-001/2026');
    });

    it('debe retornar id si numero no está definido', () => {
      const exp = { id: 75, numero_expediente: 'EXP-002/2026' };
      expect(TrackByUtils.byExpediente(0, exp)).toBe(75);
    });

    it('debe retornar expediente_id si numero e id no están definidos', () => {
      const exp = { expediente_id: 88, numero_expediente: 'EXP-003/2026' };
      expect(TrackByUtils.byExpediente(0, exp)).toBe(88);
    });

    it('debe retornar numero_expediente si numero e id no están definidos', () => {
      const exp = { numero_expediente: 'EXP-003/2026' };
      expect(TrackByUtils.byExpediente(1, exp)).toBe('EXP-003/2026');
    });

    it('debe retornar numeroExpediente en camelCase si los anteriores no están presentes', () => {
      const exp = { numeroExpediente: 'EXP-004/2026' };
      expect(TrackByUtils.byExpediente(2, exp)).toBe('EXP-004/2026');
    });

    it('debe soportar valor numérico 0 en numero o id', () => {
      expect(TrackByUtils.byExpediente(3, { numero: 0 })).toBe(0);
      expect(TrackByUtils.byExpediente(4, { id: 0 })).toBe(0);
    });

    it('debe retornar el índice si item es nulo o indefinido', () => {
      expect(TrackByUtils.byExpediente(5, null)).toBe(5);
      expect(TrackByUtils.byExpediente(6, undefined)).toBe(6);
    });

    it('debe retornar el índice si ninguna propiedad identificadora está presente', () => {
      expect(TrackByUtils.byExpediente(7, { estado: 'iniciado' })).toBe(7);
      expect(TrackByUtils.byExpediente(8, 'expediente-invalido')).toBe(8);
    });
  });

  describe('byValue', () => {
    it('debe retornar el valor primitivo exacto para strings, números y booleanos', () => {
      expect(TrackByUtils.byValue(0, 'ACTIVO')).toBe('ACTIVO');
      expect(TrackByUtils.byValue(1, '')).toBe('');
      expect(TrackByUtils.byValue(2, 42)).toBe(42);
      expect(TrackByUtils.byValue(3, 0)).toBe(0);
      expect(TrackByUtils.byValue(4, true)).toBe(true);
      expect(TrackByUtils.byValue(5, false)).toBe(false);
    });

    it('debe retornar la referencia de objeto si item es un objeto', () => {
      const obj = { key: 'value' };
      expect(TrackByUtils.byValue(0, obj)).toBe(obj);
    });

    it('debe retornar el índice si el valor es null o undefined', () => {
      expect(TrackByUtils.byValue(10, null)).toBe(10);
      expect(TrackByUtils.byValue(11, undefined)).toBe(11);
    });
  });

  describe('Métodos de instancia delegados', () => {
    it('debe delegar byId a la implementación estática', () => {
      expect(instance.byId(0, { id: 99 })).toBe(99);
      expect(instance.byId(5, null)).toBe(5);
    });

    it('debe delegar bySocio a la implementación estática', () => {
      expect(instance.bySocio(0, { nroSocio: 88 })).toBe(88);
      expect(instance.bySocio(4, null)).toBe(4);
    });

    it('debe delegar byExpediente a la implementación estática', () => {
      expect(instance.byExpediente(0, { numero: 'EXP-10' })).toBe('EXP-10');
      expect(instance.byExpediente(6, null)).toBe(6);
    });

    it('debe delegar byValue a la implementación estática', () => {
      expect(instance.byValue(0, 'item-val')).toBe('item-val');
      expect(instance.byValue(3, null)).toBe(3);
    });
  });

  describe('Funciones standalone exportadas', () => {
    it('trackById debe coincidir con TrackByUtils.byId', () => {
      expect(trackById(0, { id: 123 })).toBe(123);
    });

    it('trackBySocio debe coincidir con TrackByUtils.bySocio', () => {
      expect(trackBySocio(0, { legajo: '74907' })).toBe('74907');
    });

    it('trackByExpediente debe coincidir con TrackByUtils.byExpediente', () => {
      expect(trackByExpediente(0, { numero: 'EXP-001' })).toBe('EXP-001');
    });

    it('trackByValue debe coincidir con TrackByUtils.byValue', () => {
      expect(trackByValue(0, 'test')).toBe('test');
    });
  });
});
