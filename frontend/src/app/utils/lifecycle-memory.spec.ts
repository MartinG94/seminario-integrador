import { NO_ERRORS_SCHEMA } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatPaginatorIntl, MatPaginatorModule } from '@angular/material/paginator';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { of } from 'rxjs';

import { RankingSociosComponent } from '../ranking-socios/ranking-socios.component';
import { ExpedientesSocioDialogComponent } from '../ranking-socios/expedientes-socio-dialog/expedientes-socio-dialog.component';
import { MisExpedientesComponent } from '../mis-expedientes/mis-expedientes.component';
import { GestionarExpedientesComponent } from '../gestionar-expedientes/gestionar-expedientes.component';
import { VisorExpedienteComponent } from '../gestionar-expedientes/visor-expediente/visor-expediente.component';
import { AsistenciaEventoComponent } from '../pages/eventos/asistencia-evento/asistencia-evento.component';
import { SolicitarPuntosComponent } from '../solicitar-puntos/solicitar-puntos.component';
import { ReportesComponent } from '../reportes/reportes.component';
import { CalendarioInstitucionalComponent } from '../calendario-institucional/calendario-institucional.component';
import { ReglamentosComponent } from '../reglamentos/reglamentos.component';
import { NavbarComponent } from '../components/navbar/navbar.component';
import { SidebarComponent } from '../components/sidebar/sidebar.component';
import { AdminLayoutComponent } from '../layouts/admin-layout/admin-layout.component';

import { RankingService } from '../services/ranking.service';
import { TribunalDataService } from '../services/tribunal-data.service';
import { NotificationService } from '../services/notification.service';
import { ModalScrollLockService } from '../services/modal-scroll-lock.service';
import { AuthService } from '../services/auth.service';
import { SpanishPaginatorIntl } from '../shared/spanish-paginator-intl';
import { environment } from '../../environments/environment';

