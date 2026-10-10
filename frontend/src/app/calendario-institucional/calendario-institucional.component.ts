import { Component, OnDestroy, OnInit } from '@angular/core';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { CalendarioApiService, CalcularPlazoResponse, HolidayDto } from '../services/calendario-api.service';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-calendario-institucional',
  templateUrl: './calendario-institucional.component.html',
  styleUrls: ['./calendario-institucional.component.scss']
})
export class CalendarioInstitucionalComponent implements OnInit, OnDestroy {
  holidays: HolidayDto[] = [];
  filteredHolidays: HolidayDto[] = [];
  selectedYear: number | null = null;
  selectedMonth: number | null = null;
  dateAscending = true;
  loading = false;
  loadError = '';
  errorMessage = '';
  successMessage = '';
  showHolidayForm = false;
  holidayDate = '';
  holidayDescription = '';
  savingHoliday = false;

  simulationStart = '';
  simulationDays = 5;
  simulationLoading = false;
  simulationResult: CalcularPlazoResponse | null = null;
  simulationError = '';

  readonly months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  private readonly destroy$ = new Subject<void>();
  private readonly cancelSimulation$ = new Subject<void>();

  constructor(private calendarApi: CalendarioApiService, public auth: AuthService) {}

  get canManage(): boolean { return this.auth.tieneRol('ADMIN', 'CD', 'TD'); }

  get today(): string {
    return this.institutionalDateTime().slice(0, 10);
  }

  get years(): number[] {
    return Array.from(new Set([
      Number(this.today.slice(0, 4)),
      ...this.holidays.map(holiday => Number(holiday.fecha.slice(0, 4)))
    ])).sort((a, b) => b - a);
  }

  get canSaveHoliday(): boolean {
    return !!this.holidayDate && this.holidayDate >= this.today &&
      !!this.holidayDescription.trim() && !this.savingHoliday && !this.loading && !this.loadError;
  }

  ngOnInit(): void {
    this.simulationStart = this.institutionalDateTime();
    this.loadHolidays();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.cancelSimulation$.complete();
  }

  private institutionalDateTime(): string {
    const parts = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/Argentina/Buenos_Aires',
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', hourCycle: 'h23'
    }).formatToParts(new Date());
    const value = (key: string): string => parts.find(part => part.type === key)?.value || '';
    return `${value('year')}-${value('month')}-${value('day')}T${value('hour')}:${value('minute')}`;
  }

  loadHolidays(): void {
    this.loading = true;
    this.loadError = '';
    this.calendarApi.getFeriados().pipe(takeUntil(this.destroy$)).subscribe({
      next: holidays => {
        this.holidays = holidays;
        this.applyFilters();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.loadError = 'No se pudo cargar el calendario. Intentá nuevamente.';
      }
    });
  }

  applyFilters(): void {
    this.filteredHolidays = this.holidays.filter(holiday =>
      (this.selectedYear == null || Number(holiday.fecha.slice(0, 4)) === this.selectedYear) &&
      (this.selectedMonth == null || Number(holiday.fecha.slice(5, 7)) === this.selectedMonth)
    ).sort((a, b) => this.dateAscending ? a.fecha.localeCompare(b.fecha) : b.fecha.localeCompare(a.fecha));
  }

  toggleDateOrder(): void {
    this.dateAscending = !this.dateAscending;
    this.applyFilters();
  }

  formatCalendarDate(value: string): string {
    const [year, month, day] = value.split('-');
    return `${day}/${month}/${year}`;
  }

  toggleHolidayForm(): void {
    if (this.savingHoliday || this.loading || this.loadError) { return; }
    this.showHolidayForm = !this.showHolidayForm;
    this.holidayDate = '';
    this.holidayDescription = '';
  }

  saveHoliday(): void {
    if (!this.canManage || this.savingHoliday || this.loading || this.loadError) { return; }
    if (!this.holidayDate || !this.holidayDescription.trim()) {
      this.errorMessage = 'Completá la fecha y la denominación.';
      return;
    }
    if (this.holidayDate < this.today) {
      this.errorMessage = 'La fecha debe ser hoy o posterior.';
      return;
    }
    this.errorMessage = '';
    this.successMessage = '';
    this.savingHoliday = true;
    this.calendarApi.addFeriado({
      fecha: this.holidayDate,
      descripcion: this.holidayDescription.trim()
    }).pipe(takeUntil(this.destroy$)).subscribe({
      next: holiday => {
        this.holidays = [...this.holidays, holiday];
        this.selectedYear = null;
        this.selectedMonth = null;
        this.applyFilters();
        this.savingHoliday = false;
        this.showHolidayForm = false;
        this.holidayDate = '';
        this.holidayDescription = '';
        this.successMessage = 'Feriado creado.';
        if (this.simulationResult || this.simulationLoading) {
          this.cancelSimulation$.next();
          this.simulationLoading = false;
          this.calculateDeadline();
        }
      },
      error: (error: { error?: { fecha?: string[]; descripcion?: string[]; detail?: string } }) => {
        this.savingHoliday = false;
        this.errorMessage = error.error?.fecha?.[0] || error.error?.descripcion?.[0] ||
          error.error?.detail || 'No se pudo crear el feriado. Intentá nuevamente.';
      }
    });
  }

  calculateDeadline(): void {
    if (this.simulationLoading) { return; }
    this.simulationError = '';
    this.simulationResult = null;
    if (!this.simulationStart || Number.isNaN(Date.parse(`${this.simulationStart}-03:00`))) {
      this.simulationError = 'Indicá una fecha y hora de inicio válidas.';
      return;
    }
    if (!Number.isInteger(this.simulationDays) || this.simulationDays < 1) {
      this.simulationError = 'La cantidad de días hábiles debe ser un entero mayor a cero.';
      return;
    }
    this.simulationLoading = true;
    this.calendarApi.calcularPlazo({
      start_at: `${this.simulationStart}-03:00`,
      business_days: this.simulationDays
    }).pipe(takeUntil(this.destroy$), takeUntil(this.cancelSimulation$)).subscribe({
      next: result => {
        this.simulationLoading = false;
        this.simulationResult = result;
      },
      error: () => {
        this.simulationLoading = false;
        this.simulationError = 'No se pudo calcular el vencimiento. Intentá nuevamente.';
      }
    });
  }
}
