import { ComponentFixture, fakeAsync, flush, TestBed, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { OverlayContainer } from '@angular/cdk/overlay';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, Subject, throwError } from 'rxjs';

import { AdminParametrosComponent } from './admin-parametros.component';
import {
  AdminApiService, CambioParametroDTO, CandidatoTribunalDTO, MiembroTribunalDTO, ParametroSistemaDTO
} from '../../../services/admin-api.service';
import { NotificationService } from '../../../services/notification.service';
import { ParametrosVigentesService } from '../../../services/parametros-vigentes.service';
import { AdminLayoutRoutes } from '../../../layouts/admin-layout/admin-layout.routing';
import { TribunalGuard } from '../../../services/tribunal.guard';

function parametro(over: Partial<ParametroSistemaDTO>): ParametroSistemaDTO {
  return {
    clave: 'plazo_descargo_dias_habiles', categoria: 'PLAZOS', etiqueta: 'Plazo de descargo',
    descripcion: 'Días hábiles', tipo: 'INTEGER', unidad: 'días hábiles', editable: true,
    minimo: '1', maximo: '30', valor: 5, valor_inicial: 5, actualizado_at: null, actualizado_por: '',
    ...over
  };
}

const candidato = (over: Partial<CandidatoTribunalDTO> = {}): CandidatoTribunalDTO => ({
  id: 9, numero_socio: 1201, first_name: 'Abril', last_name: 'Moya', social_year: 4, subcomision: null, ...over
});

