import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { AuthService, LoginResponse } from './auth.service';

const RESPUESTA_LOGIN: LoginResponse = {
  access: 'access-token-de-prueba',
  refresh: 'refresh-token-de-prueba',
  user: {
    legajo: '408917',
    first_name: 'Nicolás',
    last_name: 'Rosales',
    email: '408917@aveit.test',
    role: 'TD',
    category: 'ACTIVE',
    category_display: 'Activo',
    subcomision: 'Cómputos'
  }
};

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('parte sin sesión activa', () => {
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.getToken()).toBeNull();
    expect(service.getPerfil()).toBeNull();
  });

  it('almacena tokens y perfil al iniciar sesión', () => {
    service.login('408917', 'Aveit-Demo-2026!').subscribe();

    const peticion = httpMock.expectOne('/api/v1/auth/login/');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({
      identifier: '408917',
      password: 'Aveit-Demo-2026!'
    });
    peticion.flush(RESPUESTA_LOGIN);

    expect(service.isAuthenticated()).toBeTrue();
    expect(service.getToken()).toBe('access-token-de-prueba');
    expect(service.getPerfil()?.role).toBe('TD');
  });

  it('no guarda la contraseña en el almacenamiento local', () => {
    service.login('408917', 'Aveit-Demo-2026!').subscribe();
    httpMock.expectOne('/api/v1/auth/login/').flush(RESPUESTA_LOGIN);

    const contenido = Object.keys(localStorage)
      .map(clave => localStorage.getItem(clave))
      .join('|');
    expect(contenido).not.toContain('Aveit-Demo-2026!');
  });

  it('no deja sesión iniciada si las credenciales son inválidas', () => {
    let statusRecibido = 0;
    service.login('408917', 'clave-mala').subscribe({
      error: error => (statusRecibido = error.status)
    });

    httpMock
      .expectOne('/api/v1/auth/login/')
      .flush({ detail: 'Credenciales inválidas.' }, { status: 401, statusText: 'Unauthorized' });

    expect(statusRecibido).toBe(401);
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.getToken()).toBeNull();
  });

  it('descarta la sesión al cerrarla', () => {
    service.login('408917', 'Aveit-Demo-2026!').subscribe();
    httpMock.expectOne('/api/v1/auth/login/').flush(RESPUESTA_LOGIN);

    service.logout();

    expect(service.isAuthenticated()).toBeFalse();
    expect(service.getPerfil()).toBeNull();
    expect(localStorage.getItem('aveit.access')).toBeNull();
  });

  it('expone el rol para decidir qué muestra la interfaz', () => {
    service.login('408917', 'Aveit-Demo-2026!').subscribe();
    httpMock.expectOne('/api/v1/auth/login/').flush(RESPUESTA_LOGIN);

    expect(service.tieneRol('TD', 'CD')).toBeTrue();
    expect(service.tieneRol('SOCIO')).toBeFalse();
  });

  it('emite el perfil a los suscriptores', () => {
    const emitidos: (string | null)[] = [];
    service.perfil$.subscribe(perfil => emitidos.push(perfil?.role ?? null));

    service.login('408917', 'Aveit-Demo-2026!').subscribe();
    httpMock.expectOne('/api/v1/auth/login/').flush(RESPUESTA_LOGIN);
    service.logout();

    expect(emitidos).toEqual([null, 'TD', null]);
  });
});
