import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
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
import { SocioApiService } from '../../../services/socio-api.service';
import { EventoInstitucional } from '../../../models/evento.model';

describe('AsistenciaEventoComponent (Rediseño 2 Pestañas / SCRUM-50)', () => {
  let component: AsistenciaEventoComponent;
  let fixture: ComponentFixture<AsistenciaEventoComponent>;
  let eventoServiceSpy: jasmine.SpyObj<EventoService>;
  let notificationSpy: jasmine.SpyObj<NotificationService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;
  let socioApiSpy: jasmine.SpyObj<SocioApiService>;

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
      'getMisEventos',
      'getAsistencias',
      'registrarAsistenciasBulk',
      'procesarAsistencias',
      'crearEvento',
      'notificarEvento',
      'anularEvento',
      'fijarHoraFin'
    ]);
    notificationSpy = jasmine.createSpyObj('NotificationService', ['success', 'error', 'info', 'warning']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
    socioApiSpy = jasmine.createSpyObj('SocioApiService', ['searchSocios']);

    eventoServiceSpy.getEventos.and.returnValue(of([mockEvento]));
    eventoServiceSpy.getMisEventos.and.returnValue(of([mockEvento]));
    eventoServiceSpy.getAsistencias.and.returnValue(of(mockAsistencias));
    socioApiSpy.searchSocios.and.returnValue(of({ count: 0, next: null, previous: null, results: [] }));

    await TestBed.configureTestingModule({
      imports: [FormsModule, ReactiveFormsModule, HttpClientTestingModule, RouterTestingModule],
      declarations: [AsistenciaEventoComponent],
      providers: [
        { provide: EventoService, useValue: eventoServiceSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: MatDialog, useValue: dialogSpy },
        { provide: SocioApiService, useValue: socioApiSpy },
        AttendanceContextService,
        BiometricAttendanceStrategy,
        TribunalDataService
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AsistenciaEventoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe inicializar y cargar la lista de eventos, mis eventos y formulario reactivo', () => {
    expect(component).toBeTruthy();
    expect(component.tabActiva).toBe('generar');
    expect(component.crearForm).toBeDefined();
    expect(component.crearForm.get('titulo')).toBeDefined();
    expect(component.eventoActivo).toEqual(mockEvento);
    expect(component.convocados.length).toBe(2);
    expect(eventoServiceSpy.getEventos).toHaveBeenCalled();
    expect(eventoServiceSpy.getMisEventos).toHaveBeenCalled();
  });

  it('debe alternar pestañas entre Generar Evento y Mis Eventos', () => {
    component.setTab('mis-eventos');
    expect(component.tabActiva).toBe('mis-eventos');
    expect(eventoServiceSpy.getMisEventos).toHaveBeenCalledTimes(2);

    component.setTab('generar');
    expect(component.tabActiva).toBe('generar');
  });

  it('debe conmutar a detalle de evento y permitir volver a Mis Eventos', () => {
    component.verDetalle(mockEvento);
    expect(component.modoDetalle).toBeTrue();
    expect(component.eventoActivo).toEqual(mockEvento);

    component.volverAMisEventos();
    expect(component.modoDetalle).toBeFalse();
  });

  it('debe exigir detalle_tarea cuando la categoría es ACTIVIDAD y permitir sanción personalizada', () => {
    component.onCategoriaChange('ACTIVIDAD');
    expect(component.crearForm.get('categoria')?.value).toBe('ACTIVIDAD');

    const detalleControl = component.crearForm.get('detalle_tarea');
    expect(detalleControl?.validator).toBeDefined();

    component.crearForm.patchValue({
      titulo: 'Jornada Solidaria',
      fecha_programada: '2026-10-20T10:00',
      puntos_sancion: -2.5
    });

    expect(component.crearForm.valid).toBeFalse(); // falta detalle_tarea

    detalleControl?.setValue('Pintura y acondicionamiento del aula Magna');
    expect(component.crearForm.get('puntos_sancion')?.value).toBe(-2.5);
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
      estado_evento: 'FINALIZADO',
      asistencias_procesadas: 2,
      expedientes_generados: 1,
      apercibimientos_generados: 0
    }));

    component.abrirModalProcesarYCerrar();

    expect(dialogSpy.open).toHaveBeenCalled();
    expect(eventoServiceSpy.procesarAsistencias).toHaveBeenCalled();
    expect(component.eventoActivo?.estado).toBe('FINALIZADO');
    expect(notificationSpy.success).toHaveBeenCalled();
  });
});
