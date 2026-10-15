import { ComponentFixture, TestBed, fakeAsync, tick, discardPeriodicTasks } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of } from 'rxjs';
import { CrearEventoDialogComponent } from './crear-evento-dialog.component';
import { EventoService } from '../../../../services/evento.service';
import { SocioApiService } from '../../../../services/socio-api.service';
import { NotificationService } from '../../../../services/notification.service';

describe('CrearEventoDialogComponent (T14 / CA1 / CA8 / CA9)', () => {
  let component: CrearEventoDialogComponent;
  let fixture: ComponentFixture<CrearEventoDialogComponent>;
  let eventoServiceSpy: jasmine.SpyObj<EventoService>;
  let socioServiceSpy: jasmine.SpyObj<SocioApiService>;
  let notificationSpy: jasmine.SpyObj<NotificationService>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<CrearEventoDialogComponent>>;

  beforeEach(async () => {
    eventoServiceSpy = jasmine.createSpyObj('EventoService', ['crearEvento']);
    socioServiceSpy = jasmine.createSpyObj('SocioApiService', ['searchSocios']);
    notificationSpy = jasmine.createSpyObj('NotificationService', ['success', 'error', 'info', 'warning']);
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule],
      declarations: [CrearEventoDialogComponent],
      providers: [
        { provide: EventoService, useValue: eventoServiceSpy },
        { provide: SocioApiService, useValue: socioServiceSpy },
        { provide: NotificationService, useValue: notificationSpy },
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: {} }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CrearEventoDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    fixture.destroy();
  });

  it('debe inicializar el formulario con valores por defecto válidos', () => {
    expect(component).toBeTruthy();
    expect(component.form.get('categoria')?.value).toBe('REUNION');
    expect(component.form.get('tipo')?.value).toBe('ORDINARIA');
    expect(component.form.get('modalidad')?.value).toBe('PRESENCIAL_SEDE');
    expect(component.form.get('modo_convocatoria')?.value).toBe('GRUPO');
  });

  it('el título y fecha_programada son obligatorios, mientras fecha_fin es estrictamente opcional (CA8)', () => {
    const tituloCtrl = component.form.get('titulo');
    const fechaProgCtrl = component.form.get('fecha_programada');
    const fechaFinCtrl = component.form.get('fecha_fin');

    tituloCtrl?.setValue('');
    fechaProgCtrl?.setValue('');
    fechaFinCtrl?.setValue('');

    expect(tituloCtrl?.valid).toBeFalse();
    expect(fechaProgCtrl?.valid).toBeFalse();
    expect(fechaFinCtrl?.valid).toBeTrue(); // estrictamente opcional
  });

  it('debe cambiar subtipos dinámicamente al alternar entre REUNION y ACTIVIDAD (CA9)', () => {
    component.form.patchValue({ categoria: 'ACTIVIDAD' });
    component.onCategoriaChange();

    expect(component.subtiposDisponibles.some(s => s.value === 'MANTENIMIENTO')).toBeTrue();
    expect(component.subtiposDisponibles.some(s => s.value === 'VOLUNTARIADO')).toBeTrue();
    expect(component.subtiposDisponibles.some(s => s.value === 'JORNADA')).toBeTrue();
    expect(component.form.get('tipo')?.value).toBe('MANTENIMIENTO');

    component.form.patchValue({ categoria: 'REUNION' });
    component.onCategoriaChange();

    expect(component.subtiposDisponibles.some(s => s.value === 'ORDINARIA')).toBeTrue();
    expect(component.subtiposDisponibles.some(s => s.value === 'ASAMBLEA')).toBeTrue();
    expect(component.form.get('tipo')?.value).toBe('ORDINARIA');
  });

  it('debe exigir ubicación obligatoria solo para modalidad externa o virtual', () => {
    const ubicCtrl = component.form.get('ubicacion');

    // PRESENCIAL_SEDE -> no requiere ubicacion
    component.form.patchValue({ modalidad: 'PRESENCIAL_SEDE' });
    component.onModalidadChange();
    expect(ubicCtrl?.valid).toBeTrue();

    // PRESENCIAL_EXTERNA -> requiere ubicacion
    component.form.patchValue({ modalidad: 'PRESENCIAL_EXTERNA' });
    component.onModalidadChange();
    expect(ubicCtrl?.valid).toBeFalse();

    ubicCtrl?.setValue('Campus UTN FRC');
    expect(ubicCtrl?.valid).toBeTrue();

    // VIRTUAL -> requiere enlace
    component.form.patchValue({ modalidad: 'VIRTUAL' });
    ubicCtrl?.setValue('');
    component.onModalidadChange();
    expect(ubicCtrl?.valid).toBeFalse();

    ubicCtrl?.setValue('https://meet.google.com/xyz-1234');
    expect(ubicCtrl?.valid).toBeTrue();
  });

  it('debe verificar antelación mínima de 2 días hábiles (CA1)', () => {
    // Fecha dentro de pocas horas (mismo día) -> NO_SANCIONABLE
    const fechaInmediata = new Date();
    fechaInmediata.setHours(fechaInmediata.getHours() + 4);
    component.form.patchValue({ fecha_programada: fechaInmediata.toISOString() });
    component.verificarAntelacion();
    expect(component.antelacionAviso).toBe('NO_SANCIONABLE');

    // Fecha a 5 días hábiles en el futuro -> SANCIONABLE
    const fechaFutura = new Date();
    fechaFutura.setDate(fechaFutura.getDate() + 7);
    component.form.patchValue({ fecha_programada: fechaFutura.toISOString() });
    component.verificarAntelacion();
    expect(component.antelacionAviso).toBe('SANCIONABLE');
  });

  it('debe permitir buscar y agregar socios en modo convocatoria PERSONALIZADA (Select2)', fakeAsync(() => {
    component.form.patchValue({ modo_convocatoria: 'PERSONALIZADA' });
    component.onModoConvocatoriaChange();

    socioServiceSpy.searchSocios.and.returnValue(of({
      count: 1,
      next: null,
      previous: null,
      results: [
        { id: 201, legajo: '88123', first_name: 'Ana', last_name: 'Pérez', email: 'ana@aveit.com', role: 'socio', category: 'ACTIVE', category_display: 'Activo', subcomision: 'Deportes' }
      ]
    }));

    component.filtroSocioControl.setValue('Pérez');
    tick(350);

    expect(socioServiceSpy.searchSocios).toHaveBeenCalledWith('Pérez');
    expect(component.sociosEncontrados.length).toBe(1);

    // Agregar socio
    component.agregarSocioPersonalizado(component.sociosEncontrados[0]);
    expect(component.sociosSeleccionados.length).toBe(1);
    expect(component.sociosSeleccionados[0].id).toBe(201);
    expect(component.sociosEncontrados.length).toBe(0);

    // Quitar socio
    component.quitarSocioPersonalizado(201);
    expect(component.sociosSeleccionados.length).toBe(0);

    tick(350);
    discardPeriodicTasks();
  }));

  it('guardar debe rechazar si modo PERSONALIZADA no tiene socios seleccionados', () => {
    component.form.patchValue({
      titulo: 'Reunión Personalizada',
      fecha_programada: new Date().toISOString(),
      modo_convocatoria: 'PERSONALIZADA'
    });
    component.sociosSeleccionados = [];

    component.guardar();
    expect(notificationSpy.error).toHaveBeenCalledWith('Debe convocar al menos a un socio en la lista personalizada.');
    expect(eventoServiceSpy.crearEvento).not.toHaveBeenCalled();
  });

  it('guardar debe enviar el payload completo, notificar éxito y cerrar diálogo', () => {
    component.form.patchValue({
      titulo: 'Reunión Ordinaria Consejo Directivo',
      categoria: 'REUNION',
      tipo: 'ORDINARIA',
      modalidad: 'PRESENCIAL_SEDE',
      fecha_programada: '2026-11-10T18:00:00Z',
      modo_convocatoria: 'GRUPO',
      grupo_convocado: 'G58'
    });

    const mockCreado = { id: 99, titulo: 'Reunión Ordinaria Consejo Directivo' } as any;
    eventoServiceSpy.crearEvento.and.returnValue(of(mockCreado));

    component.guardar();

    expect(eventoServiceSpy.crearEvento).toHaveBeenCalled();
    expect(notificationSpy.success).toHaveBeenCalledWith('Evento institucional programado y publicado exitosamente.');
    expect(dialogRefSpy.close).toHaveBeenCalledWith(mockCreado);
  });
});
