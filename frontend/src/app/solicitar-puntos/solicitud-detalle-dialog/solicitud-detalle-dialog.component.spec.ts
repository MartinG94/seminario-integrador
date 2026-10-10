import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { SolicitudMonitoreo } from '../../services/expediente-api.service';
import { SolicitudDetalleDialogComponent } from './solicitud-detalle-dialog.component';

describe('SolicitudDetalleDialogComponent', () => {
  let component: SolicitudDetalleDialogComponent;
  let fixture: ComponentFixture<SolicitudDetalleDialogComponent>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<SolicitudDetalleDialogComponent>>;

  const mockSolicitud: SolicitudMonitoreo = {
    id: 'sol-001',
    numero: 'T01-2026-001',
    numero_expediente: 'EXP-2026-001',
    fecha: '2026-03-15T10:00:00Z',
    estado: 'ISSUED',
    tipo_accion: 'SANCTION',
    puntos: -1.5,
    titulo: 'Inconducta en Asamblea Ordinaria',
    motivo: 'Incumplimiento reiterado de las normas de convivencia',
    causal: 'Falta grave estatutaria',
    razon: 'Incumplimiento reiterado de las normas de convivencia durante la sesión',
    reglamentos_respaldantes: ['Estatuto Social AVEIT', 'Reglamento Disciplinario'],
    anexo_fecha: '2026-03-14',
    anexo_lugar: 'Sede Central AVEIT, Sala de Sesiones',
    anexo_relato: 'El socio interrumpió la asamblea de forma intempestiva',
    anexo_testigos: 'Juan Pérez, María López',
    destinatarios_socios_ids: [101, 102],
    estado_procesal: 'en_descargo',
    estado_procesal_display: 'En Descargo',
    involucrados: [
      { socio_id: 101, legajo: 'LEG-101', first_name: 'Carlos', last_name: 'Pérez', subcomision: 'Deportes' },
      { socio_id: 102, legajo: 'LEG-102', first_name: 'Ana', last_name: 'Gómez', subcomision: 'Cómputos' },
    ],
    resolucion_final: null,
    created_at: '2026-03-15T09:30:00Z',
    issued_at: '2026-03-15T10:00:00Z',
  };

  beforeEach(async () => {
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    await TestBed.configureTestingModule({
      declarations: [SolicitudDetalleDialogComponent],
      imports: [MatIconModule],
      providers: [
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: mockSolicitud },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SolicitudDetalleDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('muestra el número de solicitud y el estado procesal con su badge', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Solicitud T01-2026-001');
    expect(compiled.textContent).toContain('En Descargo');
  });

  it('renderiza título, tipo de acción y puntos propuestos', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Inconducta en Asamblea Ordinaria');
    expect(compiled.textContent).toContain('Sanción');
    expect(compiled.textContent).toContain('-1.5 pts');
    expect(compiled.textContent).toContain('Falta grave estatutaria');
  });

  it('muestra la lista de socios involucrados con legajo y subcomisión', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('LEG-101');
    expect(compiled.textContent).toContain('Pérez, Carlos');
    expect(compiled.textContent).toContain('Deportes');
    expect(compiled.textContent).toContain('LEG-102');
    expect(compiled.textContent).toContain('Gómez, Ana');
    expect(compiled.textContent).toContain('Cómputos');
  });

  it('muestra la razón y fundamentos de la solicitud', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Incumplimiento reiterado de las normas de convivencia durante la sesión');
  });

  it('muestra la hoja de anexo circunstanciada sin citar "Art. 16 bis"', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Hoja de anexo');
    expect(compiled.textContent).not.toContain('Art. 16 bis');
    expect(compiled.textContent).toContain('Sede Central AVEIT, Sala de Sesiones');
    expect(compiled.textContent).toContain('Juan Pérez, María López');
    expect(compiled.textContent).toContain('El socio interrumpió la asamblea de forma intempestiva');
  });

  it('no muestra tarjeta de resolución final si resolucion_final es null (confidencialidad)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).not.toContain('Resolución Firme Emitida');
  });

  it('muestra la resolución firme cuando está emitida y no expone deliberaciones ni votos reservados', () => {
    component.solicitud = {
      ...mockSolicitud,
      estado_procesal: 'emitido',
      estado_procesal_display: 'Resuelto con Dictamen',
      resolucion_final: {
        emitido: true,
        fecha: '2026-03-20T18:00:00Z',
        dictamen: 'Resolución firme emitida para causa EXP-2026-001. Se aplica sanción de -1.5 puntos.',
      },
    };
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Resolución Firme Emitida por el Tribunal de Disciplina');
    expect(compiled.textContent).toContain('Resolución firme emitida para causa EXP-2026-001');

    // Verificación estricta de confidencialidad de deliberaciones del TD (CA3)
    expect(compiled.textContent).not.toContain('voto');
    expect(compiled.textContent).not.toContain('deliberación');
    expect(compiled.textContent).not.toContain('nota interna');
  });

  it('invoca dialogRef.close al hacer clic en cerrar()', () => {
    component.cerrar();
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });

  it('mapea correctamente las clases de badge según el estado procesal', () => {
    expect(component.obtenerClaseEstado('creado')).toBe('badge-mat-info');
    expect(component.obtenerClaseEstado('justificando')).toBe('badge-mat-warning');
    expect(component.obtenerClaseEstado('en_descargo')).toBe('badge-mat-warning');
    expect(component.obtenerClaseEstado('revision_resolucion')).toBe('badge-mat-primary');
    expect(component.obtenerClaseEstado('espera_resolucion')).toBe('badge-mat-primary');
    expect(component.obtenerClaseEstado('evaluacion')).toBe('badge-mat-primary');
    expect(component.obtenerClaseEstado('pendiente_correos')).toBe('badge-mat-rose');
    expect(component.obtenerClaseEstado('emitido')).toBe('badge-mat-success');
    expect(component.obtenerClaseEstado('resuelto')).toBe('badge-mat-success');
    expect(component.obtenerClaseEstado('rechazado')).toBe('badge-mat-danger');
    expect(component.obtenerClaseEstado('desestimado')).toBe('badge-mat-danger');
    expect(component.obtenerClaseEstado('otro')).toBe('badge-mat-info');
  });
});
