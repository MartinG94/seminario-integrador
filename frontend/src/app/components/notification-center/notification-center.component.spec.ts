import { ApplicationRef, Component, TemplateRef, ViewChild } from '@angular/core';
import { ComponentFixture, fakeAsync, TestBed, tick } from '@angular/core/testing';
import { OverlayContainer, OverlayModule } from '@angular/cdk/overlay';
import { PortalModule } from '@angular/cdk/portal';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { NotificationService } from '../../services/notification.service';
import { NotificationCenterComponent } from './notification-center.component';

@Component({ template: '<ng-template #content><h2 mat-dialog-title>Prueba</h2><mat-dialog-content>Contenido</mat-dialog-content></ng-template>' })
class DialogTestComponent { @ViewChild('content') content: TemplateRef<unknown>; }

describe('NotificationCenterComponent', () => {
  let fixture: ComponentFixture<NotificationCenterComponent>;
  let service: NotificationService;
  let container: HTMLElement;
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [NotificationCenterComponent, DialogTestComponent],
      imports: [OverlayModule, PortalModule, MatDialogModule, NoopAnimationsModule]
    }).compileComponents();
    fixture = TestBed.createComponent(NotificationCenterComponent);
    service = TestBed.inject(NotificationService);
    container = TestBed.inject(OverlayContainer).getContainerElement();
    fixture.detectChanges();
  });

  it('muestra texto plano, anuncia errores y permite cerrar con una X accesible', () => {
    service.error('<img src=x onerror=alert(1)>');
    fixture.detectChanges();
    const notice = container.querySelector('[role="alert"]') as HTMLElement;
    expect(notice.textContent).toContain('<img src=x onerror=alert(1)>');
    expect(notice.querySelector('img')).toBeNull();
    const close = notice.querySelector('button') as HTMLButtonElement;
    expect(close.getAttribute('aria-label')).toContain('Cerrar notificación');
    close.click();
    fixture.detectChanges();
    expect(container.querySelector('[role="alert"]')).toBeNull();
  });

  it('incorpora la X al foco del diálogo y conserva el aviso al cerrarlo', fakeAsync(() => {
    const dialogFixture = TestBed.createComponent(DialogTestComponent);
    dialogFixture.detectChanges();
    const dialog = TestBed.inject(MatDialog).open(dialogFixture.componentInstance.content);
    TestBed.inject(ApplicationRef).tick();
    tick();
    service.success('Guardado desde el modal.');
    fixture.detectChanges();
    const notice = container.querySelector('[role="status"]') as HTMLElement;
    expect(notice.closest('[aria-hidden="true"]')).toBeNull();
    expect(notice.closest('.cdk-overlay-container')).toBe(container);
    expect(notice.closest('[role="dialog"]')).toBeTruthy();
    dialog.close();
    TestBed.inject(ApplicationRef).tick();
    tick(500);
    fixture.detectChanges();
    expect(container.textContent).toContain('Guardado desde el modal.');
    expect(notice.closest('[role="dialog"]')).toBeNull();
    tick(10000);
    fixture.detectChanges();
    expect(container.querySelector('[role="status"]')).toBeNull();
    dialogFixture.destroy();
  }));

  it('devuelve el foco al diálogo cuando se cierra o vence un aviso enfocado', fakeAsync(() => {
    const dialogFixture = TestBed.createComponent(DialogTestComponent);
    dialogFixture.detectChanges();
    const dialog = TestBed.inject(MatDialog).open(dialogFixture.componentInstance.content);
    TestBed.inject(ApplicationRef).tick();
    tick();
    service.error('Error de prueba.');
    fixture.detectChanges();
    const close = container.querySelector('.notification-close') as HTMLButtonElement;
    close.focus();
    close.click();
    fixture.detectChanges();
    expect(document.activeElement?.getAttribute('role')).toBe('dialog');
    service.info('Otro aviso.');
    fixture.detectChanges();
    (container.querySelector('.notification-close') as HTMLButtonElement).focus();
    tick(10000);
    fixture.detectChanges();
    expect(document.activeElement?.getAttribute('role')).toBe('dialog');
    dialog.close();
    TestBed.inject(ApplicationRef).tick();
    tick(500);
    dialogFixture.destroy();
  }));
});
