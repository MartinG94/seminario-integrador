import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MisExpedientesComponent } from './mis-expedientes.component';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';

describe('MisExpedientesComponent', () => {
  let component: MisExpedientesComponent;
  let fixture: ComponentFixture<MisExpedientesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [MisExpedientesComponent],
      providers: [TribunalDataService]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MisExpedientesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  describe('Coloreado de Puntos Totales', () => {
    it('retorna clase verde para puntos >= 0', () => {
      expect(component.getColorClasePuntos(10)).toBe('puntos-verde');
      expect(component.getColorClasePuntos(0)).toBe('puntos-verde');
      expect(component.getHeaderClassPuntos(0)).toBe('card-header-success');
    });

    it('retorna clase gris para puntos < 0 y >= -7', () => {
      expect(component.getColorClasePuntos(-1)).toBe('puntos-gris');
      expect(component.getColorClasePuntos(-7)).toBe('puntos-gris');
      expect(component.getHeaderClassPuntos(-5)).toBe('card-header-secondary');
    });

    it('retorna clase amarillo para puntos < -7 y >= -9', () => {
      expect(component.getColorClasePuntos(-7.5)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-8)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-9)).toBe('puntos-amarillo');
      expect(component.getHeaderClassPuntos(-8)).toBe('card-header-warning');
    });

    it('retorna clase rojo para puntos < -9', () => {
      expect(component.getColorClasePuntos(-9.5)).toBe('puntos-rojo');
      expect(component.getColorClasePuntos(-15)).toBe('puntos-rojo');
      expect(component.getHeaderClassPuntos(-10)).toBe('card-header-danger');
    });
  });

  describe('Ordenamiento de tabla', () => {
    const mockExpedientes: Expediente[] = [
      {
        id: '1',
        numero: 'EXP-2026-002',
        tipo: 'falta',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Falta a reunión',
        subcomision: 'Deportes',
        puntos: -2,
        estado: 'creado',
        fechaCreacion: '2026-03-01',
        horasRestantes: 72
      },
      {
        id: '2',
        numero: 'EXP-2026-001',
        tipo: 'merito',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Reconocimiento',
        subcomision: 'Cultura',
        puntos: 5,
        estado: 'emitido',
        fechaCreacion: '2026-02-15',
        horasRestantes: 0
      }
    ];

    beforeEach(() => {
      component.misExpedientes = [...mockExpedientes];
    });

    it('ordena ascendentemente por defecto', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-001');
      expect(ordenados[1].numero).toBe('EXP-2026-002');
    });

    it('invierte orden al hacer click en la misma columna', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      component.cambiarOrden('numero');
      expect(component.ordenAscendente).toBeFalse();
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-002');
      expect(ordenados[1].numero).toBe('EXP-2026-001');
    });

    it('cambia columna y reinicia orden a ascendente', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = false;
      component.cambiarOrden('motivo');
      expect(component.columnaOrden).toBe('motivo');
      expect(component.ordenAscendente).toBeTrue();
    });
  });
});
