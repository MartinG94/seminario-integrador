import { A11yModule, CdkTrapFocus } from '@angular/cdk/a11y';
import { OverlayContainer, OverlayModule } from '@angular/cdk/overlay';
import { PortalModule } from '@angular/cdk/portal';
import { CommonModule } from '@angular/common';
import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule } from '@angular/material/dialog';
import { By } from '@angular/platform-browser';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of, throwError } from 'rxjs';

import { NotificationCenterComponent } from '../components/notification-center/notification-center.component';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { Expediente, TribunalDataService } from '../services/tribunal-data.service';
import { GestionarExpedientesComponent } from './gestionar-expedientes.component';

describe('SCRUM-77 notificaciones dentro del detalle con foco contenido', () => {
  let board: ComponentFixture<GestionarExpedientesComponent>;
  let center: ComponentFixture<NotificationCenterComponent>;
  let notifications: NotificationService;
  let overlay: HTMLElement;
  let dataService: jasmine.SpyObj<TribunalDataService>;
  const caseFixture: Expediente = {
    id: '77', numero: 'EXP-77/2026', socio: 'Socio sintético', legajo: '99077001',
    subcomision: 'Cómputos', motivo: 'Causa sintética para verificar el foco',
    fechaCreacion: '2026-10-12', estado: 'creado', urgencia: 'normal',
    horasRestantes: 0, tipo: 'falta', puntos: -1, cantidadSocios: 1
  };

  beforeEach(async () => {
    dataService = jasmine.createSpyObj('TribunalDataService', ['obtenerTablero'], {
      expedientes$: of([caseFixture])
    });
    dataService.obtenerTablero.and.returnValue(of({ columns: [] }));
    await TestBed.configureTestingModule({
      declarations: [GestionarExpedientesComponent, NotificationCenterComponent],
      imports: [CommonModule, FormsModule, MatButtonModule, MatDialogModule,
        NoopAnimationsModule, A11yModule, OverlayModule, PortalModule],
      providers: [
        { provide: AuthService, useValue: { tieneRol: () => false } },
        { provide: TribunalDataService, useValue: dataService }
      ]
    }).compileComponents();
    notifications = TestBed.inject(NotificationService);
    overlay = TestBed.inject(OverlayContainer).getContainerElement();
    center = TestBed.createComponent(NotificationCenterComponent);
    center.detectChanges();
    board = TestBed.createComponent(GestionarExpedientesComponent);
    board.detectChanges();
  });

  function detectChanges(): void {
    board.detectChanges();
    center.detectChanges();
  }

  function open(): HTMLElement {
    const card = board.nativeElement.querySelector('.kanban-card-mat') as HTMLElement;
    card.focus();
    card.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    detectChanges();
    tick();
    detectChanges();
    return card;
  }

  function closeButton(): HTMLButtonElement {
    return board.nativeElement.querySelector('[cdkFocusInitial]') as HTMLButtonElement;
  }

  function notice(): HTMLElement | null {
    return document.querySelector('.user-notification');
  }

  it('permite alcanzar y cerrar con teclado un aviso previo sin salir del detalle', fakeAsync(() => {
    dataService.obtenerTablero.and.returnValue(throwError(() => ({ status: 500 })));
    board.componentInstance.cargarDatosTablero();
    detectChanges();
    expect(notice()?.textContent).toContain('No se pudo cargar el tablero.');

    open();
    const dialog = board.nativeElement.querySelector('[role="dialog"]') as HTMLElement;
    const notification = notice()!;
    expect(dialog.contains(notification)).withContext('La notificación pertenece al foco del detalle').toBeTrue();
    const trap = board.debugElement.query(By.directive(CdkTrapFocus)).injector.get(CdkTrapFocus).focusTrap;
    expect(trap.focusLastTabbableElement()).toBeTrue();
    const closeNotice = notification.querySelector('button') as HTMLButtonElement;
    expect(document.activeElement).withContext('La X participa del mismo recorrido de Tab').toBe(closeNotice);
    closeNotice.click();
    detectChanges();
    expect(notice()).toBeNull();
    expect(document.activeElement).withContext('Cerrar el aviso devuelve el foco al detalle').toBe(closeButton());
    // FocusMonitor de CDK libera el origen de teclado en el siguiente milisegundo.
    tick(1);
  }));

  it('devuelve el mismo aviso al overlay al cerrar y conserva su vencimiento original', fakeAsync(() => {
    notifications.info('Aviso previo a abrir el expediente.');
    detectChanges();
    const notification = notice()!;
    tick(2000);
    const origin = open();
    expect(board.nativeElement.querySelector('[role="dialog"]').contains(notification)).toBeTrue();
    closeButton().dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    detectChanges();
    tick();
    detectChanges();

    expect(board.nativeElement.querySelector('[role="dialog"]')).toBeNull();
    expect(document.activeElement).toBe(origin);
    expect(overlay.contains(notification)).withContext('El DOM regresa al overlay global').toBeTrue();
    expect(notice()).toBe(notification);
    tick(7999);
    detectChanges();
    expect(notice()).toBe(notification);
    tick(1);
    detectChanges();
    expect(notice()).toBeNull();
  }));

  it('conserva el aviso y su plazo al destruir la pantalla con el detalle abierto', fakeAsync(() => {
    notifications.warning('Aviso que permanece durante la navegación.');
    detectChanges();
    const notification = notice()!;
    open();
    expect(board.nativeElement.querySelector('[role="dialog"]').contains(notification)).toBeTrue();
    tick(3000);
    board.destroy();
    center.detectChanges();

    expect(overlay.contains(notification)).withContext('Destruir la vista libera el portal').toBeTrue();
    expect(notice()).toBe(notification);
    tick(6999);
    center.detectChanges();
    expect(notice()).toBe(notification);
    tick(1);
    center.detectChanges();
    expect(notice()).toBeNull();
  }));
});
