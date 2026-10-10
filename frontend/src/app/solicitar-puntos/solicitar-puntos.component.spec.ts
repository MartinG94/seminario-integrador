import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { ExpedienteApiService, SolicitudMonitoreo, SolicitudT01 } from '../services/expediente-api.service';
import { PadronApiService } from '../services/padron-api.service';
import { SolicitudDetalleDialogComponent } from './solicitud-detalle-dialog/solicitud-detalle-dialog.component';
import { SolicitarPuntosComponent } from './solicitar-puntos.component';

describe('SolicitarPuntosComponent', () => {
  let component: SolicitarPuntosComponent;
  let fixture: ComponentFixture<SolicitarPuntosComponent>;
  let expediente: jasmine.SpyObj<ExpedienteApiService>;
  let padron: jasmine.SpyObj<PadronApiService>;
  let dialog: jasmine.SpyObj<MatDialog>;

  const draft: SolicitudT01 = {
    id: 'draft-1',
    estado: 'DRAFT',
    solicitante: 1,
    destinatario_socio_id: 7,
    destinatarios_socios_ids: [7],
    tipo_accion: 'SANCTION',
    titulo: 'Título causa',
    causal: '',
    puntos: -1,
    motivo: 'Motivo',
    razon: 'Razón',
    reglamentos_respaldantes: [],
    anexo_fecha: null,
    anexo_lugar: '',
    anexo_relato: '',
    anexo_testigos: '',
    snapshot_destinatario: null,
    snapshots_destinatarios: [],
    snapshot_emitido: null,
    numero_expediente: null,
    created_at: '',
    updated_at: '',
    issued_at: null,
  };

  const mockSolicitudes: SolicitudMonitoreo[] = [
    {
      id: 'draft-1',
      numero: 'T01-001',
      numero_expediente: null,
      fecha: '2026-03-01T10:00:00Z',
      estado: 'DRAFT',
      tipo_accion: 'SANCTION',
      puntos: -1,
      titulo: 'Borrador 1',
      motivo: 'Motivo borrador',
      causal: 'Causal borrador',
      razon: 'Razón borrador',
      reglamentos_respaldantes: ['Estatuto AVEIT'],
      anexo_fecha: '2026-03-01',
      anexo_lugar: 'Sede AVEIT',
      anexo_relato: 'Relato anexo',
      anexo_testigos: 'Testigo 1',
      destinatarios_socios_ids: [7],
      estado_procesal: 'borrador',
      estado_procesal_display: 'Borrador',
      involucrados: [{ socio_id: 7, legajo: '777', first_name: 'Ana', last_name: 'Prueba' }],
      resolucion_final: null,
      created_at: '2026-03-01T10:00:00Z',
      issued_at: null,
    },
    {
      id: 'issued-2',
      numero: 'T01-002',
      numero_expediente: 'EXP-002',
      fecha: '2026-03-02T12:00:00Z',
      estado: 'ISSUED',
      tipo_accion: 'MERIT',
      puntos: 2,
      titulo: 'Mérito 2',
      motivo: 'Motivo emitido',
      causal: 'Causal emitido',
      razon: 'Razón emitida',
      reglamentos_respaldantes: [],
      anexo_fecha: null,
      anexo_lugar: '',
      anexo_relato: '',
      anexo_testigos: '',
      destinatarios_socios_ids: [7, 8],
      estado_procesal: 'en_descargo',
      estado_procesal_display: 'En Descargo',
      involucrados: [
        { socio_id: 7, legajo: '777', first_name: 'Ana', last_name: 'Prueba' },
        { socio_id: 8, legajo: '888', first_name: 'Bruno', last_name: 'García' },
      ],
      resolucion_final: null,
      created_at: '2026-03-02T12:00:00Z',
      issued_at: '2026-03-02T12:30:00Z',
    },
  ];

  beforeEach(() => {
    expediente = jasmine.createSpyObj('ExpedienteApiService', [
      'crearBorrador',
      'actualizarBorrador',
      'emitir',
      'obtener',
      'listarReglamentos',
      'listarMisSolicitudes',
      'eliminarBorrador',
    ]);
    padron = jasmine.createSpyObj('PadronApiService', ['listarSocios']);
    dialog = jasmine.createSpyObj('MatDialog', ['open']);

    padron.listarSocios.and.returnValue(
      of([
        {
          socio_id: 7,
          legajo: '777',
          first_name: 'Ana',
          last_name: 'Prueba',
          subcomision: { id: 1, name: 'Cómputos' },
          is_active: true,
        },
        {
          socio_id: 8,
          legajo: '888',
          first_name: 'Bruno',
          last_name: 'García',
          subcomision: null,
          is_active: true,
        },
      ])
    );
    expediente.crearBorrador.and.returnValue(of(draft));
    expediente.actualizarBorrador.and.returnValue(of(draft));
    expediente.emitir.and.returnValue(
      of({ ...draft, estado: 'ISSUED', numero_expediente: 'T01-2026-1', issued_at: '2026-01-01' })
    );
    expediente.listarReglamentos.and.returnValue(of({ reglamentos: ['Estatuto AVEIT Reforma 2026'] }));
    expediente.listarMisSolicitudes.and.returnValue(of(mockSolicitudes));
    expediente.eliminarBorrador.and.returnValue(of(undefined as unknown as void));

    TestBed.configureTestingModule({
      imports: [
        FormsModule,
        ReactiveFormsModule,
        MatAutocompleteModule,
        MatButtonModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDialogModule,
        MatExpansionModule,
        MatIconModule,
        NoopAnimationsModule,
        RouterTestingModule,
      ],
      declarations: [SolicitarPuntosComponent],
      providers: [
        { provide: ExpedienteApiService, useValue: expediente },
        { provide: PadronApiService, useValue: padron },
        { provide: MatDialog, useValue: dialog },
      ],
    });
    fixture = TestBed.createComponent(SolicitarPuntosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga lista de socios del padrón', () => {
    expect(component.socios.length).toBe(2);
    expect(component.socios[0].socio_id).toBe(7);
  });

  function urgencyOption(value: string): HTMLInputElement {
    const option = fixture.nativeElement.querySelector(`input[name="urgency"][value="${value}"]`) as HTMLInputElement | null;
    if (!option) throw new Error(`Falta la opción visible de urgencia ${value}.`);
    return option;
  }

  function selectedUrgency(): string {
    const selected = fixture.nativeElement.querySelector('input[name="urgency"]:checked') as HTMLInputElement | null;
    if (!selected) throw new Error('Debe haber un nivel de urgencia seleccionado.');
    return selected.value;
  }

  function selectUrgency(value: string): void {
    tick();
    urgencyOption(value).click();
    fixture.detectChanges();
    tick();
  }

  it('ofrece tres opciones visibles y etiquetadas con Normal seleccionado, sin desplegable', async () => {
    await fixture.whenStable();
    fixture.detectChanges();
    const options: HTMLInputElement[] = Array.from(fixture.nativeElement.querySelectorAll('input[name="urgency"]'));
    expect(options.map(option => option.value)).toEqual(['baja', 'normal', 'urgente']);
    expect(options.map(option => option.closest('label')?.textContent?.trim())).toEqual(['Baja', 'Normal', 'Urgente']);
    expect(fixture.nativeElement.querySelector('.urgency-field legend').textContent.trim()).toBe('Urgencia');
    expect(fixture.nativeElement.querySelector('select#urgencia-solicitud')).toBeNull();
    expect(selectedUrgency()).toBe('normal');
  });

  it('permite elegir desde la etiqueta y mantiene un único nivel incluso al pulsar el ya elegido', fakeAsync(() => {
    tick();
    for (const value of ['urgente', 'baja', 'baja', 'normal']) {
      urgencyOption(value).closest('label')?.click();
      fixture.detectChanges();
      tick();
      expect(selectedUrgency()).toBe(value);
      expect(component.urgency).toBe(value);
      expect(fixture.nativeElement.querySelectorAll('input[name="urgency"]:checked').length).toBe(1);
    }
  }));

  it('bloquea los tres niveles durante la carga sin perder la elección y vuelve a habilitarlos', async () => {
    await fixture.whenStable();
    fixture.detectChanges();
    expect(selectedUrgency()).toBe('normal');
    component.cargando = true;
    fixture.detectChanges();
    await fixture.whenStable();
    for (const value of ['baja', 'normal', 'urgente']) {
      expect(urgencyOption(value).matches(':disabled')).toBeTrue();
      urgencyOption(value).click();
    }
    fixture.detectChanges();
    await fixture.whenStable();
    expect(selectedUrgency()).toBe('normal');
    component.cargando = false;
    fixture.detectChanges();
    await fixture.whenStable();
    urgencyOption('urgente').click();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(selectedUrgency()).toBe('urgente');
    expect(urgencyOption('urgente').matches(':disabled')).toBeFalse();
  });

  for (const urgency of ['baja', 'urgente'] as const) {
    it(`envía y conserva la urgencia ${urgency} al guardar y actualizar un borrador`, fakeAsync(() => {
      expediente.crearBorrador.and.returnValue(of({ ...draft, urgencia: urgency }));
      expediente.actualizarBorrador.and.returnValue(of({ ...draft, urgencia: urgency }));
      selectUrgency(urgency);
      component.guardarBorrador();
      fixture.detectChanges();
      tick();
      expect(expediente.crearBorrador).toHaveBeenCalledWith(jasmine.objectContaining({ urgencia: urgency }));
      expect(selectedUrgency()).toBe(urgency);
      component.guardarBorrador();
      expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.objectContaining({ urgencia: urgency }));
    }));
  }

  it('retoma un borrador urgente y lo emite conservando su urgencia y bloqueando el selector', fakeAsync(() => {
    spyOn(window, 'scrollTo');
    expediente.actualizarBorrador.and.returnValue(of({ ...draft, urgencia: 'urgente' as const }));
    expediente.emitir.and.returnValue(of({ ...draft, urgencia: 'urgente' as const, estado: 'ISSUED', numero_expediente: 'T01-2026-1' }));
    component.continuarEdicion({ ...mockSolicitudes[0], urgencia: 'urgente' });
    fixture.detectChanges();
    tick();
    expect(selectedUrgency()).toBe('urgente');
    component.emitirT01();
    fixture.detectChanges();
    tick();
    expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.objectContaining({ urgencia: 'urgente' }));
    expect(expediente.emitir).toHaveBeenCalledWith('draft-1');
    expect(selectedUrgency()).toBe('urgente');
    expect(urgencyOption('urgente').matches(':disabled')).toBeTrue();
  }));

  it('vuelve a Normal al iniciar otra solicitud o retomar un borrador sin urgencia', fakeAsync(() => {
    spyOn(window, 'scrollTo');
    selectUrgency('baja');
    component.resetearFormulario();
    fixture.detectChanges();
    tick();
    expect(selectedUrgency()).toBe('normal');
    selectUrgency('urgente');
    component.continuarEdicion(mockSolicitudes[0]);
    fixture.detectChanges();
    tick();
    expect(selectedUrgency()).toBe('normal');
  }));

  it('conserva la urgencia seleccionada si falla el guardado', fakeAsync(() => {
    expediente.crearBorrador.and.returnValue(throwError(() => ({ status: 500 })));
    selectUrgency('urgente');
    component.guardarBorrador();
    fixture.detectChanges();
    tick();
    expect(selectedUrgency()).toBe('urgente');
    expect(urgencyOption('urgente').matches(':disabled')).toBeFalse();
  }));

  it('conserva la opción de puntos al recibir decimales serializados por Django', async () => {
    await fixture.whenStable();
    expediente.crearBorrador.and.returnValue(of({ ...draft, puntos: '-1.00' }));
    component.guardarBorrador();
    fixture.detectChanges();
    await fixture.whenStable();
    const selects: HTMLSelectElement[] = Array.from(fixture.nativeElement.querySelectorAll('select'));
    const pointsSelect = selects.find(select => Array.from(select.options).some(option => option.textContent?.includes('Falta Media')));
    expect(pointsSelect?.selectedOptions[0]?.textContent?.trim()).toBe('-1.0 pts: Falta Media');
    component.guardarBorrador();
    expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.objectContaining({ puntos: -1 }));
  });

  it('agrega socios seleccionados a la lista', () => {
    component.agregarSocio(component.socios[0]);
    expect(component.sociosSeleccionados.length).toBe(1);
    expect(component.sociosSeleccionados[0].socio_id).toBe(7);
  });

  it('evita duplicados al intentar agregar el mismo socio dos veces', () => {
    component.agregarSocio(component.socios[0]);
    component.agregarSocio(component.socios[0]);
    expect(component.sociosSeleccionados.length).toBe(1);
  });

  it('permite eliminar un socio de la lista de seleccionados', () => {
    component.agregarSocio(component.socios[0]);
    component.agregarSocio(component.socios[1]);
    expect(component.sociosSeleccionados.length).toBe(2);
    component.eliminarSocio(7);
    expect(component.sociosSeleccionados.length).toBe(1);
    expect(component.sociosSeleccionados[0].socio_id).toBe(8);
  });

  it('no muestra coincidencias con menos de tres caracteres', () => {
    component.filtrarSocios('Pr');
    expect(component.sociosFiltrados).toEqual([]);
  });

  it('filtra por legajo y por nombre o apellido excluyendo los ya seleccionados', () => {
    component.filtrarSocios('777');
    expect(component.sociosFiltrados.map(socio => socio.socio_id)).toEqual([7]);
    component.agregarSocio(component.socios[0]);
    component.filtrarSocios('777');
    expect(component.sociosFiltrados).toEqual([]);
  });

  it('deshabilita el control cuando el expediente está emitido', () => {
    component.estado = 'ISSUED';
    component.sincronizarEstadoSocio();
    fixture.detectChanges();
    expect(component.socioBusqueda.disabled).toBeTrue();
  });

  it('guarda por POST y luego por PATCH, sin exigir anexo', () => {
    component.agregarSocio(component.socios[0]);
    component.guardarBorrador();
    expect(expediente.crearBorrador).toHaveBeenCalled();
    component.guardarBorrador();
    expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.any(Object));
  });

  it('emite usando el id del borrador y bloquea el estado ISSUED', () => {
    component.titulo = 'Título de prueba';
    component.agregarSocio(component.socios[0]);
    component.razon = 'Motivo de prueba';
    component.emitirT01();
    expect(expediente.emitir).toHaveBeenCalledWith('draft-1');
    expect(component.estado).toBe('ISSUED');
    expect(component.numeroExpediente).toBe('T01-2026-1');
  });

  it('muestra errores del backend', () => {
    expediente.crearBorrador.and.returnValue(throwError(() => ({ error: { detail: 'No autorizado' } })));
    component.guardarBorrador();
    expect(component.errorMensaje).toBe('No autorizado');
  });

  it('muestra un mensaje seguro para errores 500', () => {
    expediente.crearBorrador.and.returnValue(
      throwError(() => ({ status: 500, error: '<pre>traceback</pre>' }))
    );
    component.guardarBorrador();
    expect(component.errorMensaje).toContain('servicio no está disponible');
    expect(component.errorMensaje).not.toContain('traceback');
    expect(component.errorMensaje).not.toContain('<pre>');
  });

  it('no trata una respuesta string o HTML como objeto de errores', () => {
    expediente.crearBorrador.and.returnValue(
      throwError(() => ({ status: 400, error: '<html>Error interno</html>' }))
    );
    component.guardarBorrador();
    expect(component.errorMensaje).toBe('No se pudo completar la operación.');
    expect(component.errorMensaje).not.toContain('<html>');
  });

  // ==========================================
  // Pruebas TS-75.5: Panel Mis Solicitudes T01
  // ==========================================

  it('carga la lista de solicitudes al inicializar el componente', () => {
    expect(expediente.listarMisSolicitudes).toHaveBeenCalledWith({ search: undefined, estado: undefined });
    expect(component.misSolicitudes.length).toBe(2);
    expect(component.misSolicitudes[0].id).toBe('draft-1');
  });

  it('filtra solicitudes con debounce al escribir en el buscador', fakeAsync(() => {
    expediente.listarMisSolicitudes.calls.reset();
    component.busquedaControl.setValue('inconducta');
    tick(100);
    expect(expediente.listarMisSolicitudes).not.toHaveBeenCalled();

    tick(250); // Completa el debounceTime(300)
    expect(expediente.listarMisSolicitudes).toHaveBeenCalledWith({ search: 'inconducta', estado: undefined });
  }));

  it('filtra solicitudes inmediatamente al cambiar el estado', () => {
    expediente.listarMisSolicitudes.calls.reset();
    component.estadoFiltro.setValue('DRAFT');
    expect(expediente.listarMisSolicitudes).toHaveBeenCalledWith({ search: undefined, estado: 'DRAFT' });
  });

  it('carga el borrador en el formulario al presionar continuarEdicion y desplaza hacia arriba', () => {
    spyOn(window, 'scrollTo').and.callFake(() => {});
    const borrador = mockSolicitudes[0];

    component.continuarEdicion(borrador);

    expect(component.borradorId).toBe('draft-1');
    expect(component.tabActiva).toBe('nueva');
    expect(component.titulo).toBe('Borrador 1');
    expect(component.causal).toBe('Causal borrador');
    expect(component.tipoAccion).toBe('SANCTION');
    expect(component.puntosSeleccionados).toBe(-1);
    expect(component.razon).toBe('Razón borrador');
    expect(component.anexoFecha).toBe('2026-03-01');
    expect(component.anexoLugar).toBe('Sede AVEIT');
    expect(component.anexoExpandido).toBeTrue();
    expect(component.sociosSeleccionados.length).toBe(1);
    expect(component.sociosSeleccionados[0].socio_id).toBe(7);
    expect(component.exitoMensaje).toContain('cargado en el formulario');
    expect(window.scrollTo).toHaveBeenCalled();
  });

  it('conmuta correctamente entre pestañas (nueva solicitud y solicitudes creadas)', () => {
    expect(component.tabActiva).toBe('nueva');
    component.setTab('creadas');
    expect(component.tabActiva).toBe('creadas');
    component.setTab('nueva');
    expect(component.tabActiva).toBe('nueva');
  });

  it('no ejecuta continuarEdicion si la solicitud ya está en estado ISSUED', () => {
    const emitida = mockSolicitudes[1];
    component.borradorId = null;
    component.continuarEdicion(emitida);
    expect(component.borradorId).toBeNull();
  });

  it('cancela la eliminación de borrador si el usuario rechaza la confirmación', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    component.eliminarBorrador(mockSolicitudes[0]);
    expect(expediente.eliminarBorrador).not.toHaveBeenCalled();
  });

  it('elimina el borrador, limpia el formulario si coincidía y recarga la lista cuando el usuario confirma', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    expediente.listarMisSolicitudes.calls.reset();
    component.borradorId = 'draft-1';
    component.titulo = 'Borrador 1';

    component.eliminarBorrador(mockSolicitudes[0]);

    expect(expediente.eliminarBorrador).toHaveBeenCalledWith('draft-1');
    expect(component.exitoMensaje).toContain('eliminado correctamente');
    expect(component.borradorId).toBeNull();
    expect(component.titulo).toBe('');
    expect(expediente.listarMisSolicitudes).toHaveBeenCalled();
  });

  it('abre el diálogo de detalle al presionar abrirDetalle sobre una solicitud emitida', () => {
    const emitida = mockSolicitudes[1];
    component.abrirDetalle(emitida);

    expect(dialog.open).toHaveBeenCalledWith(SolicitudDetalleDialogComponent, {
      width: '100%',
      maxWidth: '750px',
      data: emitida,
    });
  });

  it('retorna clases semánticas de badge conformes a DESIGN.md', () => {
    expect(component.obtenerClaseBadge(mockSolicitudes[0])).toBe('badge-mat-rose'); // DRAFT
    expect(component.obtenerClaseBadge(mockSolicitudes[1])).toBe('badge-mat-warning'); // en_descargo

    const solCreada = { ...mockSolicitudes[1], estado_procesal: 'creado' };
    expect(component.obtenerClaseBadge(solCreada)).toBe('badge-mat-info');

    const solEval = { ...mockSolicitudes[1], estado_procesal: 'espera_resolucion' };
    expect(component.obtenerClaseBadge(solEval)).toBe('badge-mat-primary');

    const solEmitida = { ...mockSolicitudes[1], estado_procesal: 'emitido' };
    expect(component.obtenerClaseBadge(solEmitida)).toBe('badge-mat-success');

    const solRechazada = { ...mockSolicitudes[1], estado_procesal: 'rechazado' };
    expect(component.obtenerClaseBadge(solRechazada)).toBe('badge-mat-danger');
  });

  it('formatea correctamente el texto de socios involucrados', () => {
    expect(component.obtenerTextoInvolucrados({ ...mockSolicitudes[0], involucrados: [] })).toBe('Sin socios asignados');
    expect(component.obtenerTextoInvolucrados(mockSolicitudes[0])).toBe('Prueba, Ana');
    expect(component.obtenerTextoInvolucrados(mockSolicitudes[1])).toBe('Prueba, Ana (+1)');
  });
});
