import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MisExpedientesComponent } from './mis-expedientes.component';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';

describe('MisExpedientesComponent', () => {
  let component: MisExpedientesComponent;
  let fixture: ComponentFixture<MisExpedientesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [MisExpedientesComponent],
      providers: [TribunalDataService]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MisExpedientesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  describe('Coloreado de Puntos Totales', () => {
    it('retorna clase verde para puntos >= 0', () => {
      expect(component.getColorClasePuntos(10)).toBe('puntos-verde');
      expect(component.getColorClasePuntos(0)).toBe('puntos-verde');
      expect(component.getHeaderClassPuntos(0)).toBe('card-header-success');
    });

    it('retorna clase gris para puntos < 0 y >= -7', () => {
      expect(component.getColorClasePuntos(-1)).toBe('puntos-gris');
      expect(component.getColorClasePuntos(-7)).toBe('puntos-gris');
      expect(component.getHeaderClassPuntos(-5)).toBe('card-header-secondary');
    });

    it('retorna clase amarillo para puntos < -7 y >= -9', () => {
      expect(component.getColorClasePuntos(-7.5)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-8)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-9)).toBe('puntos-amarillo');
      expect(component.getHeaderClassPuntos(-8)).toBe('card-header-warning');
    });

    it('retorna clase rojo para puntos < -9', () => {
      expect(component.getColorClasePuntos(-9.5)).toBe('puntos-rojo');
      expect(component.getColorClasePuntos(-15)).toBe('puntos-rojo');
      expect(component.getHeaderClassPuntos(-10)).toBe('card-header-danger');
    });
  });

  describe('Ordenamiento de tabla', () => {
    const mockExpedientes: Expediente[] = [
      {
        id: '1',
        numero: 'EXP-2026-002',
        tipo: 'falta',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Falta a reunión',
        subcomision: 'Deportes',
        puntos: -2,
        estado: 'creado',
        fechaCreacion: '2026-03-01',
        horasRestantes: 72
      },
      {
        id: '2',
        numero: 'EXP-2026-001',
        tipo: 'merito',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Reconocimiento',
        subcomision: 'Cultura',
        puntos: 5,
        estado: 'emitido',
        fechaCreacion: '2026-02-15',
        horasRestantes: 0
      }
    ];

    beforeEach(() => {
      component.misExpedientes = [...mockExpedientes];
    });

    it('ordena ascendentemente por defecto', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-001');
      expect(ordenados[1].numero).toBe('EXP-2026-002');
    });

    it('invierte orden al hacer click en la misma columna', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      component.cambiarOrden('numero');
      expect(component.ordenAscendente).toBeFalse();
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-002');
      expect(ordenados[1].numero).toBe('EXP-2026-001');
    });

    it('cambia columna y reinicia orden a ascendente', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = false;
      component.cambiarOrden('motivo');
      expect(component.columnaOrden).toBe('motivo');
      expect(component.ordenAscendente).toBeTrue();
    });
  });

  describe('Temporizador Dinámico y Plazo Preclusivo (S3-02 / CA3)', () => {
    const expEnPlazo: Expediente = {
      id: 'EXP-01',
      numero: 'EXP-001/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-08',
      horasRestantes: 48,
      plazoInicioAt: '2026-10-08T18:00:00-03:00',
      plazoLimiteAt: '2026-10-15T18:00:00-03:00',
      descargoPresentado: false
    };

    it('formatea la fecha y hora exacta del vencimiento (getDeadlineLabel)', () => {
      const label = component.getDeadlineLabel(expEnPlazo);
      expect(label).toContain('Vence:');
      expect(label).toContain('15/10/2026');
      expect(label).toContain('18:00 hs');
    });

    it('calcula el countdown dinámico restante cuando está en plazo (getCountdownLabel)', () => {
      // Fijamos ahoraMs a 2 días y 4 horas antes del vencimiento
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const countdown = component.getCountdownLabel(expEnPlazo);
      expect(countdown).toBe('2d 04h 15m restantes');
      expect(component.esPlazoVencido(expEnPlazo)).toBeFalse();
    });

    it('detecta plazo vencido y muestra "Plazo expirado" al superar el límite', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs + 1000; // 1 segundo después

      expect(component.esPlazoVencido(expEnPlazo)).toBeTrue();
      expect(component.getCountdownLabel(expEnPlazo)).toBe('Plazo expirado');
    });

    it('formatea countdown compacto para el badge (getCompactCountdownLabel)', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const compact = component.getCompactCountdownLabel(expEnPlazo);
      expect(compact).toBe('2d 04h');
      expect(component.getEstadoLabel('justificando', expEnPlazo)).toBe('Justificando · 2d 04h');
    });

    it('abre y cierra el modal de detalle del expediente', () => {
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();

      component.abrirModalDetalle(expEnPlazo);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.expedienteDetalle).toBe(expEnPlazo);

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();
    });

    it('limpia el timer subscription en ngOnDestroy para evitar memory leaks', () => {
      component.ngOnDestroy();
      expect((component as any).tickerSub).toBeNull();
    });
  });

  describe('Gestión de Justificativos y Auditoría en Modal Detalle', () => {
    const expConDescargo: Expediente = {
      id: 'EXP-99',
      numero: 'EXP-099/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'revision_resolucion',
      fechaCreacion: '2026-10-01',
      horasRestantes: 0,
      descargoPresentado: true,
      descargo: {
        tipo: 'T02_CERTIFICADO',
        causal: 'Examen Académico Universitario en UTN FRC',
        archivo: 'comprobante.pdf',
        texto: 'Certificado de examen rendido',
        fecha: '2026-10-01'
      },
      logsDescargo: [
        {
          operacion: 'CREACION',
          accionLabel: 'Añadir Justificativo',
          usuario: 'Lucas Gastiaburu (Legajo 74907)',
          timestamp: '01/10/2026 10:00 hs',
          detalle: 'Modalidad T02 (Certificado)'
        }
      ]
    };

    it('abre el modal de añadir justificativo en modo creación', () => {
      const expSinDescargo: Expediente = { ...expConDescargo, descargo: undefined, logsDescargo: [] };
      component.abrirModalDescargo(expSinDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeFalse();
      expect(component.expedienteSeleccionado).toBe(expSinDescargo);
      expect(component.nombreArchivo).toBe('');
    });

    it('abre el modal de editar justificativo precargando los datos existentes', () => {
      component.abrirModalEditarDescargo(expConDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeTrue();
      expect(component.tipoDescargo).toBe('T02_CERTIFICADO');
      expect(component.causalSeleccionada).toBe('Examen Académico Universitario en UTN FRC');
      expect(component.nombreArchivo).toBe('comprobante.pdf');
      expect(component.relatoTexto).toBe('Certificado de examen rendido');
    });

    it('elimina el justificativo al confirmar en el diálogo', () => {
      spyOn(window, 'confirm').and.returnValue(true);
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(dataSpy).toHaveBeenCalledWith('EXP-99', jasmine.objectContaining({ nombre: jasmine.any(String) }));
    });

    it('no elimina el justificativo si el usuario cancela la confirmación', () => {
      spyOn(window, 'confirm').and.returnValue(false);
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(dataSpy).not.toHaveBeenCalled();
    });

    it('asigna clases badge adecuadas a cada tipo de operación', () => {
      expect(component.getBadgeClaseOperacion('CREACION')).toBe('badge-success');
      expect(component.getBadgeClaseOperacion('EDICION')).toBe('badge-info');
      expect(component.getBadgeClaseOperacion('ELIMINACION')).toBe('badge-danger');
    });
  });

  describe('Bloqueo de scroll al abrir modales', () => {
    const mockExpediente: Expediente = {
      id: 'EXP-101',
      numero: 'EXP-2026-101',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-01',
      horasRestantes: 72
    };

    afterEach(() => {
      document.body.classList.remove('modal-open');
      document.body.style.removeProperty('overflow');
      document.documentElement.style.removeProperty('overflow');
    });

    it('bloquea el scroll del fondo al abrir el modal de detalle y lo restaura al cerrar', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.documentElement.style.overflow).toBe('hidden');

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
      expect(document.documentElement.style.overflow).toBe('');
    });

    it('bloquea el scroll al abrir el modal de justificación T02/T03 y lo restaura al cerrar', () => {
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });

    it('mantiene el bloqueo de scroll activo si el modal de detalle sigue abierto al cerrar el de justificación', () => {
      component.abrirModalDetalle(mockExpediente);
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      // Cerrar solo el de justificación
      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.body.classList.contains('modal-open')).toBeTrue();

      // Cerrar finalmente el de detalle
      component.cerrarModalDetalle();
      expect(document.body.style.overflow).toBe('');
      expect(document.body.classList.contains('modal-open')).toBeFalse();
    });

    it('limpia las clases y estilos de scroll al destruir el componente', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.ngOnDestroy();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });
  });
});
