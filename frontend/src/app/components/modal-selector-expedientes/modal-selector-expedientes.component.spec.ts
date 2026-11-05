import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { By } from '@angular/platform-browser';
import { SimpleChange } from '@angular/core';
import { ModalSelectorExpedientesComponent } from './modal-selector-expedientes.component';
import { ModalScrollLockService } from '../../services/modal-scroll-lock.service';
import { AntecedenteT03DTO } from '../../services/expediente-api.service';

describe('ModalSelectorExpedientesComponent', () => {
  let component: ModalSelectorExpedientesComponent;
  let fixture: ComponentFixture<ModalSelectorExpedientesComponent>;
  let scrollLockServiceSpy: jasmine.SpyObj<ModalScrollLockService>;

  const mockCatalogo: AntecedenteT03DTO[] = [
    {
      id: 1,
      numero: 'EXP-0001/2026',
      fecha_emision: '2026-02-10T12:00:00Z',
      motivo: 'Falta disciplinaria grave',
      reglamento_invocado: 'Estatuto Art. 10',
      titulo: 'Sanción disciplinaria 1',
      puntos: -2.0,
      tipo_accion: 'SANCTION'
    },
    {
      id: 2,
      numero: 'EXP-0002/2026',
      fecha_emision: '2026-02-15T12:00:00Z',
      motivo: 'Aporte extraordinario al laboratorio',
      reglamento_invocado: 'Reglamento Interno Art. 4',
      titulo: 'Reconocimiento 2',
      puntos: 1.5,
      tipo_accion: 'MERIT'
    },
    {
      id: 3,
      numero: 'EXP-0003/2026',
      fecha_emision: '2026-02-20T12:00:00Z',
      motivo: 'Incumplimiento de guardia',
      reglamento_invocado: 'Reglamento Interno Art. 8',
      titulo: 'Sanción 3',
      puntos: -1.0,
      tipo_accion: 'SANCTION'
    }
  ];

  beforeEach(async () => {
    scrollLockServiceSpy = jasmine.createSpyObj('ModalScrollLockService', ['lock', 'unlock']);

    await TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [ModalSelectorExpedientesComponent],
      providers: [
        { provide: ModalScrollLockService, useValue: scrollLockServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ModalSelectorExpedientesComponent);
    component = fixture.componentInstance;
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe bloquear el scroll al abrirse y desbloquearlo al destruirse o cerrarse', fakeAsync(() => {
    component.abierto = true;
    component.ngOnChanges({
      abierto: new SimpleChange(false, true, true)
    });
    tick(150);

    expect(scrollLockServiceSpy.lock).toHaveBeenCalled();

    component.onCerrar();
    expect(scrollLockServiceSpy.unlock).toHaveBeenCalled();
  }));

  it('debe filtrar por pestañas TODOS, SANCTION y MERIT', () => {
    component.catalogo = mockCatalogo;
    component.abierto = true;
    fixture.detectChanges();

    expect(component.expedientesFiltrados.length).toBe(3);

    component.setFiltroTipo('SANCTION');
    expect(component.expedientesFiltrados.length).toBe(2);

    component.setFiltroTipo('MERIT');
    expect(component.expedientesFiltrados.length).toBe(1);
    expect(component.expedientesFiltrados[0].id).toBe(2);

    component.setFiltroTipo('TODOS');
    expect(component.expedientesFiltrados.length).toBe(3);
  });

  it('debe filtrar en tiempo real por número, título o motivo', () => {
    component.catalogo = mockCatalogo;
    component.abierto = true;
    component.filtroTexto = 'laboratorio';
    fixture.detectChanges();

    expect(component.expedientesFiltrados.length).toBe(1);
    expect(component.expedientesFiltrados[0].id).toBe(2);

    component.filtroTexto = '2/2026';
    expect(component.expedientesFiltrados.length).toBe(1);
    expect(component.expedientesFiltrados[0].id).toBe(2);

    component.filtroTexto = 'inexistente_xyz';
    expect(component.expedientesFiltrados.length).toBe(0);
  });

  it('debe seleccionar y deseleccionar expedientes mediante toggleExpediente', () => {
    component.catalogo = mockCatalogo;
    component.abierto = true;
    component.seleccionados = [mockCatalogo[0]];
    component.ngOnChanges({
      abierto: new SimpleChange(false, true, true)
    });

    expect(component.estaSeleccionado(1)).toBeTrue();
    expect(component.estaSeleccionado(2)).toBeFalse();

    component.toggleExpediente(mockCatalogo[1]);
    expect(component.estaSeleccionado(2)).toBeTrue();
    expect(component.seleccionadosLocales.length).toBe(2);

    component.toggleExpediente(mockCatalogo[0]);
    expect(component.estaSeleccionado(1)).toBeFalse();
    expect(component.seleccionadosLocales.length).toBe(1);
  });

  it('debe limpiar la selección con limpiarSeleccion', () => {
    component.seleccionadosLocales = [...mockCatalogo];
    expect(component.seleccionadosLocales.length).toBe(3);

    component.limpiarSeleccion();
    expect(component.seleccionadosLocales.length).toBe(0);
  });

  it('debe emitir seleccionadosChange y cerrar al confirmar', () => {
    spyOn(component.seleccionadosChange, 'emit');
    spyOn(component.cerrar, 'emit');

    component.seleccionadosLocales = [mockCatalogo[1]];
    component.confirmar();

    expect(component.seleccionadosChange.emit).toHaveBeenCalledWith([mockCatalogo[1]]);
    expect(component.cerrar.emit).toHaveBeenCalled();
  });

  it('debe cerrar al presionar la tecla Escape', () => {
    spyOn(component.cerrar, 'emit');

    const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    component.onKeydown(escapeEvent);

    expect(component.cerrar.emit).toHaveBeenCalled();
  });
});
