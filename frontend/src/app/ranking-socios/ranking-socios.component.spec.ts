import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { RankingSociosComponent } from './ranking-socios.component';
import { SocioApiService, PaginatedResponse, SocioListItemDTO } from '../services/socio-api.service';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog/socio-legajo-dialog.component';

describe('RankingSociosComponent', () => {
  let component: RankingSociosComponent;
  let fixture: ComponentFixture<RankingSociosComponent>;
  let mockDataService: jasmine.SpyObj<TribunalDataService>;
  let mockSocioApiService: jasmine.SpyObj<SocioApiService>;
  let mockDialog: jasmine.SpyObj<MatDialog>;

  const mockSociosPadron: PaginatedResponse<SocioListItemDTO> = {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        id: 1,
        legajo: '74907',
        first_name: 'Lucas',
        last_name: 'Gastiaburu',
        email: '74907@aveit.test',
        role: 'SOCIO',
        category: 'ACTIVE',
        category_display: 'Activo',
        subcomision: 'Cómputos'
      },
      {
        id: 2,
        legajo: '85194',
        first_name: 'Lucas Martín',
        last_name: 'Guillén',
        email: '85194@aveit.test',
        role: 'FISCALIZADORA',
        category: 'ACTIVE',
        category_display: 'Activo',
        subcomision: 'Cómputos'
      }
    ]
  };

  const mockSociosTribunal: Socio[] = [
    {
      id: '1',
      nombre: 'Lucas Gastiaburu',
      legajo: '74907',
      email: '74907@aveit.test',
      subcomision: 'Cómputos',
      saldo: 4.5,
      estado: 'HABILITADO',
      felicitaciones: 3,
      sanciones: 0
    },
    {
      id: '2',
      nombre: 'Lucas Martín Guillén',
      legajo: '85194',
      email: '85194@aveit.test',
      subcomision: 'Cómputos',
      saldo: 2.0,
      estado: 'HABILITADO',
      felicitaciones: 2,
      sanciones: 1
    }
  ];

  beforeEach(async () => {
    mockDataService = jasmine.createSpyObj('TribunalDataService', ['setRole'], {
      socios$: of(mockSociosTribunal)
    });
    mockSocioApiService = jasmine.createSpyObj('SocioApiService', ['searchSocios']);
    mockDialog = jasmine.createSpyObj('MatDialog', ['open']);

    mockSocioApiService.searchSocios.and.returnValue(of(mockSociosPadron));

    await TestBed.configureTestingModule({
      declarations: [RankingSociosComponent],
      providers: [
        { provide: TribunalDataService, useValue: mockDataService },
        { provide: SocioApiService, useValue: mockSocioApiService },
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

  it('debe crearse correctamente y consultar searchSocios al inicializar', () => {
    expect(component).toBeTruthy();
    expect(mockSocioApiService.searchSocios).toHaveBeenCalledWith('');
    expect(component.socios.length).toBe(2);
    expect(component.socios[0].nombre).toBe('Lucas Gastiaburu');
    expect(component.socios[0].legajo).toBe('74907');
    expect(component.socios[0].subcomision).toBe('Cómputos');
  });

  it('debe consultar SocioApiService.searchSocios al ejecutar buscar(query)', () => {
    const singleResult: PaginatedResponse<SocioListItemDTO> = {
      count: 1,
      next: null,
      previous: null,
      results: [mockSociosPadron.results[0]]
    };
    mockSocioApiService.searchSocios.and.returnValue(of(singleResult));

    component.buscar('gastiaburu');

    expect(mockSocioApiService.searchSocios).toHaveBeenCalledWith('gastiaburu');
    expect(component.socios.length).toBe(1);
    expect(component.socios[0].nombre).toBe('Lucas Gastiaburu');
  });

  it('onFiltroChange debe actualizar filtroTexto', () => {
    component.onFiltroChange('computos');
    expect(component.filtroTexto).toBe('computos');
  });

  it('abrirLegajoSocio debe abrir el diálogo con socioId, nombre y saldo correspondiente', () => {
    const socio = component.socios[0];
    component.abrirLegajoSocio(socio);

    expect(mockDialog.open).toHaveBeenCalledWith(SocioLegajoDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: {
        socioId: '1',
        nombreSocio: 'Lucas Gastiaburu',
        saldo: 4.5
      }
    });
  });

  it('debe ordenar por mérito o sanción según criterioOrden', () => {
    component.setOrden('merito');
    const porMerito = component.sociosOrdenados;
    expect(porMerito[0].saldo).toBeGreaterThanOrEqual(porMerito[1].saldo);

    component.setOrden('sancion');
    const porSancion = component.sociosOrdenados;
    expect(porSancion[0].saldo).toBeLessThanOrEqual(porSancion[1].saldo);
  });

  it('onRowKeyDown debe abrir el legajo al presionar Enter', () => {
    const socio = component.socios[0];
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    spyOn(event, 'preventDefault');

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(mockDialog.open).toHaveBeenCalledWith(SocioLegajoDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: {
        socioId: '1',
        nombreSocio: 'Lucas Gastiaburu',
        saldo: 4.5
      }
    });
  });

  it('onRowKeyDown debe abrir el legajo al presionar Space', () => {
    const socio = component.socios[0];
    const event = new KeyboardEvent('keydown', { key: ' ' });
    spyOn(event, 'preventDefault');

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(mockDialog.open).toHaveBeenCalledWith(SocioLegajoDialogComponent, {
      width: '100%',
      maxWidth: '600px',
      data: {
        socioId: '1',
        nombreSocio: 'Lucas Gastiaburu',
        saldo: 4.5
      }
    });
  });

  it('onRowKeyDown con ArrowDown debe prevenir scroll y dar foco a la siguiente fila', () => {
    const socio = component.socios[0];
    const nextTr = document.createElement('tr');
    spyOn(nextTr, 'focus');

    const currentTr = document.createElement('tr');
    const tbody = document.createElement('tbody');
    tbody.appendChild(currentTr);
    tbody.appendChild(nextTr);

    const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    spyOn(event, 'preventDefault');
    Object.defineProperty(event, 'target', { value: currentTr });

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(nextTr.focus).toHaveBeenCalled();
  });

  it('onRowKeyDown con ArrowUp debe prevenir scroll y dar foco a la fila anterior', () => {
    const socio = component.socios[1];
    const prevTr = document.createElement('tr');
    spyOn(prevTr, 'focus');

    const currentTr = document.createElement('tr');
    const tbody = document.createElement('tbody');
    tbody.appendChild(prevTr);
    tbody.appendChild(currentTr);

    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    spyOn(event, 'preventDefault');
    Object.defineProperty(event, 'target', { value: currentTr });

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(prevTr.focus).toHaveBeenCalled();
  });
});
