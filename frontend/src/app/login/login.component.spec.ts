import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';
import { LoginComponent } from './login.component';

describe('LoginComponent feedback', () => {
  let fixture: ComponentFixture<LoginComponent>;
  let component: LoginComponent;
  let auth: jasmine.SpyObj<AuthService>;
  let notifications: jasmine.SpyObj<NotificationService>;
  beforeEach(async () => {
    auth = jasmine.createSpyObj('AuthService', ['isAuthenticated', 'login']);
    auth.isAuthenticated.and.returnValue(false);
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'warning', 'success']);
    await TestBed.configureTestingModule({
      imports: [ReactiveFormsModule], declarations: [LoginComponent],
      providers: [
        { provide: AuthService, useValue: auth },
        { provide: NotificationService, useValue: notifications },
        { provide: ActivatedRoute, useValue: { snapshot: { queryParams: { expirada: '1' } } } },
        { provide: Router, useValue: jasmine.createSpyObj('Router', ['navigateByUrl']) }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('anuncia sesión expirada mediante una notificación sin aviso dentro del formulario', () => {
    expect(notifications.warning).toHaveBeenCalledOnceWith('Tu sesión expiró. Volvé a iniciar sesión para continuar.');
    expect(fixture.nativeElement.textContent).not.toContain('Tu sesión expiró');
  });
  it('notifica validación al enviar y conserva el campo marcado como inválido', () => {
    component.ingresar();
    fixture.detectChanges();
    expect(notifications.error).toHaveBeenCalledWith('Ingresá tu Número de Socio.');
    expect(auth.login).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('input').getAttribute('aria-invalid')).toBe('true');
    expect(fixture.nativeElement.querySelector('[role="alert"]')).toBeNull();
  });
  it('notifica credenciales incorrectas y permite reintentar', () => {
    auth.login.and.returnValue(throwError(() => ({ status: 401 })));
    component.formulario.patchValue({ identifier: 'incorrecto' });
    component.ingresar();
    expect(notifications.error).toHaveBeenCalledOnceWith('Número de Socio no encontrado o cuenta no habilitada.');
    expect(component.enviando).toBeFalse();
    auth.login.and.returnValue(of({} as never));
    component.ingresar();
    expect(TestBed.inject(Router).navigateByUrl).toHaveBeenCalledWith('/mis-expedientes');
  });
});
