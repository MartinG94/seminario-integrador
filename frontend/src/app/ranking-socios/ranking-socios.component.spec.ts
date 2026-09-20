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
});
