import { Component, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { NavigationStart, Router } from '@angular/router';
import { merge, Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

import { CalendarioApiService, CalcularPlazoResponse, HolidayDto } from '../services/calendario-api.service';
import { AuthService } from '../services/auth.service';
import { NotificationService, httpErrorMessage } from '../services/notification.service';

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
  showHolidayForm = false;
  holidayDate = '';
  holidayDescription = '';
  savingHoliday = false;

  simulationStart = '';
  simulationDays = 5;
  simulationLoading = false;
  simulationResult: CalcularPlazoResponse | null = null;
  @ViewChild('simulationTemplate', { static: true }) simulationTemplate: TemplateRef<unknown>;
  private simulationDialog: MatDialogRef<unknown> | null = null;

  readonly months = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  private readonly destroy$ = new Subject<void>();
  private readonly cancelSimulation$ = new Subject<void>();

  constructor(private calendarApi: CalendarioApiService, public auth: AuthService,
    private notifications: NotificationService, private dialog: MatDialog, private router: Router) {}

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
    this.router.events.pipe(takeUntil(this.destroy$)).subscribe(event => {
      if (event instanceof NavigationStart) { this.closeSimulation(); }
    });
  }

  ngOnDestroy(): void {
    this.closeSimulation();
    this.destroy$.next();
    this.destroy$.complete();
    this.cancelSimulation$.complete();
  }

  openSimulation(): void {
    if (this.simulationDialog) { return; }
    this.resetSimulation();
    this.simulationDialog = this.dialog.open(this.simulationTemplate, {
      width: '56rem',
      maxWidth: 'calc(100vw - 2rem)',
      maxHeight: 'calc(100vh - 2rem)',
      autoFocus: '#simulation-start',
      ariaLabelledBy: 'simulation-title',
      panelClass: 'calendar-simulation-dialog',
      closeOnNavigation: true,
      restoreFocus: true
    });
    // Cancelar al comenzar el cierre evita respuestas durante la animación de salida.
    this.simulationDialog.beforeClosed().pipe(takeUntil(this.destroy$)).subscribe(() => this.resetSimulation());
    merge(
      this.simulationDialog.backdropClick(),
      this.simulationDialog.keydownEvents().pipe(filter(event =>
        event.key === 'Escape' && !event.altKey && !event.ctrlKey && !event.metaKey && !event.shiftKey))
    ).pipe(takeUntil(this.simulationDialog.afterClosed()), takeUntil(this.destroy$))
      .subscribe(() => this.resetSimulation());
    this.simulationDialog.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(() => {
      this.simulationDialog = null;
    });
  }

  closeSimulation(): void {
    this.resetSimulation();
    this.simulationDialog?.close();
  }

  private resetSimulation(): void {
    this.cancelSimulation$.next();
    this.simulationLoading = false;
    this.simulationResult = null;
    this.simulationDays = 5;
    this.simulationStart = this.institutionalDateTime();
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
        this.notifications.error(this.loadError);
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
      this.notifications.error('Completá la fecha y la denominación.');
      return;
    }
    if (this.holidayDate < this.today) {
      this.notifications.error('La fecha debe ser hoy o posterior.');
      return;
    }
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
        this.notifications.success('Feriado creado.');
        if (this.simulationResult || this.simulationLoading) {
          this.cancelSimulation$.next();
          this.simulationLoading = false;
          this.calculateDeadline();
        }
      },
      error: (error: unknown) => {
        this.savingHoliday = false;
        this.notifications.error(httpErrorMessage(error, 'No se pudo crear el feriado. Intentá nuevamente.'));
      }
    });
  }

  calculateDeadline(): void {
    if (this.simulationLoading) { return; }
    this.simulationResult = null;
    if (!this.simulationStart || Number.isNaN(Date.parse(`${this.simulationStart}-03:00`))) {
      this.notifications.error('Indicá una fecha y hora de inicio válidas.');
      return;
    }
    if (!Number.isInteger(this.simulationDays) || this.simulationDays < 1) {
      this.notifications.error('La cantidad de días hábiles debe ser un entero mayor a cero.');
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
        this.notifications.error('No se pudo calcular el vencimiento. Intentá nuevamente.');
      }
    });
  }
}