describe('AdminParametrosComponent', () => {
  let fixture: ComponentFixture<AdminParametrosComponent>;
  let component: AdminParametrosComponent;
  let api: jasmine.SpyObj<AdminApiService>;
  let notifications: jasmine.SpyObj<NotificationService>;
  let vigentes: jasmine.SpyObj<ParametrosVigentesService>;
  let dialog: MatDialog;

  const parametros: ParametroSistemaDTO[] = [
    parametro({}),
    parametro({ clave: 'umbral_critico', categoria: 'UMBRALES', etiqueta: 'Umbral crítico', tipo: 'DECIMAL',
      editable: false, minimo: null, maximo: null, valor: '-10.0', valor_inicial: '-10.0', unidad: 'puntos' }),
    parametro({ clave: 'umbral_preventivo', categoria: 'UMBRALES', etiqueta: 'Umbral preventivo', tipo: 'DECIMAL',
      minimo: '-9.99', maximo: '-0.01', valor: '-7.0', valor_inicial: '-7.0', unidad: 'puntos' }),
    parametro({ clave: 'umbral_preventivo_activo', categoria: 'UMBRALES', etiqueta: 'Alerta preventiva activa',
      tipo: 'BOOLEAN', minimo: null, maximo: null, valor: false, valor_inicial: false, unidad: '' }),
    parametro({ clave: 'email_tribunal_disciplina', categoria: 'CORREOS', etiqueta: 'Tribunal de Disciplina',
      tipo: 'EMAIL', minimo: null, maximo: null, valor: 'td@aveit.test', valor_inicial: 'td@aveit.test', unidad: '' }),
    parametro({ clave: 'adjuntos_cantidad_maxima', categoria: 'ADJUNTOS', etiqueta: 'Cantidad máxima',
      maximo: '10', unidad: 'comprobantes', actualizado_por: 'Pérez, Ana (N° de socio 1001)',
      actualizado_at: '2026-11-15T13:00:00Z' }),
  ];
  const miembros: MiembroTribunalDTO[] = [
    { id: 1, numero_socio: 1033, legajo: '11239', last_name: 'Toselli', first_name: 'Giuliano', social_year: 6,
      email: 'g@aveit.test', subcomision: null },
    { id: 2, numero_socio: null, legajo: '11737', last_name: 'Cerda', first_name: 'Catalina', social_year: 5,
      email: 'c@aveit.test', subcomision: null },
  ];

  beforeEach(async () => {
    api = jasmine.createSpyObj('AdminApiService', ['listarParametros', 'actualizarParametro', 'historialParametro',
      'listarMiembrosTribunal', 'asignarMiembroTribunal', 'revocarMiembroTribunal', 'buscarCandidatosTribunal']);
    api.listarParametros.and.returnValue(of(parametros.map(p => ({ ...p }))));
    api.listarMiembrosTribunal.and.returnValue(of([...miembros]));
    api.buscarCandidatosTribunal.and.returnValue(of([]));
    notifications = jasmine.createSpyObj('NotificationService', ['success', 'error']);
    vigentes = jasmine.createSpyObj('ParametrosVigentesService', ['invalidar']);

    await TestBed.configureTestingModule({
      imports: [FormsModule, MatDialogModule, MatAutocompleteModule, NoopAnimationsModule],
      declarations: [AdminParametrosComponent],
      providers: [
        { provide: AdminApiService, useValue: api },
        { provide: NotificationService, useValue: notifications },
        { provide: ParametrosVigentesService, useValue: vigentes },
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(AdminParametrosComponent);
    component = fixture.componentInstance;
    dialog = TestBed.inject(MatDialog);
    fixture.detectChanges();
  });

  afterEach(() => dialog.closeAll());

  const overlay = (): HTMLElement => TestBed.inject(OverlayContainer).getContainerElement();
  const overlayText = (): string => overlay().textContent || '';

  it('muestra las cuatro tarjetas temáticas con sus parámetros', () => {
    const root: HTMLElement = fixture.nativeElement;
    const titulos = Array.from(root.querySelectorAll('.admin-card h4')).map(h => h.textContent?.trim());
    expect(titulos).toEqual(['Plazos', 'Umbrales de puntos', 'Correos institucionales', 'Comprobantes adjuntos']);
    expect(component.parametrosDe('UMBRALES').length).toBe(3);
    expect(root.textContent).toContain('Último cambio: Pérez, Ana (N° de socio 1001), 15/11/2026 10:00.');
  });

  it('muestra el umbral crítico como valor reglamentario sin campo editable ni citas', () => {
    const root: HTMLElement = fixture.nativeElement;
    const critico = root.querySelector('[data-clave="umbral_critico"]') as HTMLElement;
    expect(critico.querySelector('input')).toBeNull();
    expect(critico.textContent).toContain('-10');
    expect(critico.textContent).toContain('no editable');
    expect(root.textContent).not.toMatch(/Art\.\s*\d/);
  });

  it('muestra los rangos con coma decimal', () => {
    const preventivo = (fixture.nativeElement as HTMLElement).querySelector('[data-clave="umbral_preventivo"]')!;
    expect(preventivo.textContent).toContain('Entre -9,99 y -0,01.');
  });

  it('guarda sólo cuando hay cambios, notifica e invalida los parámetros vigentes', () => {
    const plazo = component.parametros[0];
    expect(component.tieneCambios(plazo)).toBeFalse();
    component.guardar(plazo);
    expect(api.actualizarParametro).not.toHaveBeenCalled();

    api.actualizarParametro.and.returnValue(of({ ...plazo, valor: 7, actualizado_por: 'Pérez, Ana' }));
    component.borradores[plazo.clave] = 7;
    component.guardar(plazo);

    expect(api.actualizarParametro).toHaveBeenCalledWith('plazo_descargo_dias_habiles', 7);
    expect(component.parametros[0].valor).toBe(7);
    expect(component.tieneCambios(component.parametros[0])).toBeFalse();
    expect(vigentes.invalidar).toHaveBeenCalled();
    expect(notifications.success).toHaveBeenCalledWith('Plazo de descargo actualizado.');
  });

  it('envía los decimales como texto', () => {
    const preventivo = component.parametros.find(p => p.clave === 'umbral_preventivo')!;
    api.actualizarParametro.and.returnValue(of({ ...preventivo, valor: '-8.5' }));
    component.borradores[preventivo.clave] = -8.5;
    component.guardar(preventivo);
    expect(api.actualizarParametro).toHaveBeenCalledWith('umbral_preventivo', '-8.5');
  });

  it('guarda el interruptor booleano desde el DOM', () => {
    const activo = component.parametros.find(p => p.clave === 'umbral_preventivo_activo')!;
    api.actualizarParametro.and.returnValue(of({ ...activo, valor: true }));
    const root: HTMLElement = fixture.nativeElement;
    const checkbox = root.querySelector('#param-umbral_preventivo_activo') as HTMLInputElement;
    checkbox.click();
    fixture.detectChanges();
    const boton = root.querySelector('[data-clave="umbral_preventivo_activo"] .btn-guardar') as HTMLButtonElement;
    boton.click();
    expect(api.actualizarParametro).toHaveBeenCalledWith('umbral_preventivo_activo', true);
  });

  it('guarda un correo y marca el campo inválido si el servidor lo rechaza', () => {
    const email = component.parametros.find(p => p.clave === 'email_tribunal_disciplina')!;
    api.actualizarParametro.and.returnValue(throwError(() => ({
      status: 400, error: { valor: ['Tribunal de Disciplina: ingresá un correo electrónico válido.'] }
    })));
    component.borradores[email.clave] = 'no-es-correo';
    component.guardar(email);
    fixture.detectChanges();

    expect(api.actualizarParametro).toHaveBeenCalledWith('email_tribunal_disciplina', 'no-es-correo');
    const input = (fixture.nativeElement as HTMLElement).querySelector('#param-email_tribunal_disciplina')!;
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(input.getAttribute('aria-describedby')).toContain('error-email_tribunal_disciplina');
    expect(input.getAttribute('spellcheck')).toBe('false');
    expect(notifications.error).toHaveBeenCalledWith('Tribunal de Disciplina: ingresá un correo electrónico válido.');
  });

  it('muestra el mensaje del servidor si el valor es inválido', () => {
    const plazo = component.parametros[0];
    api.actualizarParametro.and.returnValue(throwError(() => ({
      status: 400, error: { valor: ['Plazo de descargo debe estar entre 1 y 30 días hábiles.'] }
    })));
    component.borradores[plazo.clave] = 45;
    component.guardar(plazo);
    expect(notifications.error).toHaveBeenCalledWith('Plazo de descargo debe estar entre 1 y 30 días hábiles.');
    expect(component.guardando[plazo.clave]).toBeFalse();
  });

  it('descarta borradores y no envía valores vacíos', () => {
    const plazo = component.parametros[0];
    component.borradores[plazo.clave] = null;
    component.guardar(plazo);
    expect(api.actualizarParametro).not.toHaveBeenCalled();
    expect(notifications.error).toHaveBeenCalled();
    component.descartar(plazo);
    expect(component.borradores[plazo.clave]).toBe(5);
    expect(component.errores[plazo.clave]).toBeUndefined();
  });

  it('formatea valores para la lectura', () => {
    const [plazo, critico] = component.parametros;
    expect(component.formatearValor(critico, '-7.5')).toBe('-7,5');
    expect(component.formatearValor({ ...plazo, tipo: 'BOOLEAN' }, true)).toBe('Sí');
    expect(component.formatearValor(plazo, null)).toBe('—');
  });

  it('abre el historial en un panel tokenizado y evita duplicarlo con doble clic', () => {
    const respuesta = new Subject<CambioParametroDTO[]>();
    api.historialParametro.and.returnValue(respuesta);
    const abrir = spyOn(dialog, 'open').and.callThrough();

    component.verHistorial(component.parametros[0]);
    component.verHistorial(component.parametros[0]);
    respuesta.next([{ valor: 7, valor_anterior: 5, autor: 'Pérez, Ana', created_at: '2026-11-15T13:00:00Z' }]);
    respuesta.complete();
    component.verHistorial(component.parametros[0]);
    fixture.detectChanges();

    expect(api.historialParametro).toHaveBeenCalledTimes(1);
    expect(abrir).toHaveBeenCalledTimes(1);
    expect(abrir.calls.mostRecent().args[1]?.panelClass).toBe('aveit-dialog-panel');
    expect(overlayText()).toContain('Historial · Plazo de descargo');
    expect(overlayText()).toContain('15/11/2026 10:00');
    expect(overlay().querySelector('[role="region"][tabindex="0"]')).not.toBeNull();
  });

  it('notifica si falla la carga del historial', () => {
    api.historialParametro.and.returnValue(throwError(() => ({ status: 500 })));
    component.verHistorial(component.parametros[0]);
    expect(notifications.error).toHaveBeenCalledWith('No se pudo cargar el historial.');
    expect(component.cargandoHistorial).toBeFalse();
  });

  it('lista miembros del TD con su número de socio institucional', () => {
    const root: HTMLElement = fixture.nativeElement;
    const headers = Array.from(root.querySelectorAll('.miembros-table th')).map(h => h.textContent?.trim());
    expect(headers).toEqual(['N° de Socio', 'Apellido', 'Nombre', 'Año social', 'Email', 'Acciones']);
    const filas = root.querySelectorAll('.miembros-table tbody tr');
    const celdas = (fila: Element) => Array.from(fila.querySelectorAll('td')).map(td => td.textContent?.trim());
    expect(celdas(filas[0]).slice(0, 5)).toEqual(['1033', 'Toselli', 'Giuliano', '6.º', 'g@aveit.test']);
    expect(celdas(filas[1])[0]).toBe('S/D');
    expect(root.textContent).not.toContain('11239');
  });

  it('ofrece reintentar si falla la carga de miembros', () => {
    api.listarMiembrosTribunal.and.returnValue(throwError(() => ({ status: 500 })));
    component.cargarMiembros();
    fixture.detectChanges();
    expect(component.errorMiembros).toContain('No se pudo cargar la nómina');
    expect(notifications.error).toHaveBeenCalledWith(component.errorMiembros);
  });

  it('busca candidatos en el servidor a partir de dos caracteres', fakeAsync(() => {
    api.buscarCandidatosTribunal.and.returnValue(of([candidato()]));

    component.buscar('M');
    tick(300);
    expect(api.buscarCandidatosTribunal).not.toHaveBeenCalled();

    component.buscar('Moya');
    tick(300);
    expect(api.buscarCandidatosTribunal).toHaveBeenCalledOnceWith('Moya');
    expect(component.candidatos.map(s => s.id)).toEqual([9]);
    expect(component.buscandoCandidatos).toBeFalse();
  }));

  it('informa "Sin coincidencias" cuando el servidor no devuelve candidatos', fakeAsync(() => {
    component.abrirAlta();
    fixture.detectChanges();
    component.buscar('Zzz');
    tick(300);
    fixture.detectChanges();
    expect(component.sinCoincidencias).toBeTrue();
    expect(overlayText()).toContain('Sin coincidencias para «Zzz».');
    flush();
  }));

  it('selecciona un candidato desde el autocompletado sin romper búsquedas posteriores', fakeAsync(() => {
    api.buscarCandidatosTribunal.and.returnValue(of([candidato(), candidato({ id: 10, last_name: 'Mora' })]));
    component.abrirAlta();
    fixture.detectChanges();
    tick();

    const input = overlay().querySelector('#alta-busqueda') as HTMLInputElement;
    expect(input.getAttribute('aria-describedby')).toContain('alta-ayuda');
    input.focus();
    input.dispatchEvent(new Event('focusin'));
    input.value = 'Mo';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    tick(300);
    fixture.detectChanges();

    const opciones = overlay().querySelectorAll('mat-option');
    expect(opciones.length).toBe(2);
    (opciones[0] as HTMLElement).click();
    fixture.detectChanges();
    tick(300);

    expect(component.socioSeleccionado?.id).toBe(9);
    expect(input.value).toBe('Moya, Abril (N° de Socio 1201)');

    // La emisión del objeto seleccionado no debe propagarse como término de búsqueda.
    input.value = 'Mora';
    input.dispatchEvent(new Event('input'));
    tick(300);
    expect(api.buscarCandidatosTribunal).toHaveBeenCalledWith('Mora');
    expect(component.socioSeleccionado).toBeNull();
    flush();
  }));

  it('ignora el objeto emitido por el autocompletado al buscar', fakeAsync(() => {
    expect(() => {
      component.buscar(candidato());
      tick(300);
    }).not.toThrow();
    expect(api.buscarCandidatosTribunal).not.toHaveBeenCalled();
  }));

  it('designa al socio seleccionado y recarga la nómina', () => {
    api.asignarMiembroTribunal.and.returnValue(of({ ...miembros[0], id: 9, first_name: 'Abril', last_name: 'Moya' }));

    component.abrirAlta();
    component.confirmarAlta();
    expect(api.asignarMiembroTribunal).not.toHaveBeenCalled();

    component.seleccionar(candidato());
    component.confirmarAlta();

    expect(api.asignarMiembroTribunal).toHaveBeenCalledWith(9);
    expect(api.listarMiembrosTribunal).toHaveBeenCalledTimes(2);
    expect(notifications.success).toHaveBeenCalledWith('Abril Moya ahora integra el Tribunal de Disciplina.');
  });

  it('informa el rechazo del alta', () => {
    api.asignarMiembroTribunal.and.returnValue(throwError(() => ({
      status: 400, error: { detail: 'El socio ya integra el Tribunal de Disciplina.' }
    })));
    component.socioSeleccionado = candidato({ id: 1 });
    component.confirmarAlta();
    expect(notifications.error).toHaveBeenCalledWith('El socio ya integra el Tribunal de Disciplina.');
    expect(component.procesandoMiembro).toBeFalse();
  });

  it('revoca el rol tras confirmar, con botón de cierre y foco inicial en Cancelar', fakeAsync(() => {
    api.revocarMiembroTribunal.and.returnValue(of(undefined));
    const abrir = spyOn(dialog, 'open').and.callThrough();
    component.pedirRevocacion(miembros[0]);
    fixture.detectChanges();
    tick();
    expect(overlayText()).toContain('volverá a ser Socio Ordinario');
    expect(overlayText()).toContain('N° de Socio 1033');
    expect(abrir.calls.mostRecent().args[1]?.autoFocus).toBe('.btn-cancelar-revocar');
    expect(overlay().querySelector('#revocar-title')?.parentElement?.querySelector('.dialog-close')).not.toBeNull();

    component.confirmarRevocacion();

    expect(api.revocarMiembroTribunal).toHaveBeenCalledWith(1);
    expect(component.miembros.map(m => m.id)).toEqual([2]);
    expect(notifications.success).toHaveBeenCalledWith('Giuliano Toselli volvió a ser Socio Ordinario.');
    flush();
  }));

  it('notifica si la revocación falla y conserva la nómina', () => {
    api.revocarMiembroTribunal.and.returnValue(throwError(() => ({
      status: 404, error: { detail: 'El socio no integra el Tribunal de Disciplina.' }
    })));
    component.pedirRevocacion(miembros[0]);
    component.confirmarRevocacion();
    expect(notifications.error).toHaveBeenCalledWith('El socio no integra el Tribunal de Disciplina.');
    expect(component.miembros.length).toBe(2);
  });

  it('ofrece reintentar si falla la carga de parámetros', () => {
    api.listarParametros.and.returnValue(throwError(() => ({ status: 500 })));
    component.cargarParametros();
    fixture.detectChanges();
    expect(component.errorParametros).toContain('No se pudieron cargar');
    expect(notifications.error).toHaveBeenCalled();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Reintentar');
  });

  it('registra la ruta /admin/parametros protegida por TribunalGuard', () => {
    const ruta = AdminLayoutRoutes.find(r => r.path === 'admin/parametros');
    expect(ruta?.component).toBe(AdminParametrosComponent);
    expect(ruta?.canActivate).toContain(TribunalGuard);
  });
});
