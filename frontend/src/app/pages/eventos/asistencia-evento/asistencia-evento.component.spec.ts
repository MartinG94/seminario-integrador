import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';
import { AsistenciaEventoComponent } from './asistencia-evento.component';
import { EventoService } from '../../../services/evento.service';
import { TribunalDataService } from '../../../services/tribunal-data.service';
import { AttendanceContextService } from '../../../eventos-asistencia/strategies/attendance-context.service';
import { BiometricAttendanceStrategy } from '../../../eventos-asistencia/strategies/biometric-attendance.strategy';
import { NotificationService } from '../../../services/notification.service';
import { EventoInstitucional } from '../../../models/evento.model';

describe('AsistenciaEventoComponent (T15 / CA10)', () => {
  let component: AsistenciaEventoComponent;
  let fixture: ComponentFixture<AsistenciaEventoComponent>;
  let eventoServiceSpy: jasmine.SpyObj<EventoService>;
  let notificationSpy: jasmine.SpyObj<NotificationService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;

  const mockEvento: EventoInstitucional = {
    id: 1,
    titulo: 'Reunión Ordinaria Consejo Directivo',
    categoria: 'REUNION',
    tipo: 'ORDINARIA',
    modalidad: 'PRESENCIAL_SEDE',
    fecha_programada: '2026-10-14T18:00:00Z',
    estado: 'EN_CURSO',
    modo_convocatoria: 'GRUPO',
    es_sancionable: true
  };

  const mockAsistencias = [
    { socio_id: 101, socio_nombre: 'Lucas Gastiaburu', socio_legajo: '74907', estado_asistencia: 'PRESENTE' as const, motivo: 'En sede' },
    { socio_id: 102, socio_nombre: 'Lucas Guillén', socio_legajo: '85194', estado_asistencia: 'AUSENTE_INJUSTIFICADO' as const, motivo: 'Sin aviso' }
  ];

  beforeEach(async () => {
    eventoServiceSpy = jasmine.createSpyObj('EventoService', [
      'getEventos',
      'getAsistencias',
      'registrarAsistenciasBulk',
      'procesarAsistencias'
    ]);
    notificationSpy = jasmine.createSpyObj('NotificationService', ['success', 'error', 'info', 'warning']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);

    eventoServiceSpy.getEventos.and.returnValue(of([mockEvento]));
    eventoServiceSpy.getAsistencias.and.returnValue(of(mockAsistencias));

    await TestBed.configureTestingModule({
      imports: [FormsModule, HttpClientTestingModule, RouterTestingModule],
      declarations: [AsistenciaEventoComponent],
      providers: [
        { provide: EventoService, useValue: eventoServiceSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: MatDialog, useValue: dialogSpy },
        AttendanceContextService,
        BiometricAttendanceStrategy,
        TribunalDataService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AsistenciaEventoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe inicializar y cargar la lista de eventos y convocados', () => {
    expect(component).toBeTruthy();
    expect(component.eventoActivo).toEqual(mockEvento);
    expect(component.convocados.length).toBe(2);
    expect(eventoServiceSpy.getEventos).toHaveBeenCalled();
    expect(eventoServiceSpy.getAsistencias).toHaveBeenCalledWith(1);
  });

  it('debe calcular métricas de presentes, ausentes y tardanzas', () => {
    expect(component.totalPresentes).toBe(1);
    expect(component.totalAusentes).toBe(1);
    expect(component.totalTardanzas).toBe(0);
  });

  it('debe filtrar convocados por texto o estado', () => {
    component.filtroTexto = '85194';
    expect(component.convocadosFiltrados.length).toBe(1);
    expect(component.convocadosFiltrados[0].socio_legajo).toBe('85194');

    component.filtroTexto = '';
    component.filtroEstado = 'PRESENTE';
    expect(component.convocadosFiltrados.length).toBe(1);
    expect(component.convocadosFiltrados[0].estado_asistencia).toBe('PRESENTE');
  });

  it('debe sugerir motivo circunstanciado al cambiar de estado (CA10)', () => {
    const socio = component.convocados[0];
    socio.estado_asistencia = 'TARDANZA_LEVE';
    socio.motivo = '';
    component.onCambiarEstadoSocio(socio);
    expect(socio.motivo).toContain('Tardanza leve');
  });

  it('debe alternar la estrategia de captura (Manual vs Biométrico)', () => {
    component.cambiarEstrategia('BIOMETRICO');
    expect(component.estrategiaActual).toBe('BIOMETRICO');
    expect(notificationSpy.info).toHaveBeenCalledWith('Estrategia cambiada a modo Biométrico.');

    component.cambiarEstrategia('MANUAL');
    expect(component.estrategiaActual).toBe('MANUAL');
  });

  it('simularHuellaSocio debe marcar asistencia biométrica con timestamp y audio', fakeAsync(() => {
    const socio = component.convocados[1]; // ausente
    component.simularHuellaSocio(socio);

    tick(500);

    expect(socio.metodo_captura).toBe('BIOMETRICO');
    expect(socio.hora_registro).toBeDefined();
    expect(notificationSpy.success).toHaveBeenCalled();
  }));

  it('guardarPlanilla debe registrar bulk las asistencias y motivos circunstanciados', () => {
    eventoServiceSpy.registrarAsistenciasBulk.and.returnValue(of({
      evento_id: 1,
      estado_evento: 'EN_CURSO',
      asistencias_procesadas: 2,
      expedientes_generados: 0,
      apercibimientos_generados: 0
    }));

    component.guardarPlanilla();

    expect(eventoServiceSpy.registrarAsistenciasBulk).toHaveBeenCalled();
    expect(notificationSpy.success).toHaveBeenCalledWith('Planilla de asistencia guardada correctamente.');
  });

  it('abrirModalProcesarYCerrar debe abrir ResumenCierreDialogComponent y procesar cierre al confirmar', () => {
    const dialogRefSpy = jasmine.createSpyObj({ afterClosed: of(true) });
    dialogSpy.open.and.returnValue(dialogRefSpy);

    eventoServiceSpy.procesarAsistencias.and.returnValue(of({
      evento_id: 1,
      estado_evento: 'CERRADA',
      asistencias_procesadas: 2,
      expedientes_generados: 1,
      apercibimientos_generados: 0
    }));

    component.abrirModalProcesarYCerrar();

    expect(dialogSpy.open).toHaveBeenCalled();
    expect(eventoServiceSpy.procesarAsistencias).toHaveBeenCalled();
    expect(component.eventoActivo?.estado).toBe('CERRADA');
    expect(notificationSpy.success).toHaveBeenCalled();
  });
});
