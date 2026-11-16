import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { OverlayContainer } from '@angular/cdk/overlay';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { AdminParametrosComponent } from './admin-parametros.component';
import { AdminApiService, MiembroTribunalDTO, ParametroSistemaDTO } from '../../../services/admin-api.service';
import { NotificationService } from '../../../services/notification.service';
import { SocioApiService, SocioListItemDTO } from '../../../services/socio-api.service';

function parametro(over: Partial<ParametroSistemaDTO>): ParametroSistemaDTO {
  return {
    clave: 'plazo_descargo_dias_habiles', categoria: 'PLAZOS', etiqueta: 'Plazo de descargo',
    descripcion: 'Días hábiles', tipo: 'INTEGER', unidad: 'días hábiles', editable: true,
    minimo: '1', maximo: '30', valor: 5, valor_inicial: 5, actualizado_at: null, actualizado_por: '',
    ...over
  };
}

describe('AdminParametrosComponent', () => {
  let fixture: ComponentFixture<AdminParametrosComponent>;
  let component: AdminParametrosComponent;
  let api: jasmine.SpyObj<AdminApiService>;
  let socioApi: jasmine.SpyObj<SocioApiService>;
  let notifications: jasmine.SpyObj<NotificationService>;

  const parametros: ParametroSistemaDTO[] = [
    parametro({}),
    parametro({ clave: 'umbral_critico', categoria: 'UMBRALES', etiqueta: 'Umbral crítico', tipo: 'DECIMAL',
      editable: false, minimo: null, maximo: null, valor: '-10.0', valor_inicial: '-10.0', unidad: 'puntos' }),
    parametro({ clave: 'umbral_preventivo', categoria: 'UMBRALES', etiqueta: 'Umbral preventivo', tipo: 'DECIMAL',
      minimo: '-9.99', maximo: '-0.01', valor: '-7.0', valor_inicial: '-7.0', unidad: 'puntos' }),
    parametro({ clave: 'email_tribunal_disciplina', categoria: 'CORREOS', etiqueta: 'Tribunal de Disciplina',
      tipo: 'EMAIL', minimo: null, maximo: null, valor: 'td@aveit.test', valor_inicial: 'td@aveit.test', unidad: '' }),
    parametro({ clave: 'adjuntos_cantidad_maxima', categoria: 'ADJUNTOS', etiqueta: 'Cantidad máxima',
      maximo: '10', unidad: 'comprobantes', actualizado_por: 'Pérez, Ana (403655)',
      actualizado_at: '2026-11-15T10:00:00-03:00' }),
  ];
  const miembros: MiembroTribunalDTO[] = [
    { id: 1, legajo: '11239', last_name: 'Toselli', first_name: 'Giuliano', social_year: 6,
      email: 'g@aveit.test', subcomision: null },
    { id: 2, legajo: '11737', last_name: 'Cerda', first_name: 'Catalina', social_year: 5,
      email: 'c@aveit.test', subcomision: null },
  ];

  beforeEach(async () => {
    api = jasmine.createSpyObj('AdminApiService', ['listarParametros', 'actualizarParametro', 'historialParametro',
      'listarMiembrosTribunal', 'asignarMiembroTribunal', 'revocarMiembroTribunal']);
    api.listarParametros.and.returnValue(of(parametros.map(p => ({ ...p }))));
    api.listarMiembrosTribunal.and.returnValue(of([...miembros]));
    socioApi = jasmine.createSpyObj('SocioApiService', ['searchSocios']);
    notifications = jasmine.createSpyObj('NotificationService', ['success', 'error']);

    await TestBed.configureTestingModule({
      imports: [FormsModule, MatDialogModule, MatAutocompleteModule, NoopAnimationsModule],
      declarations: [AdminParametrosComponent],
      providers: [
        { provide: AdminApiService, useValue: api },
        { provide: SocioApiService, useValue: socioApi },
        { provide: NotificationService, useValue: notifications },
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(AdminParametrosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => TestBed.inject(MatDialog).closeAll());

  const overlayText = (): string =>
    TestBed.inject(OverlayContainer).getContainerElement().textContent || '';

  it('muestra las cuatro tarjetas temáticas con sus parámetros', () => {
    const root: HTMLElement = fixture.nativeElement;
    const titulos = Array.from(root.querySelectorAll('.admin-card h4')).map(h => h.textContent?.trim());
    expect(titulos).toEqual(['Plazos', 'Umbrales de puntos', 'Correos institucionales', 'Comprobantes adjuntos']);
    expect(component.parametrosDe('UMBRALES').length).toBe(2);
    expect(root.textContent).toContain('Último cambio: Pérez, Ana (403655)');
  });

  it('muestra el umbral crítico como valor reglamentario sin campo editable', () => {
    const root: HTMLElement = fixture.nativeElement;
    const critico = root.querySelector('[data-clave="umbral_critico"]') as HTMLElement;
    expect(critico.querySelector('input')).toBeNull();
    expect(critico.textContent).toContain('-10');
    expect(critico.textContent).toContain('no editable');
  });

  it('guarda sólo cuando hay cambios y notifica el resultado', () => {
    const plazo = component.parametros[0];
    expect(component.tieneCambios(plazo)).toBeFalse();
    component.guardar(plazo);
    expect(api.actualizarParametro).not.toHaveBeenCalled();

    api.actualizarParametro.and.returnValue(of({ ...plazo, valor: 7, actualizado_por: 'Pérez, Ana (403655)' }));
    component.borradores[plazo.clave] = 7;
    component.guardar(plazo);

    expect(api.actualizarParametro).toHaveBeenCalledWith('plazo_descargo_dias_habiles', 7);
    expect(component.parametros[0].valor).toBe(7);
    expect(component.tieneCambios(component.parametros[0])).toBeFalse();
    expect(notifications.success).toHaveBeenCalledWith('Plazo de descargo actualizado.');
  });

  it('envía los decimales como texto', () => {
    const preventivo = component.parametros.find(p => p.clave === 'umbral_preventivo')!;
    api.actualizarParametro.and.returnValue(of({ ...preventivo, valor: '-8.5' }));
    component.borradores[preventivo.clave] = -8.5;
    component.guardar(preventivo);
    expect(api.actualizarParametro).toHaveBeenCalledWith('umbral_preventivo', '-8.5');
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
  });

  it('formatea valores para la lectura', () => {
    const [plazo, critico] = component.parametros;
    expect(component.formatearValor(critico, '-7.5')).toBe('-7,5');
    expect(component.formatearValor({ ...plazo, tipo: 'BOOLEAN' }, true)).toBe('Sí');
    expect(component.formatearValor(plazo, null)).toBe('—');
  });

  it('abre el historial de un parámetro', () => {
    api.historialParametro.and.returnValue(of([
      { valor: 7, valor_anterior: 5, autor: 'Pérez, Ana (403655)', created_at: '2026-11-15T10:00:00-03:00' }
    ]));
    component.verHistorial(component.parametros[0]);
    expect(api.historialParametro).toHaveBeenCalledWith('plazo_descargo_dias_habiles');
    expect(component.historial.length).toBe(1);
    fixture.detectChanges();
    expect(overlayText()).toContain('Historial · Plazo de descargo');
  });

  it('lista miembros del TD en columnas atómicas', () => {
    const root: HTMLElement = fixture.nativeElement;
    const headers = Array.from(root.querySelectorAll('.miembros-table th')).map(h => h.textContent?.trim());
    expect(headers).toEqual(['N° de Socio', 'Apellido', 'Nombre', 'Año social', 'Email', 'Acciones']);
    const celdas = Array.from(root.querySelectorAll('.miembros-table tbody tr:first-child td'))
      .map(td => td.textContent?.trim());
    expect(celdas.slice(0, 5)).toEqual(['11239', 'Toselli', 'Giuliano', '6.º', 'g@aveit.test']);
  });

  it('busca socios de forma reactiva y sólo ofrece Socios Ordinarios', fakeAsync(() => {
    const resultados: SocioListItemDTO[] = [
      { id: 9, legajo: '12123', first_name: 'Abril', last_name: 'Moya', email: '', role: 'SOCIO',
        category: 'ACTIVE', category_display: 'Activo', subcomision: null },
      { id: 10, legajo: '87414', first_name: 'Dir', last_name: 'Ectivo', email: '', role: 'CD',
        category: 'ACTIVE', category_display: 'Activo', subcomision: null },
    ];
    socioApi.searchSocios.and.returnValue(of({ count: 2, next: null, previous: null, results: resultados }));

    component.buscar('M');
    tick(300);
    expect(socioApi.searchSocios).not.toHaveBeenCalled();

    component.buscar('Moya');
    tick(300);
    expect(socioApi.searchSocios).toHaveBeenCalledOnceWith('Moya');
    expect(component.candidatos.map(s => s.id)).toEqual([9]);
  }));

  it('designa al socio seleccionado y recarga la nómina', () => {
    const socio = { id: 9, legajo: '12123', first_name: 'Abril', last_name: 'Moya', email: '', role: 'SOCIO',
      category: 'ACTIVE', category_display: 'Activo', subcomision: null } as SocioListItemDTO;
    api.asignarMiembroTribunal.and.returnValue(of({ ...miembros[0], id: 9, first_name: 'Abril', last_name: 'Moya' }));

    component.abrirAlta();
    component.confirmarAlta();
    expect(api.asignarMiembroTribunal).not.toHaveBeenCalled();

    component.seleccionar(socio);
    component.confirmarAlta();

    expect(api.asignarMiembroTribunal).toHaveBeenCalledWith(9);
    expect(api.listarMiembrosTribunal).toHaveBeenCalledTimes(2);
    expect(notifications.success).toHaveBeenCalledWith('Abril Moya ahora integra el Tribunal de Disciplina.');
  });

  it('informa el rechazo del alta', () => {
    api.asignarMiembroTribunal.and.returnValue(throwError(() => ({
      status: 400, error: { detail: 'El socio ya integra el Tribunal de Disciplina.' }
    })));
    component.socioSeleccionado = { id: 1 } as SocioListItemDTO;
    component.confirmarAlta();
    expect(notifications.error).toHaveBeenCalledWith('El socio ya integra el Tribunal de Disciplina.');
  });

  it('revoca el rol tras confirmar', () => {
    api.revocarMiembroTribunal.and.returnValue(of(undefined));
    component.pedirRevocacion(miembros[0]);
    fixture.detectChanges();
    expect(overlayText()).toContain('volverá a ser Socio Ordinario');

    component.confirmarRevocacion();

    expect(api.revocarMiembroTribunal).toHaveBeenCalledWith(1);
    expect(component.miembros.map(m => m.id)).toEqual([2]);
    expect(notifications.success).toHaveBeenCalledWith('Giuliano Toselli volvió a ser Socio Ordinario.');
  });

  it('ofrece reintentar si falla la carga', () => {
    api.listarParametros.and.returnValue(throwError(() => ({ status: 500 })));
    component.cargarParametros();
    fixture.detectChanges();
    expect(component.errorParametros).toContain('No se pudieron cargar');
    expect(notifications.error).toHaveBeenCalled();
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Reintentar');
  });
});
