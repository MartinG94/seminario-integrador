import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { of, Subject, throwError } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { CalendarioApiService, HolidayDto, CalcularPlazoResponse } from '../services/calendario-api.service';
import { CalendarioInstitucionalComponent } from './calendario-institucional.component';

describe('CalendarioInstitucionalComponent', () => {
  let component: CalendarioInstitucionalComponent;
  let fixture: ComponentFixture<CalendarioInstitucionalComponent>;
  let api: jasmine.SpyObj<CalendarioApiService>;
  let auth: jasmine.SpyObj<AuthService>;

  const holidays: HolidayDto[] = [
    { id: 1, fecha: '2026-10-12', descripcion: 'Diversidad cultural', creado_por: null,
      creado_por_nombre: 'Sistema (carga inicial)', created_at: '2026-10-08T12:30:45-03:00' },
    { id: 2, fecha: '2026-11-23', descripcion: 'Soberanía Nacional', creado_por: 7,
      creado_por_nombre: 'Ana Pérez (ana)', created_at: '2026-10-08T14:30:12-03:00' }
  ];
  const result: CalcularPlazoResponse = {
    start_at: '2026-10-12T14:30:00-03:00', business_days: 1,
    deadline: '2026-10-13T14:30:00-03:00',
    dias_habiles_computados: [{ day_number: 1, date: '2026-10-13', weekday: 'Martes' }],
    dias_excluidos: []
  };

  beforeEach(async () => {
    api = jasmine.createSpyObj('CalendarioApiService', ['getFeriados', 'addFeriado', 'calcularPlazo']);
    api.getFeriados.and.returnValue(of([...holidays]));
    api.calcularPlazo.and.returnValue(of(result));
    auth = jasmine.createSpyObj('AuthService', ['tieneRol']);
    auth.tieneRol.and.returnValue(true);
    await TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [CalendarioInstitucionalComponent],
      providers: [{ provide: CalendarioApiService, useValue: api }, { provide: AuthService, useValue: auth }],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();
    fixture = TestBed.createComponent(CalendarioInstitucionalComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga feriados directamente y exhibe auditoría con segundos', () => {
    expect(api.getFeriados).toHaveBeenCalledTimes(1);
    const text = (fixture.nativeElement as HTMLElement).textContent;
    expect(text).toContain('Ana Pérez (ana)');
    expect(text).toContain('08/10/2026 14:30:12');
  });

  it('muestra sólo feriados y auditoría sin versiones, tipos ni condición', () => {
    const root: HTMLElement = fixture.nativeElement;
    const headers = Array.from(root.querySelectorAll('th')).map(cell => cell.textContent?.trim());
    expect(headers[0]).toContain('Fecha');
    expect(headers.slice(1)).toEqual(['Denominación', 'Creado por', 'Creado el']);
    expect(root.textContent).not.toContain('Versión');
    expect(root.textContent).not.toContain('Condición');
    expect(root.textContent).not.toContain('Excepción');
    expect(root.textContent).toContain('Crear Feriado');
    expect(root.querySelectorAll('select').length).toBe(2);
  });

  it('conserva las fechas sin hora como días de calendario', () => {
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('.holiday-date')?.textContent).toBe('12/10/2026');
    expect(component.formatCalendarDate('2026-01-01')).toBe('01/01/2026');
    component.simulationResult = result;
    fixture.detectChanges();
    expect(root.querySelector('.simulation-days')?.textContent).toContain('13/10/2026');
  });

  it('ordena Fecha mediante un botón accesible y filtra por Año/Mes', () => {
    const root: HTMLElement = fixture.nativeElement;
    const header = root.querySelector('th');
    expect(header?.getAttribute('aria-sort')).toBe('ascending');
    header?.querySelector('button')?.click();
    fixture.detectChanges();
    expect(header?.getAttribute('aria-sort')).toBe('descending');
    expect(component.filteredHolidays.map(holiday => holiday.fecha)).toEqual(['2026-11-23', '2026-10-12']);
    component.selectedYear = 2026;
    component.selectedMonth = 10;
    component.applyFilters();
    expect(component.filteredHolidays.map(holiday => holiday.fecha)).toEqual(['2026-10-12']);
    component.selectedYear = 2027;
    component.applyFilters();
    expect(component.filteredHolidays).toEqual([]);
  });

  it('muestra calendario vacío sin alertas ni versiones inicializadas', () => {
    api.getFeriados.and.returnValue(of([]));
    component.loadHolidays();
    fixture.detectChanges();
    expect(component.errorMessage).toBe('');
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('.calendar-state[role="status"]')?.textContent).toContain('No hay feriados registrados.');
    expect(root.querySelector('[role="alert"]')).toBeNull();
    expect(root.textContent).toContain('Podés registrar el primer feriado con Crear Feriado.');
  });

  it('recupera la carga con Reintentar dentro del estado de error de la tabla', () => {
    api.getFeriados.and.returnValue(throwError(() => ({ status: 500 })));
    component.loadHolidays();
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    expect(component.loading).toBeFalse();
    const state = root.querySelector('.calendar-state[role="alert"]');
    expect(state?.textContent).toContain('No se pudo cargar el calendario. Intentá nuevamente.');
    expect(root.querySelectorAll('.holiday-date').length).toBe(0);
    const retry = state?.querySelector('button') as HTMLButtonElement;
    expect(retry?.textContent).toContain('Reintentar');
    const pending = new Subject<HolidayDto[]>();
    api.getFeriados.and.returnValue(pending);
    retry.click();
    fixture.detectChanges();
    expect(root.querySelector('[role="alert"]')).toBeNull();
    expect(root.querySelector('.calendar-state[role="status"]')?.textContent).toContain('Cargando calendario');
    pending.next(holidays);
    fixture.detectChanges();
    expect(component.holidays.length).toBe(2);
    expect(root.querySelector('.calendar-state')).toBeNull();
    expect(root.querySelectorAll('.holiday-date').length).toBe(2);
  });

  it('no presenta un error de alta como un fallo de carga ni oculta la tabla', () => {
    api.addFeriado.and.returnValue(throwError(() => ({ error: { fecha: ['Ya existe un feriado para esa fecha.'] } })));
    component.holidayDate = '2099-10-13';
    component.holidayDescription = 'Asueto';
    component.saveHoliday();
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('.calendar-notice[role="alert"]')?.textContent).toContain('Ya existe');
    expect(root.querySelector('.calendar-state[role="alert"]')).toBeNull();
    expect(root.querySelectorAll('.holiday-date').length).toBe(2);
  });

  it('requiere recuperar la carga antes de permitir un alta sobre un calendario incompleto', () => {
    api.getFeriados.and.returnValue(throwError(() => ({ status: 500 })));
    component.loadHolidays();
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    const create = root.querySelector('[aria-controls="create-holiday-form"]') as HTMLButtonElement;
    expect(create.disabled).toBeTrue();
    component.toggleHolidayForm();
    expect(component.showHolidayForm).toBeFalse();
    component.holidayDate = '2099-10-13';
    component.holidayDescription = 'Asueto';
    component.saveHoliday();
    expect(api.addFeriado).not.toHaveBeenCalled();
    api.getFeriados.and.returnValue(of(holidays));
    (root.querySelector('.calendar-state button') as HTMLButtonElement).click();
    fixture.detectChanges();
    expect(create.disabled).toBeFalse();
    create.click();
    fixture.detectChanges();
    expect(root.querySelector('#create-holiday-form')).not.toBeNull();
    expect(root.querySelectorAll('.holiday-date').length).toBe(2);
  });

  it('no ofrece crear el primer feriado a un usuario sin permiso de alta', () => {
    auth.tieneRol.and.returnValue(false);
    api.getFeriados.and.returnValue(of([]));
    component.loadHolidays();
    fixture.detectChanges();
    const root: HTMLElement = fixture.nativeElement;
    expect(root.querySelector('.calendar-state')?.textContent).toContain('No hay feriados registrados.');
    expect(root.textContent).not.toContain('Podés registrar el primer feriado');
  });

  it('bloquea fechas pasadas y muestra el mínimo institucional en el input', () => {
    jasmine.clock().install();
    try {
      jasmine.clock().mockDate(new Date('2026-10-11T00:30:00Z'));
      expect(component.today).toBe('2026-10-10');
      component.toggleHolidayForm();
      fixture.detectChanges();
      const dateInput = (fixture.nativeElement as HTMLElement).querySelector('#holiday-date');
      expect(dateInput?.getAttribute('min')).toBe('2026-10-10');
      component.holidayDate = '2026-10-09';
      component.holidayDescription = 'Asueto';
      component.saveHoliday();
      expect(api.addFeriado).not.toHaveBeenCalled();
      expect(component.errorMessage).toContain('hoy o posterior');
    } finally { jasmine.clock().uninstall(); }
  });

  it('guarda sólo fecha/denominación una vez y agrega la auditoría devuelta', () => {
    const pending = new Subject<HolidayDto>();
    api.addFeriado.and.returnValue(pending);
    component.holidayDate = '2099-10-13';
    component.holidayDescription = ' Asueto nuevo ';
    component.saveHoliday();
    component.saveHoliday();
    expect(api.addFeriado).toHaveBeenCalledOnceWith({ fecha: '2099-10-13', descripcion: 'Asueto nuevo' });
    expect(component.savingHoliday).toBeTrue();
    pending.next({ ...holidays[1], id: 3, fecha: '2099-10-13', descripcion: 'Asueto nuevo' });
    expect(component.filteredHolidays.length).toBe(3);
    expect(component.savingHoliday).toBeFalse();
    expect(component.successMessage).toBe('Feriado creado.');
  });

  it('muestra el error del servidor al intentar crear un duplicado', () => {
    api.addFeriado.and.returnValue(throwError(() => ({ error: { fecha: ['Ya existe un feriado para esa fecha.'] } })));
    component.holidayDate = '2099-10-13';
    component.holidayDescription = 'Asueto';
    component.saveHoliday();
    expect(component.errorMessage).toContain('Ya existe');
    expect(component.savingHoliday).toBeFalse();
  });

  it('oculta la creación a socios y bloquea un envío directo sin rol', () => {
    auth.tieneRol.and.returnValue(false);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('Crear Feriado');
    component.holidayDate = '2099-10-13';
    component.holidayDescription = 'Asueto';
    component.saveHoliday();
    expect(api.addFeriado).not.toHaveBeenCalled();
  });

  it('envía la hora de Buenos Aires sin depender de la zona del navegador', () => {
    component.simulationStart = '2026-10-12T14:30';
    component.simulationDays = 1;
    component.calculateDeadline();
    expect(api.calcularPlazo).toHaveBeenCalledOnceWith({ start_at: '2026-10-12T14:30-03:00', business_days: 1 });
    expect(component.simulationResult).toEqual(result);
  });

  it('recalcula con el calendario vigente cuando se crea un feriado durante una simulación pendiente', () => {
    const previousCalculation = new Subject<CalcularPlazoResponse>();
    const currentCalculation = new Subject<CalcularPlazoResponse>();
    api.calcularPlazo.and.returnValues(previousCalculation, currentCalculation);
    component.simulationStart = '2099-10-12T14:30';
    component.simulationDays = 1;
    component.calculateDeadline();
    api.addFeriado.and.returnValue(of({ ...holidays[1], id: 3, fecha: '2099-10-13' }));
    component.holidayDate = '2099-10-13';
    component.holidayDescription = 'Asueto';
    component.saveHoliday();
    expect(api.calcularPlazo).toHaveBeenCalledTimes(2);
    previousCalculation.next(result);
    expect(component.simulationResult).toBeNull();
    expect(component.simulationLoading).toBeTrue();
    const updatedResult = { ...result, deadline: '2099-10-14T14:30:00-03:00' };
    currentCalculation.next(updatedResult);
    expect(component.simulationResult).toEqual(updatedResult);
    expect(component.simulationLoading).toBeFalse();
  });

  it('rechaza días fraccionarios y fecha inválida antes de calcular', () => {
    component.simulationStart = '2026-10-12T14:30';
    component.simulationDays = 1.5;
    component.calculateDeadline();
    expect(api.calcularPlazo).not.toHaveBeenCalled();
    component.simulationDays = 1;
    component.simulationStart = 'invalid';
    component.calculateDeadline();
    expect(api.calcularPlazo).not.toHaveBeenCalled();
  });

  it('cancela solicitudes pendientes al destruir la pantalla', () => {
    const pending = new Subject<HolidayDto[]>();
    api.getFeriados.and.returnValue(pending);
    component.loadHolidays();
    component.ngOnDestroy();
    pending.next([]);
    expect(component.holidays.length).toBe(2);
  });
});
