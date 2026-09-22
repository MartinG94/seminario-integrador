import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { RankingSociosComponent } from './ranking-socios.component';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';

describe('RankingSociosComponent', () => {
  let component: RankingSociosComponent;
  let fixture: ComponentFixture<RankingSociosComponent>;
  let mockDataService: jasmine.SpyObj<TribunalDataService>;
  let mockDialog: jasmine.SpyObj<MatDialog>;

  const mockSocios: Socio[] = [
    {
      id: '1',
      nombre: 'Esteban Domínguez',
      legajo: 'LEG-4123',
      email: 'edominguez@aveit.frc.utn.edu.ar',
      subcomision: 'Relaciones Públicas',
      saldo: -10.5,
      estado: 'CESE_ESTATUTARIO',
      felicitaciones: 0,
      sanciones: 6
    },
    {
      id: '2',
      nombre: 'Lucas Benítez',
      legajo: 'LEG-9120',
      email: 'lbenitez@aveit.frc.utn.edu.ar',
      subcomision: 'Extensión',
      saldo: 6.5,
      estado: 'HABILITADO',
      felicitaciones: 4,
      sanciones: 0
    }
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('TribunalDataService', ['setRole'], {
      socios$: of(mockSocios)
    });
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);

    await TestBed.configureTestingModule({
      declarations: [RankingSociosComponent],
      providers: [
        { provide: TribunalDataService, useValue: mockDataService },
        { provide: MatDialog, useValue: mockDialog }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RankingSociosComponent);
    component = fixture.componentInstance;
    component.ngOnInit();
  });

  afterEach(() => {
    component.ngOnDestroy();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
    expect(component.socios.length).toBe(2);
  });

  it('debe filtrar por subcomision sin importar tildes (publicas -> Relaciones Públicas)', () => {
    component.filtroTexto = 'publicas';
    const resultados = component.sociosOrdenados;
    expect(resultados.length).toBe(1);
    expect(resultados[0].nombre).toBe('Esteban Domínguez');
    expect(resultados[0].subcomision).toBe('Relaciones Públicas');
  });

  it('debe filtrar por subcomision cuando se busca con tildes (públicas -> Relaciones Públicas)', () => {
    component.filtroTexto = 'públicas';
    const resultados = component.sociosOrdenados;
    expect(resultados.length).toBe(1);
    expect(resultados[0].subcomision).toBe('Relaciones Públicas');
  });

  it('debe filtrar por nombre sin importar tildes (dominguez -> Esteban Domínguez)', () => {
    component.filtroTexto = 'dominguez';
    const resultados = component.sociosOrdenados;
    expect(resultados.length).toBe(1);
    expect(resultados[0].nombre).toBe('Esteban Domínguez');
  });

  it('debe filtrar por nombre cuando se busca con tilde (Benítez -> Lucas Benítez)', () => {
    component.filtroTexto = 'Benítez';
    const resultados = component.sociosOrdenados;
    expect(resultados.length).toBe(1);
    expect(resultados[0].nombre).toBe('Lucas Benítez');
  });
});
