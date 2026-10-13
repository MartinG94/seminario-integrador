import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { fakeAsync, flushMicrotasks, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { EMPTY } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { AuthService, LoginResponse } from './auth.service';
import { AuthInterceptor } from './auth.interceptor';
import { SocioApiService } from './socio-api.service';

describe('Sesión autenticada e historial propio (TS77.61)', () => {
  let auth: AuthService;
  let http: HttpTestingController;
  let api: SocioApiService;
  let navigate: jasmine.Spy;

  function response(identifier: string, token = 'test-current-access'): LoginResponse {
    return { access: token, refresh: 'test-refresh', user: {
      legajo: identifier, first_name: 'Socio', last_name: 'De Prueba', email: 'test@aveit.test',
      role: 'SOCIO', category: 'SENIOR', category_display: 'Senior', subcomision: 'Cómputos'
    } };
  }

  function login(identifier: string, token = 'test-current-access'): void {
    auth.login(identifier).subscribe();
    http.expectOne('/api/v1/auth/login/').flush(response(identifier, token));
  }

  beforeEach(() => {
    localStorage.clear();
    navigate = jasmine.createSpy('navigate');
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true },
        { provide: Router, useValue: { navigate } }
      ]
    });
    auth = TestBed.inject(AuthService);
    api = TestBed.inject(SocioApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => { http.verify(); localStorage.clear(); });

  ['99077001', '74907'].forEach(identifier => {
    it(`el login ${identifier} guarda Bearer antes de consultar historial al emitir el perfil`, () => {
      const subscription = auth.perfil$.pipe(switchMap(profile => profile ? api.getOwnPointsHistory() : EMPTY)).subscribe();
      login(identifier);
      const request = http.expectOne('/api/v1/socios/me/points-history/');
      expect(request.request.headers.get('Authorization')).toBe('Bearer test-current-access');
      request.flush({ points_balance: 0, entries: [] });
      subscription.unsubscribe();
    });
  });

  it('un logout de otra pestaña elimina el perfil que podría generar lecturas sin credenciales', () => {
    login('99077001');
    localStorage.removeItem('aveit.access');
    localStorage.removeItem('aveit.perfil');
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'aveit.access', oldValue: 'test-current-access', newValue: null, storageArea: localStorage
    }));
    expect(auth.getPerfil()).toBeNull();
    expect(auth.isAuthenticated()).toBeFalse();
    http.expectNone('/api/v1/socios/me/points-history/');
    expect(navigate).toHaveBeenCalledOnceWith(['/login']);
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'aveit.perfil', oldValue: '{}', newValue: null, storageArea: localStorage
    }));
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it('un cambio de cuenta en otra pestaña cancela lecturas y confirma el perfil nuevo con el token nuevo', fakeAsync(() => {
    const subscription = auth.perfil$.pipe(switchMap(profile => profile ? api.getOwnPointsHistory() : EMPTY)).subscribe();
    login('99077001');
    const previous = http.expectOne('/api/v1/socios/me/points-history/');
    localStorage.setItem('aveit.access', 'test-new-access');
    localStorage.setItem('aveit.perfil', JSON.stringify(response('99077009', 'test-new-access').user));
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'aveit.access', oldValue: 'test-current-access', newValue: 'test-new-access', storageArea: localStorage
    }));
    expect(previous.cancelled).toBeTrue();
    expect(auth.getPerfil()).toBeNull();
    flushMicrotasks();
    const me = http.expectOne('/api/v1/auth/me/');
    expect(me.request.headers.get('Authorization')).toBe('Bearer test-new-access');
    me.flush(response('99077009', 'test-new-access').user);
    const current = http.expectOne('/api/v1/socios/me/points-history/');
    expect(current.request.headers.get('Authorization')).toBe('Bearer test-new-access');
    current.flush({ points_balance: 0, entries: [] });
    expect(auth.getPerfil()?.legajo).toBe('99077009');
    expect(navigate).not.toHaveBeenCalled();
    subscription.unsubscribe();
  }));

  it('localStorage.clear de otra pestaña vuelve al login cuando existía una sesión activa', () => {
    login('99077001');
    localStorage.clear();
    window.dispatchEvent(new StorageEvent('storage', { key: null, storageArea: localStorage }));
    expect(auth.getPerfil()).toBeNull();
    expect(navigate).toHaveBeenCalledOnceWith(['/login']);
  });

  it('recupera login aunque el perfil de la sesión activa todavía esté rehidratándose', fakeAsync(() => {
    login('99077001');
    localStorage.setItem('aveit.access', 'test-new-access');
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'aveit.access', oldValue: 'test-current-access', newValue: 'test-new-access', storageArea: localStorage
    }));
    expect(auth.getPerfil()).toBeNull();
    flushMicrotasks();
    const pendingProfile = http.expectOne('/api/v1/auth/me/');
    localStorage.removeItem('aveit.access');
    window.dispatchEvent(new StorageEvent('storage', {
      key: 'aveit.access', oldValue: 'test-new-access', newValue: null, storageArea: localStorage
    }));
    expect(pendingProfile.cancelled).toBeTrue();
    expect(navigate).toHaveBeenCalledOnceWith(['/login']);
  }));

  it('un evento vacío sin sesión anterior no redirige ni cambia el flujo de inicio', () => {
    window.dispatchEvent(new StorageEvent('storage', { key: null, storageArea: localStorage }));
    expect(navigate).not.toHaveBeenCalled();
    login('99077001');
    expect(auth.getPerfil()?.legajo).toBe('99077001');
    expect(navigate).not.toHaveBeenCalled();
  });

  it('un 404 por identidad institucional ausente conserva autenticación y no fabrica cero', () => {
    login('74907');
    let points: number | null = null;
    let status = 0;
    api.getOwnPointsHistory().subscribe({ next: result => points = result.points_balance, error: error => status = error.status });
    const request = http.expectOne('/api/v1/socios/me/points-history/');
    expect(request.request.headers.get('Authorization')).toBe('Bearer test-current-access');
    request.flush({}, { status: 404, statusText: 'Not Found' });
    expect(status).toBe(404);
    expect(points).toBeNull();
    expect(auth.isAuthenticated()).toBeTrue();
    expect(navigate).not.toHaveBeenCalled();
  });
});
