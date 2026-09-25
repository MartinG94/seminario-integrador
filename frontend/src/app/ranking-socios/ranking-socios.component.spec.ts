import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { of, throwError } from 'rxjs';

import { RankingSociosComponent } from './ranking-socios.component';
import { RankingService } from '../services/ranking.service';
import { RankingSocio } from './ranking-socio.model';

describe('RankingSociosComponent', () => {
  let component: RankingSociosComponent;
  let fixture: ComponentFixture<RankingSociosComponent>;
  let rankingServiceSpy: jasmine.SpyObj<RankingService>;

  const sociosMock: RankingSocio[] = [
    {
      id: '1',
      legajo: '1001',
      nombre: 'Ana',
      apellido: 'Gómez',
      categoria: 'ACTIVO',
      subcomision: 'Cómputos',
      saldo: 5,
      saldoHistorico: 5,
      saldoPuntajeGeneral: 5,
      diferencia: 0,
      reconciliado: true
    },
    {
      id: '2',
      legajo: '1002',
      nombre: 'Bruno',
      apellido: 'Pérez',
      categoria: 'PASIVO',
      subcomision: 'Deportes',
      saldo: -1,
      saldoHistorico: -1,
      saldoPuntajeGeneral: -1,
      diferencia: 0,
      reconciliado: true
    }
  ];

  beforeEach(async () => {
    rankingServiceSpy = jasmine.createSpyObj('RankingService', ['obtenerRanking']);
    rankingServiceSpy.obtenerRanking.and.returnValue(of(sociosMock));

    await TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [RankingSociosComponent],
      providers: [
        { provide: RankingService, useValue: rankingServiceSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RankingSociosComponent);
    component = fixture.componentInstance;
  });

  it('debería crear el componente', () => {
    expect(component).toBeTruthy();
  });

  it('debería cargar socios desde RankingService', () => {
    fixture.detectChanges();

    expect(component.socios.length).toBe(2);
    expect(component.cargando).toBeFalse();
    expect(component.error).toBeNull();
    expect(component.subcomisiones).toEqual(['Cómputos', 'Deportes']);
  });

  it('debería filtrar socios por categoría', () => {
    fixture.detectChanges();

    component.filtroCategoria = 'ACTIVO';

    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].nombre).toBe('Ana');
  });

  it('debería filtrar socios por texto', () => {
    fixture.detectChanges();

    component.filtroTexto = 'bruno';

    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].apellido).toBe('Pérez');
  });

  it('debería mostrar estado de error si falla la carga', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      throwError(() => new Error('Error de red'))
    );

    fixture.detectChanges();

    expect(component.socios).toEqual([]);
    expect(component.cargando).toBeFalse();
    expect(component.error).toBe('No se pudo cargar el ranking. Intentá nuevamente.');
  });

  it('debería ordenar por mérito y desempatar por apellido y nombre', () => {
    const crearSocio = (id: string, apellido: string, nombre: string, saldo: number): RankingSocio => ({
      id, legajo: id, apellido, nombre, saldo,
      categoria: 'ACTIVO', subcomision: 'Cómputos'
    });
    rankingServiceSpy.obtenerRanking.and.returnValue(of([
      crearSocio('1', 'Zapata', 'Ana', 5),
      crearSocio('2', 'Alonso', 'Bruno', 5),
      crearSocio('3', 'Alonso', 'Ana', 5),
      crearSocio('4', 'Zapata', 'Zoe', 10),
      crearSocio('5', 'Abad', 'Ana', -2)
    ]));
    fixture.detectChanges();
    component.criterioOrden = 'merito';

    expect(component.sociosOrdenados.map(s => s.id)).toEqual(['4', '3', '2', '1', '5']);
  });

  it('debería ordenar por sanción de menor a mayor saldo', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(of([
      { ...sociosMock[0], id: '1', saldo: 5 },
      { ...sociosMock[1], id: '2', saldo: -1 },
      { ...sociosMock[0], id: '3', saldo: -8 },
      { ...sociosMock[1], id: '4', saldo: 0 }
    ]));
    fixture.detectChanges();
    component.criterioOrden = 'sancion';

    expect(component.sociosOrdenados.map(s => s.id)).toEqual(['3', '2', '4', '1']);
  });

  it('debería paginar 13 socios en una primera página de 10 y una segunda de 3', () => {
    const sociosPagina: RankingSocio[] = Array.from({ length: 13 }, (_, i) => ({
      ...sociosMock[0], id: String(i + 1), legajo: String(2001 + i), saldo: 13 - i
    }));
    rankingServiceSpy.obtenerRanking.and.returnValue(of(sociosPagina));
    fixture.detectChanges();

    expect(component.totalPaginas).toBe(2);
    expect(component.sociosPaginados.length).toBe(10);
    expect(component.sociosPaginados.map(s => s.id)).toEqual([
      '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'
    ]);

    component.cambiarPagina(2);

    expect(component.paginaActual).toBe(2);
    expect(component.sociosPaginados.length).toBe(3);
    expect(component.sociosPaginados.map(s => s.id)).toEqual(['11', '12', '13']);
    expect(component.totalPaginas).toBe(2);
  });

  it('debería cambiar el criterio de orden y volver a la primera página', () => {
    fixture.detectChanges();
    component.paginaActual = 2;

    component.setOrden('sancion');

    expect(component.criterioOrden).toBe('sancion');
    expect(component.paginaActual).toBe(1);

    component.paginaActual = 2;
    component.setOrden('merito');

    expect(component.criterioOrden).toBe('merito');
    expect(component.paginaActual).toBe(1);
  });

  it('debería mostrar Coincide sin detalle cuando está reconciliado', () => {
    fixture.detectChanges();

    const celda: HTMLElement = fixture.nativeElement.querySelector('.reconciliacion');
    expect(celda.textContent.trim()).toBe('Coincide');
    expect(celda.querySelector('small')).toBeNull();
  });

  [2.5, -2.5].forEach(diferencia => {
    it(`debería mostrar la diferencia ${diferencia} con su signo`, () => {
      rankingServiceSpy.obtenerRanking.and.returnValue(of([
        { ...sociosMock[0], reconciliado: false, diferencia }
      ]));
      fixture.detectChanges();

      const celda: HTMLElement = fixture.nativeElement.querySelector('.reconciliacion');
      const signo = diferencia > 0 ? '+' : '';
      expect(celda.textContent).toContain(`Diferencia: ${signo}${diferencia.toFixed(2)} pts`);
      expect(celda.textContent).not.toContain('Coincide');
    });
  });

  it('debería mostrar los saldos histórico y general cuando hay diferencia', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(of([
      { ...sociosMock[0], reconciliado: false, saldoHistorico: 8, saldoPuntajeGeneral: 5, diferencia: 3 }
    ]));
    fixture.detectChanges();

    const detalle: HTMLElement = fixture.nativeElement.querySelector('.reconciliacion small');
    expect(detalle.textContent.trim()).toBe('Histórico: 8.00 | General: 5.00');
  });

  it('debería respetar la diferencia del backend sin recalcular ni alterar saldo u orden', () => {
    // Valores deliberadamente inconsistentes para detectar un recálculo en frontend.
    rankingServiceSpy.obtenerRanking.and.returnValue(of([
      { ...sociosMock[0], saldo: -4, saldoHistorico: 100, saldoPuntajeGeneral: 20,
        diferencia: -0.25, reconciliado: false },
      sociosMock[1]
    ]));
    fixture.detectChanges();

    expect(component.sociosOrdenados.map(s => s.id)).toEqual(['2', '1']);
    const filas: NodeListOf<HTMLTableRowElement> = fixture.nativeElement.querySelectorAll('tbody tr');
    const celda = filas[1].querySelector('.reconciliacion');
    expect(celda.textContent).toContain('Diferencia: -0.25 pts');
    expect(celda.textContent).not.toContain('Diferencia: +80.00 pts');
    expect(filas[1].cells[5].textContent).toContain('-4.00 pts');
    expect(filas[1].cells[5].textContent).toContain('Habilitado Regular');
    expect(component.socios.find(s => s.id === '1').diferencia).toBe(-0.25);
  });
});
