import { TestBed } from '@angular/core/testing';
import { ManualAttendanceStrategy } from './manual-attendance.strategy';
import { BiometricAttendanceStrategy } from './biometric-attendance.strategy';
import { AttendanceContextService } from './attendance-context.service';
import { ConvocadoAsistenciaDTO } from '../models/eventos-asistencia.models';

describe('Patrón Strategy de Asistencia (T12)', () => {
  let manual: ManualAttendanceStrategy;
  let biometric: BiometricAttendanceStrategy;
  let context: AttendanceContextService;

  const mockSocio: ConvocadoAsistenciaDTO = {
    socio_id: 101,
    socio_nombre: 'Lucas Gastiaburu',
    socio_legajo: '74907',
    estado_asistencia: 'PRESENTE',
    motivo: 'En sede',
    minutos_tardanza: 0,
    minutos_retiro_anticipado: 0,
    metodo_captura: 'MANUAL'
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ManualAttendanceStrategy, BiometricAttendanceStrategy, AttendanceContextService]
    });
    manual = TestBed.inject(ManualAttendanceStrategy);
    biometric = TestBed.inject(BiometricAttendanceStrategy);
    context = TestBed.inject(AttendanceContextService);
  });

  describe('ManualAttendanceStrategy', () => {
    it('debe tener tipo MANUAL', () => {
      expect(manual.tipo).toBe('MANUAL');
      expect(manual.nombre).toContain('Manual');
    });

    it('capturar debe registrar el estado actual del socio', () => {
      const res = manual.capturar(mockSocio);
      expect(res.socioId).toBe(101);
      expect(res.estado).toBe('PRESENTE');
      expect(res.motivo).toBe('En sede');
      expect(res.horaRegistro).toBeDefined();
    });

    it('capturar debe registrar tardanza si la hora supera la tolerancia', () => {
      const horaInicio = new Date(Date.now() - 35 * 60000); // 35 min atras
      const res = manual.capturar(mockSocio, horaInicio, 15);
      expect(res.minutosTardanza).toBeGreaterThanOrEqual(35);
    });
  });

  describe('BiometricAttendanceStrategy', () => {
    it('debe tener tipo BIOMETRICO', () => {
      expect(biometric.tipo).toBe('BIOMETRICO');
      expect(biometric.nombre).toContain('Biométrica');
    });

    it('capturar debe registrar PRESENTE si la hora está dentro de la tolerancia', () => {
      const horaInicio = new Date(Date.now() - 5 * 60000); // 5 min atras
      const res = biometric.capturar({ ...mockSocio, motivo: '' }, horaInicio, 15);
      expect(res.estado).toBe('PRESENTE');
      expect(res.minutosTardanza).toBeGreaterThanOrEqual(5);
    });

    it('capturar debe clasificar como TARDANZA_LEVE entre 15 y 30 minutos', () => {
      const horaInicio = new Date(Date.now() - 20 * 60000); // 20 min atras
      const res = biometric.capturar({ ...mockSocio, motivo: '' }, horaInicio, 15);
      expect(res.estado).toBe('TARDANZA_LEVE');
      expect(res.motivo).toContain('tardanza leve');
    });

    it('capturar debe clasificar como TARDANZA_GRAVE si supera los 30 minutos', () => {
      const horaInicio = new Date(Date.now() - 40 * 60000); // 40 min atras
      const res = biometric.capturar({ ...mockSocio, motivo: '' }, horaInicio, 15);
      expect(res.estado).toBe('TARDANZA_GRAVE');
      expect(res.motivo).toContain('gravedad estatutaria');
    });
  });

  describe('AttendanceContextService', () => {
    it('debe inicializarse por defecto con la estrategia MANUAL', () => {
      expect(context.currentStrategy.tipo).toBe('MANUAL');
    });

    it('setStrategy debe cambiar a BIOMETRICO y emitir por el observable', (done) => {
      context.setStrategy('BIOMETRICO');
      expect(context.currentStrategy.tipo).toBe('BIOMETRICO');

      context.currentStrategy$.subscribe(strat => {
        expect(strat.tipo).toBe('BIOMETRICO');
        done();
      });
    });

    it('setStrategy debe permitir volver a MANUAL', () => {
      context.setStrategy('BIOMETRICO');
      expect(context.currentStrategy.tipo).toBe('BIOMETRICO');
      context.setStrategy('MANUAL');
      expect(context.currentStrategy.tipo).toBe('MANUAL');
    });
  });
});
