import { TestBed, async } from '@angular/core/testing';
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';
import { OverlayContainer, OverlayModule } from '@angular/cdk/overlay';
import { PortalModule } from '@angular/cdk/portal';
import { MatDialogModule } from '@angular/material/dialog';
import { NotificationCenterComponent } from './components/notification-center/notification-center.component';
import { NotificationService } from './services/notification.service';

import { AppComponent } from './app.component';

@Component({ template: '<p>Vista de prueba</p>' })
class RoutedTestComponent {}

describe('AppComponent', () => {
  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [
        AppComponent, RoutedTestComponent, NotificationCenterComponent
      ],
      imports: [OverlayModule, PortalModule, MatDialogModule, RouterTestingModule.withRoutes([{ path: 'prueba', component: RoutedTestComponent }])],
    }).compileComponents();
  }));

  it('should create the app', async(() => {
    const fixture = TestBed.createComponent(AppComponent);
    const app = fixture.debugElement.componentInstance;
    expect(app).toBeTruthy();
  }));

  it('aloja el outlet de navegación', async(() => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('router-outlet')).toBeTruthy();
  }));

  it('muestra la vista de la ruta activa', async(async () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const notifications = TestBed.inject(NotificationService);
    const id = notifications.success('Cambios guardados.');
    fixture.detectChanges();
    await TestBed.inject(Router).navigateByUrl('/prueba');
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Vista de prueba');
    expect(TestBed.inject(OverlayContainer).getContainerElement().textContent).toContain('Cambios guardados.');
    notifications.dismiss(id);
  }));
});
