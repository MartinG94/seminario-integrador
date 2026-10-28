import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { By } from '@angular/platform-browser';
import { of, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import {
  ArticuloReglamentoDTO,
  ExpedienteApiService
} from '../services/expediente-api.service';
import { NotificationService } from '../services/notification.service';
import { ReglamentosComponent } from './reglamentos.component';

describe('ReglamentosComponent', () => {
  let component: ReglamentosComponent;
  let fixture: ComponentFixture<ReglamentosComponent>;
  let expedienteServiceSpy: jasmine.SpyObj<ExpedienteApiService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let notificationServiceSpy: jasmine.SpyObj<NotificationService>;

  const mockArticulosInterno: ArticuloReglamentoDTO[] = [
    {
      id: 1,
      titulo: 'Reglamento Interno',
      seccion: 1,
      articulo: 14,
      inciso: 'a',
      cuerpo: 'El socio debe respetar las instalaciones y elementos comunes.',
      descripcion: 'El socio debe respetar las instalaciones y elementos comunes.',
      cita_corta: 'Art. 14 inc. a',
      cita_completa: 'Art. 14 inc. a - Reglamento Interno',
      activo: true,
      created_at: '2026-10-27T10:00:00Z',
      updated_at: '2026-10-27T10:00:00Z'
    },
    {
      id: 2,
      titulo: 'Reglamento Interno',
      seccion: 1,
      articulo: 15,
      inciso: '-',
      cuerpo: 'Es falta grave la agresión física o verbal entre miembros.',
      descripcion: 'Es falta grave la agresión física o verbal entre miembros.',
      cita_corta: 'Art. 15',
      cita_completa: 'Art. 15 - Reglamento Interno',
      activo: true,
      created_at: '2026-10-27T10:00:00Z',
      updated_at: '2026-10-27T10:00:00Z'
    }
  ];

  const mockArticulosEstatuto: ArticuloReglamentoDTO[] = [
    {
      id: 3,
      titulo: 'Estatuto',
      seccion: 1,
      articulo: 2,
      inciso: '-',
      cuerpo: 'El domicilio legal de la Asociación se fija en la Ciudad de Córdoba.',
      descripcion: 'El domicilio legal de la Asociación se fija en la Ciudad de Córdoba.',
      cita_corta: 'Art. 2',
      cita_completa: 'Art. 2 - Estatuto',
      activo: true,
      created_at: '2026-10-27T10:00:00Z',
      updated_at: '2026-10-27T10:00:00Z'
    }
  ];

  beforeEach(async () => {
    expedienteServiceSpy = jasmine.createSpyObj('ExpedienteApiService', [
      'listarArticulosReglamento',
      'crearArticuloReglamento',
      'actualizarArticuloReglamento',
      'eliminarArticuloReglamento'
    ]);
    authServiceSpy = jasmine.createSpyObj('AuthService', ['tieneRol']);
    notificationServiceSpy = jasmine.createSpyObj('NotificationService', [
      'success',
      'error',
      'warning',
      'info'
    ]);

    expedienteServiceSpy.listarArticulosReglamento.and.returnValue(of(mockArticulosInterno));
    authServiceSpy.tieneRol.and.returnValue(true);

    await TestBed.configureTestingModule({
      imports: [FormsModule, MatButtonModule, MatTooltipModule],
      declarations: [ReglamentosComponent],
      providers: [
        { provide: ExpedienteApiService, useValue: expedienteServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: NotificationService, useValue: notificationServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ReglamentosComponent);
    component = fixture.componentInstance;
  });

  it('debe crearse correctamente e inicializar en Reglamento Interno', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(component.tabActiva).toBe('Reglamento Interno');
    expect(expedienteServiceSpy.listarArticulosReglamento).toHaveBeenCalledWith({
      titulo: 'Reglamento Interno',
      search: undefined
    });
    expect(component.articulos.length).toBe(2);
  });

  describe('Pestañas y Navegación', () => {
    it('cambia de pestaña entre Reglamento Interno y Estatuto recargando los datos', () => {
      fixture.detectChanges();
      expedienteServiceSpy.listarArticulosReglamento.and.returnValue(of(mockArticulosEstatuto));

      component.seleccionarPestaña('Estatuto');
      fixture.detectChanges();

      expect(component.tabActiva).toBe('Estatuto');
      expect(expedienteServiceSpy.listarArticulosReglamento).toHaveBeenCalledWith({
        titulo: 'Estatuto',
        search: undefined
      });
      expect(component.articulos).toEqual(mockArticulosEstatuto);
    });

    it('no recarga si se hace click en la misma pestaña activa', () => {
      fixture.detectChanges();
      expedienteServiceSpy.listarArticulosReglamento.calls.reset();

      component.seleccionarPestaña('Reglamento Interno');
      expect(expedienteServiceSpy.listarArticulosReglamento).not.toHaveBeenCalled();
    });
  });

  describe('Estructura de Tabla y Encabezados', () => {
    it('renderiza los 4 encabezados canónicos cuando el usuario tiene permisos de gestión', () => {
      authServiceSpy.tieneRol.and.returnValue(true);
      fixture.detectChanges();

      const headers = fixture.debugElement.queryAll(By.css('thead th'));
      expect(headers.length).toBe(4);
      const textHeaders = headers.map(h => h.nativeElement.textContent.trim());
      expect(textHeaders).toEqual(['Artículo', 'Inciso', 'Cuerpo', 'Acciones']);
    });

    it('renderiza correctamente las filas con los datos de los artículos', () => {
      fixture.detectChanges();

      const rows = fixture.debugElement.queryAll(By.css('tbody tr'));
      expect(rows.length).toBe(2);

      const firstRowCols = rows[0].queryAll(By.css('td'));
      expect(firstRowCols[0].nativeElement.textContent.trim()).toBe('Art. 14');
      expect(firstRowCols[1].nativeElement.textContent.trim()).toBe('a');
      expect(firstRowCols[2].nativeElement.textContent.trim()).toContain('El socio debe respetar');
    });
  });

  describe('Búsqueda Reactiva', () => {
    it('filtra artículos según el término de búsqueda al cambiar el modelo', () => {
      fixture.detectChanges();

      component.busqueda = 'instalaciones';
      component.onSearchChange();

      expect(expedienteServiceSpy.listarArticulosReglamento).toHaveBeenCalledWith({
        titulo: 'Reglamento Interno',
        search: 'instalaciones'
      });
    });
  });

  describe('Control de Acceso basado en Roles (RBAC)', () => {
    it('muestra el botón + Agregar artículo y acciones de edición/baja cuando el rol es TD, CD o ADMIN', () => {
      authServiceSpy.tieneRol.and.returnValue(true);
      fixture.detectChanges();

      const addBtn = fixture.debugElement.query(By.css('.actions-box button'));
      expect(addBtn).not.toBeNull();
      expect(addBtn.nativeElement.textContent).toContain('+ Agregar artículo');

      const actionHeader = fixture.debugElement.query(By.css('thead th.col-acciones'));
      expect(actionHeader).not.toBeNull();

      const actionButtons = fixture.debugElement.queryAll(By.css('td.td-actions button'));
      expect(actionButtons.length).toBeGreaterThan(0);
    });

    it('oculta el botón + Agregar artículo y la columna de acciones cuando el rol es SOCIO', () => {
      authServiceSpy.tieneRol.and.returnValue(false);
      fixture.detectChanges();

      const addBtn = fixture.debugElement.query(By.css('.actions-box button'));
      expect(addBtn).toBeNull();

      const headers = fixture.debugElement.queryAll(By.css('thead th'));
      expect(headers.length).toBe(3);
      const textHeaders = headers.map(h => h.nativeElement.textContent.trim());
      expect(textHeaders).toEqual(['Artículo', 'Inciso', 'Cuerpo']);

      const actionCells = fixture.debugElement.queryAll(By.css('td.td-actions'));
      expect(actionCells.length).toBe(0);
    });
  });

  describe('Modal de Creación y Edición', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('abre el modal en modo creación con campos limpios', () => {
      component.abrirModalCrear();
      fixture.detectChanges();

      expect(component.modalAbierto).toBeTrue();
      expect(component.modoEdicion).toBeFalse();
      expect(component.articulo).toBeNull();
      expect(component.inciso).toBe('');
      expect(component.cuerpo).toBe('');

      const modalHeader = fixture.debugElement.query(By.css('.modal-dialog-custom .card-title'));
      expect(modalHeader.nativeElement.textContent).toContain('Agregar Artículo — Reglamento Interno');
    });

    it('valida campos obligatorios antes de guardar', () => {
      component.abrirModalCrear();
      component.articulo = 0;
      component.cuerpo = '';

      component.guardarArticulo();

      expect(expedienteServiceSpy.crearArticuloReglamento).not.toHaveBeenCalled();
      expect(notificationServiceSpy.warning).toHaveBeenCalled();
    });

    it('crea un artículo con éxito, notifica y recarga el listado', () => {
      const createdArt: ArticuloReglamentoDTO = {
        ...mockArticulosInterno[0],
        id: 10,
        articulo: 16,
        inciso: 'b',
        cuerpo: 'Nuevo artículo reglamentario.'
      };
      expedienteServiceSpy.crearArticuloReglamento.and.returnValue(of(createdArt));

      component.abrirModalCrear();
      component.articulo = 16;
      component.inciso = 'b';
      component.cuerpo = 'Nuevo artículo reglamentario.';

      component.guardarArticulo();

      expect(expedienteServiceSpy.crearArticuloReglamento).toHaveBeenCalledWith({
        titulo: 'Reglamento Interno',
        articulo: 16,
        inciso: 'b',
        cuerpo: 'Nuevo artículo reglamentario.'
      });
      expect(notificationServiceSpy.success).toHaveBeenCalledWith('Artículo creado con éxito.');
      expect(component.modalAbierto).toBeFalse();
    });

    it('notifica error al fallar la creación en el servidor', () => {
      expedienteServiceSpy.crearArticuloReglamento.and.returnValue(
        throwError(() => ({ status: 400, error: { detail: 'Ya existe un artículo activo con la misma numeración.' } }))
      );

      component.abrirModalCrear();
      component.articulo = 14;
      component.inciso = 'a';
      component.cuerpo = 'Conflicto';

      component.guardarArticulo();

      expect(notificationServiceSpy.error).toHaveBeenCalledWith('Ya existe un artículo activo con la misma numeración.');
      expect(component.modalAbierto).toBeTrue();
    });

    it('abre el modal en modo edición cargando los datos del artículo seleccionado', () => {
      component.abrirModalEditar(mockArticulosInterno[0]);
      fixture.detectChanges();

      expect(component.modalAbierto).toBeTrue();
      expect(component.modoEdicion).toBeTrue();
      expect(component.articuloEnEdicionId).toBe(1);
      expect(component.articulo).toBe(14);
      expect(component.inciso).toBe('a');
      expect(component.cuerpo).toBe('El socio debe respetar las instalaciones y elementos comunes.');

      const modalHeader = fixture.debugElement.query(By.css('.modal-dialog-custom .card-title'));
      expect(modalHeader.nativeElement.textContent).toContain('Editar Artículo — Reglamento Interno');
    });

    it('actualiza un artículo con éxito y notifica', () => {
      const updatedArt: ArticuloReglamentoDTO = {
        ...mockArticulosInterno[0],
        cuerpo: 'Texto actualizado'
      };
      expedienteServiceSpy.actualizarArticuloReglamento.and.returnValue(of(updatedArt));

      component.abrirModalEditar(mockArticulosInterno[0]);
      component.cuerpo = 'Texto actualizado';

      component.guardarArticulo();

      expect(expedienteServiceSpy.actualizarArticuloReglamento).toHaveBeenCalledWith(1, {
        articulo: 14,
        inciso: 'a',
        cuerpo: 'Texto actualizado'
      });
      expect(notificationServiceSpy.success).toHaveBeenCalledWith('Artículo modificado con éxito.');
      expect(component.modalAbierto).toBeFalse();
    });
  });

  describe('Modal de Eliminación (Baja Lógica)', () => {
    beforeEach(() => {
      fixture.detectChanges();
    });

    it('abre el modal de confirmación con el texto institucional correspondiente', () => {
      component.abrirModalEliminar(mockArticulosInterno[0]);
      fixture.detectChanges();

      expect(component.modalEliminarAbierto).toBeTrue();
      expect(component.articuloAEliminar).toBe(mockArticulosInterno[0]);

      const bodyText = fixture.debugElement.query(By.css('.modal-confirmacion-dialog .card-body p'));
      expect(bodyText.nativeElement.textContent).toContain('Art. 14 inc. a');
      expect(bodyText.nativeElement.textContent).toContain('Reglamento Interno');
      expect(bodyText.nativeElement.textContent).toContain('Ya no estará disponible para nuevos expedientes ni resoluciones');
    });

    it('confirma la eliminación, llama al endpoint de borrado lógico y notifica', () => {
      expedienteServiceSpy.eliminarArticuloReglamento.and.returnValue(of(undefined as any));

      component.abrirModalEliminar(mockArticulosInterno[0]);
      component.confirmarEliminar();

      expect(expedienteServiceSpy.eliminarArticuloReglamento).toHaveBeenCalledWith(1);
      expect(notificationServiceSpy.success).toHaveBeenCalledWith('Artículo eliminado con éxito.');
      expect(component.modalEliminarAbierto).toBeFalse();
    });

    it('notifica error si la eliminación falla', () => {
      expedienteServiceSpy.eliminarArticuloReglamento.and.returnValue(
        throwError(() => ({ status: 500, error: {} }))
      );

      component.abrirModalEliminar(mockArticulosInterno[0]);
      component.confirmarEliminar();

      expect(notificationServiceSpy.error).toHaveBeenCalledWith('No se pudo eliminar el artículo.');
      expect(component.modalEliminarAbierto).toBeTrue();
    });
  });
});