describe('Auditoría de Memoria y Ciclo de Vida Integral (T-87.19)', () => {
  let notifSpy: jasmine.SpyObj<NotificationService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;

  beforeEach(() => {
    notifSpy = jasmine.createSpyObj('NotificationService', ['success', 'error', 'info', 'warning']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
  });

  it('debe ejecutar 10 ciclos de RankingSociosComponent con MatPaginator liberando destroy$', async () => {
    const rankingSpy = jasmine.createSpyObj('RankingService', ['obtenerRanking']);
    rankingSpy.obtenerRanking.and.returnValue(
      of({
        count: 0,
        total_pages: 1,
        current_page: 1,
        page_size: 10,
        next: null,
        previous: null,
        results: [],
      })
    );

    await TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [FormsModule, MatPaginatorModule, NoopAnimationsModule],
      declarations: [RankingSociosComponent],
      providers: [
        { provide: MatPaginatorIntl, useClass: SpanishPaginatorIntl },
        { provide: RankingService, useValue: rankingSpy },
        { provide: NotificationService, useValue: notifSpy },
        { provide: MatDialog, useValue: dialogSpy },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    for (let i = 0; i < 10; i++) {
      const fixture = TestBed.createComponent(RankingSociosComponent);
      fixture.detectChanges();
      const component = fixture.componentInstance;
      expect(component['destroy$'].isStopped).toBeFalse();
      fixture.destroy();
      expect(component['destroy$'].isStopped).toBeTrue();
    }
  });

  it('debe ejecutar 10 ciclos de MisExpedientesComponent liberando tickers, scrollLock y HTTP pendientes', async () => {
    await TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule, MatPaginatorModule, NoopAnimationsModule],
      declarations: [MisExpedientesComponent],
      providers: [
        TribunalDataService,
        { provide: MatPaginatorIntl, useClass: SpanishPaginatorIntl },
        { provide: NotificationService, useValue: notifSpy },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    const http = TestBed.inject(HttpTestingController);
    const scrollLock = TestBed.inject(ModalScrollLockService);
    const resetSpy = spyOn(scrollLock, 'reset').and.callThrough();

    for (let i = 0; i < 10; i++) {
      const fixture = TestBed.createComponent(MisExpedientesComponent);
      fixture.detectChanges();
      const component = fixture.componentInstance;
      const pending = http.match((r) => r.url === `${environment.apiUrl}/expedientes/mis-expedientes/`);
      expect(pending.length).toBeGreaterThan(0);

      fixture.destroy();

      expect(component['destroy$'].isStopped).toBeTrue();
      expect(component['activeTimers'].size).toBe(0);
      expect(pending.every((req) => req.cancelled)).toBeTrue();
    }

    expect(resetSpy).toHaveBeenCalledTimes(10);
    http.verify();
  });

  it('debe cancelar suscripciones y timers en GestionarExpedientesComponent al desmontar', async () => {
    await TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        FormsModule,
        RouterTestingModule,
        MatPaginatorModule,
        NoopAnimationsModule,
      ],
      declarations: [GestionarExpedientesComponent],
      providers: [
        TribunalDataService,
        AuthService,
        { provide: MatPaginatorIntl, useClass: SpanishPaginatorIntl },
        { provide: NotificationService, useValue: notifSpy },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    const http = TestBed.inject(HttpTestingController);
    const fixture = TestBed.createComponent(GestionarExpedientesComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    const tableroReqs = http.match((r) => r.url.includes('/expedientes/'));
    expect(tableroReqs.length).toBeGreaterThan(0);
    component['scheduleTimer'](() => {}, 60000);
    expect(component['activeTimers'].size).toBe(1);

    fixture.destroy();

    expect(component['destroy$'].isStopped).toBeTrue();
    expect(component['activeTimers'].size).toBe(0);
    expect(tableroReqs.every((req) => req.cancelled)).toBeTrue();
    http.verify();
  });

  it('debe limpiar destroy$, HTTP y timers en AsistenciaEventoComponent y SolicitarPuntosComponent', async () => {
    await TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [
        HttpClientTestingModule,
        FormsModule,
        ReactiveFormsModule,
        RouterTestingModule,
        MatAutocompleteModule,
        MatPaginatorModule,
        NoopAnimationsModule,
      ],
      declarations: [AsistenciaEventoComponent, SolicitarPuntosComponent],
      providers: [
        TribunalDataService,
        { provide: MatPaginatorIntl, useClass: SpanishPaginatorIntl },
        { provide: NotificationService, useValue: notifSpy },
        { provide: MatDialog, useValue: dialogSpy },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    const http = TestBed.inject(HttpTestingController);

    const fEvento = TestBed.createComponent(AsistenciaEventoComponent);
    fEvento.detectChanges();
    const cEvento = fEvento.componentInstance;
    cEvento['scheduleTimer'](() => {}, 60000);
    expect(cEvento['activeTimers'].size).toBe(1);
    const reqsEvento = http.match((r) => r.url.includes('/expedientes/eventos/'));
    expect(reqsEvento.length).toBeGreaterThanOrEqual(2);
    fEvento.destroy();
    expect(cEvento['destroy$'].isStopped).toBeTrue();
    expect(cEvento['activeTimers'].size).toBe(0);
    expect(reqsEvento.every((r) => r.cancelled)).toBeTrue();

    const fSol = TestBed.createComponent(SolicitarPuntosComponent);
    fSol.detectChanges();
    const cSol = fSol.componentInstance;
    cSol['scheduleTimer'](() => {}, 60000);
    expect(cSol['activeTimers'].size).toBe(1);
    const reqsSol = http.match(() => true);
    fSol.destroy();
    expect(cSol['destroy$'].isStopped).toBeTrue();
    expect(cSol['activeTimers'].size).toBe(0);
    expect(reqsSol.every((r) => r.cancelled)).toBeTrue();

    http.verify();
  });

  it('debe cancelar destroy$ y timers en Reportes, Calendario, Visor, Reglamentos, Dialog y Shell', async () => {
    await TestBed.resetTestingModule();
    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule, RouterTestingModule, NoopAnimationsModule],
      declarations: [
        ReportesComponent,
        CalendarioInstitucionalComponent,
        VisorExpedienteComponent,
        ReglamentosComponent,
        ExpedientesSocioDialogComponent,
        NavbarComponent,
        SidebarComponent,
        AdminLayoutComponent,
      ],
      providers: [
        TribunalDataService,
        AuthService,
        { provide: NotificationService, useValue: notifSpy },
        { provide: MatDialog, useValue: dialogSpy },
        { provide: MatDialogRef, useValue: jasmine.createSpyObj('MatDialogRef', ['close']) },
        { provide: MAT_DIALOG_DATA, useValue: { legajo: '74907', nombreSocio: 'Test' } },
        {
          provide: ActivatedRoute,
          useValue: { snapshot: { paramMap: { get: () => '1' } } },
        },
      ],
      schemas: [NO_ERRORS_SCHEMA],
    }).compileComponents();

    const http = TestBed.inject(HttpTestingController);
    const components: Array<ComponentFixture<any>> = [
      TestBed.createComponent(ReportesComponent),
      TestBed.createComponent(CalendarioInstitucionalComponent),
      TestBed.createComponent(VisorExpedienteComponent),
      TestBed.createComponent(ReglamentosComponent),
      TestBed.createComponent(ExpedientesSocioDialogComponent),
      TestBed.createComponent(NavbarComponent),
      TestBed.createComponent(SidebarComponent),
      TestBed.createComponent(AdminLayoutComponent),
    ];

    components.forEach((f) => f.detectChanges());

    const repInst = components[0].componentInstance as ReportesComponent;
    const idTimer = window.setTimeout(() => {}, 60000);
    repInst['revokeTimers'].add(idTimer);

    const visorInst = components[2].componentInstance as VisorExpedienteComponent;
    visorInst['scheduleTimer'](() => {}, 60000);

    const pendingHttp = http.match(() => true);

    components.forEach((f) => {
      const inst = f.componentInstance;
      f.destroy();
      expect(inst['destroy$'].isStopped).toBeTrue();
    });

    expect(repInst['revokeTimers'].size).toBe(0);
    expect(visorInst['activeTimers'].size).toBe(0);
    expect(pendingHttp.every((r) => r.cancelled)).toBeTrue();
    http.verify();
  });
});
