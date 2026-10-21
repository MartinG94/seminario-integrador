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

  it('QA-FE-01: crearEventoSubmit debe crear el evento, resetear el formulario y cambiar a la pestaña Mis Eventos', () => {
    const eventoCreado: EventoInstitucional = {
      ...mockEvento,
      id: 99,
      titulo: 'Reunión Plenaria QA',
      estado: 'NOTIFICADO'
    };
    eventoServiceSpy.crearEvento.and.returnValue(of(eventoCreado));

    component.crearForm.patchValue({
      titulo: 'Reunión Plenaria QA',
      categoria: 'REUNION',
      tipo: 'ORDINARIA',
      modalidad: 'PRESENCIAL_SEDE',
      fecha_programada: '2026-10-28T18:00',
      modo_convocatoria: 'GRUPO',
      grupo_convocado: 'G58',
      notificar: true
    });

    component.crearEventoSubmit();

    expect(eventoServiceSpy.crearEvento).toHaveBeenCalled();
    expect(notificationSpy.success).toHaveBeenCalledWith(
      'Evento "Reunión Plenaria QA" generado y notificado formalmente a los convocados.'
    );
    expect(component.tabActiva).toBe('mis-eventos');
  });

  it('QA-FE-02: confirmarHoraFin debe registrar la hora de fin y actualizar el estado del evento abierto', () => {
    const eventoAbierto: EventoInstitucional = {
      ...mockEvento,
      id: 50,
      estado: 'ABIERTO',
      fecha_fin: null
    };
    eventoServiceSpy.fijarHoraFin.and.returnValue(
      of({
        detail: 'Fecha de finalización registrada exitosamente.',
        evento: { ...eventoAbierto, estado: 'FINALIZADO', fecha_fin: '2026-10-20T20:00:00Z' }
      })
    );

    component.abrirModalHoraFin(eventoAbierto);
    expect(component.modalHoraFinVisible).toBeTrue();
    component.horaFinInput = '2026-10-20T20:00';
    component.confirmarHoraFin();

    expect(eventoServiceSpy.fijarHoraFin).toHaveBeenCalled();
    expect(eventoAbierto.estado).toBe('FINALIZADO');
    expect(component.modalHoraFinVisible).toBeFalse();
    expect(notificationSpy.success).toHaveBeenCalled();
  });

  it('QA-FE-03: confirmarAnulacion debe anular el evento con motivo y cerrar el modal', () => {
    const eventoNotificado: EventoInstitucional = {
      ...mockEvento,
      id: 60,
      estado: 'NOTIFICADO'
    };
    eventoServiceSpy.anularEvento.and.returnValue(
      of({
        detail: 'Evento anulado correctamente.',
        evento: {
          ...eventoNotificado,
          estado: 'ANULADO',
          motivo_cancelacion: 'Corte de suministro eléctrico en sede'
        }
      })
    );

    component.abrirModalAnular(eventoNotificado);
    expect(component.modalAnularVisible).toBeTrue();
    component.motivoAnulacionInput = 'Corte de suministro eléctrico en sede';
    component.confirmarAnulacion();

    expect(eventoServiceSpy.anularEvento).toHaveBeenCalledWith(
      60,
      'Corte de suministro eléctrico en sede'
    );
    expect(eventoNotificado.estado).toBe('ANULADO');
    expect(component.modalAnularVisible).toBeFalse();
    expect(notificationSpy.success).toHaveBeenCalled();
  });

  it('QA-FE-04: seleccionarSocio y removerSocio deben administrar la lista de convocatoria PERSONALIZADA', () => {
    const socioMock = {
      id: 777,
      legajo: '74907',
      first_name: 'Lucas',
      last_name: 'Gastiaburu',
      full_name: 'Lucas Gastiaburu',
      email: 'lucas@aveit.org.ar',
      role: 'SOCIO',
      category: 'ACTIVE',
      social_year: 3,
      subcomision: 'Cómputos',
      is_enabled: true
    };

    component.seleccionarSocio(socioMock as any);
    expect(component.sociosSeleccionados.length).toBe(1);
    expect(component.sociosSeleccionados[0].id).toBe(777);

    component.removerSocio(777);
    expect(component.sociosSeleccionados.length).toBe(0);
  });
});
