import { HttpErrorResponse, HttpHandler, HttpRequest } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Subject, throwError } from 'rxjs';
import { AuthInterceptor } from './auth.interceptor';
import { AuthService } from './auth.service';

describe('AuthInterceptor', () => {
  let interceptor: AuthInterceptor;
  let auth: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;
  beforeEach(() => {
    auth = jasmine.createSpyObj('AuthService', ['getToken', 'logout', 'isAuthenticated']);
    auth.getToken.and.returnValue('old-token');
    auth.isAuthenticated.and.returnValue(true);
    router = jasmine.createSpyObj('Router', ['navigate']);
    router.navigate.and.returnValue(Promise.resolve(true));
    TestBed.configureTestingModule({ providers: [
      AuthInterceptor, { provide: AuthService, useValue: auth }, { provide: Router, useValue: router }
    ] });
    interceptor = TestBed.inject(AuthInterceptor);
  });

  it('redirige una sola vez ante 401 concurrentes y no propaga avisos de la pantalla anterior', () => {
    const first = new Subject<never>();
    const second = new Subject<never>();
    const errors = jasmine.createSpy('screenError');
    const handler = jasmine.createSpyObj<HttpHandler>('HttpHandler', ['handle']);
    handler.handle.and.returnValues(first, second);
    const request = new HttpRequest('GET', '/api/v1/calendario/');
    interceptor.intercept(request, handler).subscribe({ error: errors });
    interceptor.intercept(request, handler).subscribe({ error: errors });
    auth.logout.and.callFake(() => auth.getToken.and.returnValue(null));
    first.error(new HttpErrorResponse({ status: 401 }));
    second.error(new HttpErrorResponse({ status: 401 }));
    expect(auth.logout).toHaveBeenCalledTimes(1);
    expect(router.navigate).toHaveBeenCalledOnceWith(['/login'], { queryParams: { expirada: 1 } });
    expect(errors).not.toHaveBeenCalled();
  });

  it('ignora un 401 pendiente de una sesión anterior sin cerrar una sesión nueva', () => {
    const pending = new Subject<never>();
    const handler = { handle: () => pending } as HttpHandler;
    const errors = jasmine.createSpy('screenError');
    interceptor.intercept(new HttpRequest('GET', '/api/v1/calendario/'), handler).subscribe({ error: errors });
    auth.getToken.and.returnValue('new-token');
    pending.error(new HttpErrorResponse({ status: 401 }));
    expect(auth.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
    expect(errors).not.toHaveBeenCalled();
  });

  it('conserva errores de credenciales sin token y errores 403 para su manejo contextual', () => {
    for (const status of [401, 403]) {
      auth.getToken.and.returnValue(null);
      const error = new HttpErrorResponse({ status });
      const errors = jasmine.createSpy('screenError');
      const handler = { handle: () => throwError(() => error) } as HttpHandler;
      interceptor.intercept(new HttpRequest('POST', '/api/auth/login/', {}), handler).subscribe({ error: errors });
      expect(errors).toHaveBeenCalledOnceWith(error);
    }
    expect(auth.logout).not.toHaveBeenCalled();
  });

  it('recupera una sesión ausente ante 401 de un recurso protegido, sin mostrar credenciales faltantes', () => {
    auth.getToken.and.returnValue(null);
    const errors = jasmine.createSpy('screenError');
    const handler = { handle: () => throwError(() => new HttpErrorResponse({ status: 401 })) } as HttpHandler;
    interceptor.intercept(new HttpRequest('GET', '/api/v1/socios/me/points-history/'), handler)
      .subscribe({ error: errors });
    expect(auth.logout).toHaveBeenCalledOnceWith();
    expect(router.navigate).toHaveBeenCalledOnceWith(['/login'], { queryParams: { expirada: 1 } });
    expect(errors).not.toHaveBeenCalled();
  });

  it('un 401 de login informa credenciales inválidas aunque exista un token anterior', () => {
    const error = new HttpErrorResponse({ status: 401 });
    const errors = jasmine.createSpy('loginError');
    const handler = { handle: (request: HttpRequest<unknown>) => {
      expect(request.headers.has('Authorization')).toBeFalse();
      return throwError(() => error);
    } } as HttpHandler;
    interceptor.intercept(new HttpRequest('POST', '/api/v1/auth/login/', {}), handler)
      .subscribe({ error: errors });
    expect(errors).toHaveBeenCalledOnceWith(error);
    expect(auth.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('recupera una sola vez ante dos 401 concurrentes capturados sin token', () => {
    auth.getToken.and.returnValue(null);
    const first = new Subject<never>();
    const second = new Subject<never>();
    const handler = jasmine.createSpyObj<HttpHandler>('HttpHandler', ['handle']);
    handler.handle.and.returnValues(first, second);
    const request = new HttpRequest('GET', '/api/v1/socios/me/points-history/');
    interceptor.intercept(request, handler).subscribe();
    interceptor.intercept(request, handler).subscribe();
    first.error(new HttpErrorResponse({ status: 401 }));
    second.error(new HttpErrorResponse({ status: 401 }));
    expect(auth.logout).toHaveBeenCalledTimes(1);
    expect(router.navigate).toHaveBeenCalledTimes(1);
  });

  it('ignora un 401 anónimo anterior que llega después de un nuevo login', () => {
    auth.getToken.and.returnValue(null);
    const pending = new Subject<never>();
    interceptor.intercept(new HttpRequest('GET', '/api/v1/socios/me/points-history/'), { handle: () => pending } as HttpHandler)
      .subscribe();
    auth.getToken.and.returnValue('new-token');
    pending.error(new HttpErrorResponse({ status: 401 }));
    expect(auth.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('no transmite nuestro token ni interpreta un 401 externo como sesión expirada', () => {
    const error = new HttpErrorResponse({ status: 401 });
    const errors = jasmine.createSpy('externalError');
    const handler = { handle: (request: HttpRequest<unknown>) => {
      expect(request.headers.has('Authorization')).toBeFalse();
      return throwError(() => error);
    } } as HttpHandler;
    interceptor.intercept(new HttpRequest('GET', 'https://public.example/status'), handler).subscribe({ error: errors });
    expect(errors).toHaveBeenCalledOnceWith(error);
    expect(auth.logout).not.toHaveBeenCalled();
    expect(router.navigate).not.toHaveBeenCalled();
  });
});
