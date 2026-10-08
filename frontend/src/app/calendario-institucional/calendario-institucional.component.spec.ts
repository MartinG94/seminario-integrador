import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { CalendarioApiService, CalendarioVersionDto } from '../services/calendario-api.service';
import { CalendarioInstitucionalComponent } from './calendario-institucional.component';

describe('CalendarioInstitucionalComponent', () => {
  let component: CalendarioInstitucionalComponent;
  let fixture: ComponentFixture<CalendarioInstitucionalComponent>;
  let mockCalendarioApi: jasmine.SpyObj<CalendarioApiService>;
  let mockAuth: jasmine.SpyObj<AuthService>;

  const mockVersiones: CalendarioVersionDto[] = [
    {
      id: 1,
      version: 1,
      nombre: 'Calendario Oficial AVEIT 2026',
      vigencia_desde: '2026-01-01',
      vigencia_hasta: null,
      activa: true,
      motivo_cambio: 'Carga inicial oficial 2026',
      feriados_count: 1,
      created_at: '2026-01-01T00:00:00Z',
      feriados: [
        {
          id: 1,
          fecha: '2026-10-12',
          descripcion: 'Día del Respeto a la Diversidad Cultural',
          tipo: 'NACIONAL',
          tipo_display: 'Feriado Nacional',
          es_laborable: false
        }
      ]
    }
  ];

  beforeEach(async () => {
    mockCalendarioApi = jasmine.createSpyObj('CalendarioApiService', [
      'getVersiones',
      'getVersionDetail',
      'createVersion',
      'getFeriados',
      'addFeriado',
      'calcularPlazo'
    ]);

    mockCalendarioApi.getVersiones.and.returnValue(of(mockVersiones));
    mockCalendarioApi.getVersionDetail.and.returnValue(of(mockVersiones[0]));

    mockAuth = jasmine.createSpyObj('AuthService', ['tieneRol']);
    mockAuth.tieneRol.and.returnValue(true);

    await TestBed.configureTestingModule({
      imports: [FormsModule, MatDialogModule],
      declarations: [CalendarioInstitucionalComponent],
      providers: [
        { provide: CalendarioApiService, useValue: mockCalendarioApi },
        { provide: AuthService, useValue: mockAuth }
      ],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(CalendarioInstitucionalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('se crea correctamente e inicializa las versiones', () => {
    expect(component).toBeTruthy();
    expect(mockCalendarioApi.getVersiones).toHaveBeenCalled();
    expect(component.versiones.length).toBe(1);
    expect(component.versionActiva?.version).toBe(1);
  });

  it('aplica filtros de feriados por tipo y búsqueda', () => {
    component.busqueda = 'Diversidad';
    component.aplicarFiltros();
    expect(component.feriadosFiltrados.length).toBe(1);

    component.busqueda = 'Inexistente';
    component.aplicarFiltros();
    expect(component.feriadosFiltrados.length).toBe(0);

    component.busqueda = '';
    component.filtroTipo = 'PROVINCIAL';
    component.aplicarFiltros();
    expect(component.feriadosFiltrados.length).toBe(0);
  });

  it('ejecuta la simulación de cálculo de plazos', () => {
    mockCalendarioApi.calcularPlazo.and.returnValue(of({
      start_at: '2026-10-08T10:00:00Z',
      business_days: 5,
      deadline: '2026-10-16T10:00:00Z',
      calendario_version: { id: 1, version: 1, nombre: 'Oficial' },
      dias_habiles_computados: [{ day_number: 1, date: '2026-10-09', weekday: 'Viernes' }],
      dias_excluidos: [{ date: '2026-10-10', reason: 'Sábado' }]
    }));

    component.simuladorFechaInicio = '2026-10-08T10:00';
    component.simuladorDiasHabiles = 5;
    component.calcularPlazoSimulado();

    expect(mockCalendarioApi.calcularPlazo).toHaveBeenCalled();
    expect(component.simuladorResultado?.deadline).toBe('2026-10-16T10:00:00Z');
  });

  it('verifica permisos de gestión de calendario', () => {
    mockAuth.tieneRol.and.returnValue(true);
    expect(component.puedeGestionar).toBeTrue();

    mockAuth.tieneRol.and.returnValue(false);
    expect(component.puedeGestionar).toBeFalse();
  });
});
