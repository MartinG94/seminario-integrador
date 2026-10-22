import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { ResumenCierreDialogComponent, ResumenCierreDialogData } from './resumen-cierre-dialog.component';
import { EventoInstitucional } from '../../../../models/evento.model';

describe('ResumenCierreDialogComponent (T16 / CA3 / CA4 / CA5 / CA9)', () => {
  let component: ResumenCierreDialogComponent;
  let fixture: ComponentFixture<ResumenCierreDialogComponent>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<ResumenCierreDialogComponent>>;

  const mockEventoOrdinaria: EventoInstitucional = {
    id: 1,
    titulo: 'Reunión Ordinaria',
    categoria: 'REUNION',
    tipo: 'ORDINARIA',
    modalidad: 'PRESENCIAL_SEDE',
    fecha_programada: '2026-10-20T18:00:00Z',
    estado: 'EN_CURSO',
    modo_convocatoria: 'GRUPO',
    es_sancionable: true
  };

  const mockEventoExtraordinaria: EventoInstitucional = {
    ...mockEventoOrdinaria,
    id: 2,
    titulo: 'Reunión Extraordinaria Urgente',
    tipo: 'EXTRAORDINARIA'
  };

  const mockEventoAsamblea: EventoInstitucional = {
    ...mockEventoOrdinaria,
    id: 3,
    titulo: 'Asamblea Anual Ordinaria',
    tipo: 'ASAMBLEA'
  };

  const mockEventoActividad: EventoInstitucional = {
    ...mockEventoOrdinaria,
    id: 4,
    titulo: 'Jornada de Mantenimiento',
    categoria: 'ACTIVIDAD',
    tipo: 'MANTENIMIENTO'
  };

  const mockEventoNoSancionable: EventoInstitucional = {
    ...mockEventoOrdinaria,
    id: 5,
    titulo: 'Convocatoria Fuera de Término',
    es_sancionable: false,
    motivo_no_sancionable: 'Preaviso menor a 2 días hábiles'
  };

  const dialogDataMock: ResumenCierreDialogData = {
    evento: mockEventoOrdinaria,
    convocados: [
      { socio_id: 1, socio_nombre: 'Lucas Presente', socio_legajo: '100', estado_asistencia: 'PRESENTE', motivo: 'A tiempo', minutos_tardanza: 0, minutos_retiro_anticipado: 0, metodo_captura: 'MANUAL' },
      { socio_id: 2, socio_nombre: 'Martín Ausente', socio_legajo: '101', estado_asistencia: 'AUSENTE_INJUSTIFICADO', motivo: 'Sin aviso', minutos_tardanza: 0, minutos_retiro_anticipado: 0, metodo_captura: 'MANUAL' },
      { socio_id: 3, socio_nombre: 'Nicolás Tardanza Leve', socio_legajo: '102', estado_asistencia: 'TARDANZA_LEVE', motivo: 'Llegó 20m tarde', minutos_tardanza: 20, minutos_retiro_anticipado: 0, metodo_captura: 'MANUAL' },
      { socio_id: 4, socio_nombre: 'Ignacio Tardanza Grave', socio_legajo: '103', estado_asistencia: 'TARDANZA_GRAVE', motivo: 'Llegó 45m tarde', minutos_tardanza: 45, minutos_retiro_anticipado: 0, metodo_captura: 'MANUAL' }
    ]
  };

  beforeEach(async () => {
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [ResumenCierreDialogComponent],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: dialogDataMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ResumenCierreDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe calcular graduación reglamentaria de faltas para Reunión Ordinaria (CA3 / Art. 85.b)', () => {
    expect(component).toBeTruthy();
    expect(component.actuacionesPrevistas.length).toBe(4);

    const ausente = component.actuacionesPrevistas.find(a => a.socioId === 2);
    expect(ausente?.tipoActuacion).toBe('EXPEDIENTE');
    expect(ausente?.puntos).toBe(-1.0);
    expect(ausente?.norma).toContain('Art. 85.b');

    const leve = component.actuacionesPrevistas.find(a => a.socioId === 3);
    expect(leve?.tipoActuacion).toBe('APERCIBIMIENTO');
    expect(leve?.norma).toContain('Regla 3:1');

    const grave = component.actuacionesPrevistas.find(a => a.socioId === 4);
    expect(grave?.tipoActuacion).toBe('EXPEDIENTE');
    expect(grave?.puntos).toBe(-0.5);
    expect(grave?.norma).toContain('Art. 100.b');
  });

  it('debe previsualizar -1.5 pts para Extraordinaria y -2.0 pts para Asamblea (CA3)', () => {
    // Probar Extraordinaria
    component.data = { ...dialogDataMock, evento: mockEventoExtraordinaria };
    component.totalPresentes = 0;
    component.totalExpedientes = 0;
    component.totalApercibimientos = 0;
    component.calcularActuaciones();

    const ausenteExtra = component.actuacionesPrevistas.find(a => a.socioId === 2);
    expect(ausenteExtra?.puntos).toBe(-1.5);

    // Probar Asamblea
    component.data = { ...dialogDataMock, evento: mockEventoAsamblea };
    component.totalPresentes = 0;
    component.totalExpedientes = 0;
    component.totalApercibimientos = 0;
    component.calcularActuaciones();

    const ausenteAsamblea = component.actuacionesPrevistas.find(a => a.socioId === 2);
    expect(ausenteAsamblea?.puntos).toBe(-2.0);

    // Probar Actividad con puntos_sancion personalizado (-2.5)
    component.data = {
      ...dialogDataMock,
      evento: { ...mockEventoActividad, puntos_sancion: -2.5 }
    };
    component.totalPresentes = 0;
    component.totalExpedientes = 0;
    component.totalApercibimientos = 0;
    component.calcularActuaciones();

    const ausenteActividadCustom = component.actuacionesPrevistas.find(a => a.socioId === 2);
    expect(ausenteActividadCustom?.puntos).toBe(-2.5);
  });

  it('debe previsualizar 0 expedientes si el evento es NO SANCIONABLE (CA1 / CA2)', () => {
    component.data = { ...dialogDataMock, evento: mockEventoNoSancionable };
    component.totalPresentes = 0;
    component.totalExpedientes = 0;
    component.totalApercibimientos = 0;
    component.calcularActuaciones();

    const ausente = component.actuacionesPrevistas.find(a => a.socioId === 2);
    expect(ausente?.tipoActuacion).toBe('NINGUNA');
    expect(ausente?.actuacionLabel).toContain('Sin sanción');
    expect(component.totalExpedientes).toBe(0);
  });

  it('debe cerrar el modal devolviendo true al confirmar y false al cancelar', () => {
    component.confirmar();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(true);

    component.cancelar();
    expect(dialogRefSpy.close).toHaveBeenCalledWith(false);
  });
});
