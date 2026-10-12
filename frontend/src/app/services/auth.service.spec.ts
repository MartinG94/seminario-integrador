import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { fakeAsync, flushMicrotasks, TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';

import { AuthService, LoginResponse, MembershipCategory } from './auth.service';
import { AuthInterceptor } from './auth.interceptor';

const RESPUESTA_LOGIN: LoginResponse = {
  access: 'access-token-de-prueba',
  refresh: 'refresh-token-de-prueba',
  user: {
    legajo: '408917',
    first_name: 'Nicolás',
    last_name: 'Rosales',
    email: '408917@aveit.test',
    role: 'TD',
    category: 'SENIOR',
    category_display: 'Senior',
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

  it('permite iniciar sesión sólo con el legajo sin contraseña', () => {
    service.login('408917').subscribe();

    const peticion = httpMock.expectOne('/api/v1/auth/login/');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({
      identifier: '408917'
    });
    peticion.flush(RESPUESTA_LOGIN);

    expect(service.isAuthenticated()).toBeTrue();
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

describe('AuthService — perfil confirmado (TS77.35)', () => {
  let http: HttpTestingController;
  let router: jasmine.SpyObj<Router>;
  const currentProfile = (category = 'SENIOR') => ({
    ...RESPUESTA_LOGIN.user,
    category,
    category_display: category === 'JUNIOR' ? 'Junior' : category === 'EX_TRAVELER' ? 'Exviajero' : 'Senior'
  });
  const restore = (category?: string): AuthService => {
    localStorage.setItem('aveit.access', 'historical-access');
    localStorage.setItem('aveit.refresh', 'historical-refresh');
    if (category) {
      localStorage.setItem('aveit.perfil', JSON.stringify({
        ...RESPUESTA_LOGIN.user,
        category,
        category_display: category === 'PASSIVE' ? 'Pasivo' : 'Activo'
      }));
    }
    return TestBed.inject(AuthService);
  };

  beforeEach(() => {
    localStorage.clear();
    router = jasmine.createSpyObj<Router>('Router', ['navigate']);
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [
        { provide: Router, useValue: router },
        { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
      ]
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  ['PASSIVE', 'ACTIVE', 'JUNIOR', 'SENIOR', 'EX_TRAVELER'].forEach(cachedCategory => {
    it(`confirma por me el perfil cacheado ${cachedCategory} sin traducirlo`, fakeAsync(() => {
      const service = restore(cachedCategory);
      expect(service.isAuthenticated()).toBeTrue();
      expect(service.getPerfil()?.role).toBe('TD');
      expect(service.tieneRol('TD')).toBeTrue();
      expect(service.getPerfil()?.category).toBeNull();
      expect(service.getPerfil()?.category_display).toBe('');

      flushMicrotasks();
      const request = http.expectOne('/api/v1/auth/me/');
      expect(request.request.method).toBe('GET');
      expect(request.request.headers.get('Authorization')).toBe('Bearer historical-access');
      request.flush(currentProfile());

      expect(service.getPerfil()?.category).toBe('SENIOR');
      expect(service.getPerfil()?.category_display).toBe('Senior');
      expect(JSON.parse(localStorage.getItem('aveit.perfil')!).category).toBe('SENIOR');
      expect(service.getToken()).toBe('historical-access');
      expect(localStorage.getItem('aveit.refresh')).toBe('historical-refresh');
    }));
  });

  const confirmedCategories: MembershipCategory[] = ['JUNIOR', 'SENIOR', 'EX_TRAVELER'];
  confirmedCategories.forEach(category => {
    it(`usa ${category} de me y no el claim ni el perfil históricos`, fakeAsync(() => {
      const service = restore('PASSIVE');
      flushMicrotasks();
      http.expectOne('/api/v1/auth/me/').flush(currentProfile(category));
      expect(service.getPerfil()?.category).toBe(category);
      expect(service.getPerfil()?.role).toBe('TD');
    }));
  });

  it('emite clasificación pendiente y luego confirmada a los suscriptores', fakeAsync(() => {
    const service = restore('PASSIVE');
    const categories: (string | null)[] = [];
    service.perfil$.subscribe(profile => categories.push(profile?.category ?? null));
    flushMicrotasks();
    http.expectOne('/api/v1/auth/me/').flush(currentProfile());
    expect(categories).toEqual([null, 'SENIOR']);
  }));

  it('recupera el perfil con token aunque no haya caché', fakeAsync(() => {
    const service = restore();
    expect(service.getPerfil()).toBeNull();
    flushMicrotasks();
    http.expectOne('/api/v1/auth/me/').flush(currentProfile('EX_TRAVELER'));
    expect(service.getPerfil()?.category).toBe('EX_TRAVELER');
  }));

  it('recupera un caché ilegible desde me sin convertirlo en un perfil', fakeAsync(() => {
    localStorage.setItem('aveit.perfil', '{invalid');
    const service = restore();
    expect(service.getPerfil()).toBeNull();
    flushMicrotasks();
    http.expectOne('/api/v1/auth/me/').flush(currentProfile('JUNIOR'));
    expect(service.getPerfil()?.category).toBe('JUNIOR');
  }));

  it('ignora un perfil sin token y no consulta me', fakeAsync(() => {
    localStorage.setItem('aveit.perfil', JSON.stringify(currentProfile()));
    const service = TestBed.inject(AuthService);
    flushMicrotasks();
    expect(service.getPerfil()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
    http.expectNone('/api/v1/auth/me/');
  }));

  [403, 500].forEach(status => {
    it(`conserva la sesión y el rol ante HTTP ${status} sin mostrar categoría antigua`, fakeAsync(() => {
      const service = restore('PASSIVE');
      flushMicrotasks();
      http.expectOne('/api/v1/auth/me/').flush({ detail: 'Error' }, { status, statusText: 'Error' });
      expect(service.getPerfil()?.category).toBeNull();
      expect(service.getPerfil()?.category_display).toBe('');
      expect(service.getPerfil()?.role).toBe('TD');
      expect(service.isAuthenticated()).toBeTrue();
      expect(router.navigate).not.toHaveBeenCalled();
    }));
  });

  it('conserva sesión y rol ante un fallo de red sin inventar clasificación', fakeAsync(() => {
    const service = restore('ACTIVE');
    flushMicrotasks();
    http.expectOne('/api/v1/auth/me/').error(new ProgressEvent('error'));
    expect(service.getPerfil()?.category).toBeNull();
    expect(service.getPerfil()?.role).toBe('TD');
    expect(service.getToken()).toBe('historical-access');
    expect(router.navigate).not.toHaveBeenCalled();
  }));

  it('mantiene el cierre de sesión y redirección del interceptor ante 401', fakeAsync(() => {
    const service = restore('PASSIVE');
    flushMicrotasks();
    http.expectOne('/api/v1/auth/me/').flush({}, { status: 401, statusText: 'Unauthorized' });
    expect(service.getPerfil()).toBeNull();
    expect(service.isAuthenticated()).toBeFalse();
    expect(localStorage.getItem('aveit.perfil')).toBeNull();
    expect(router.navigate).toHaveBeenCalledWith(['/login'], { queryParams: { expirada: 1 } });
  }));

  it('no inicia hidratación diferida después de logout', fakeAsync(() => {
    const service = restore('PASSIVE');
    service.logout();
    flushMicrotasks();
    http.expectNone('/api/v1/auth/me/');
    expect(service.getPerfil()).toBeNull();
  }));

  it('cancela la hidratación al cerrar sesión', fakeAsync(() => {
    const service = restore('PASSIVE');
    flushMicrotasks();
    const request = http.expectOne('/api/v1/auth/me/');
    service.logout();
    expect(request.cancelled).toBeTrue();
    expect(service.getPerfil()).toBeNull();
    expect(localStorage.getItem('aveit.perfil')).toBeNull();
  }));

  it('no sobreescribe un nuevo login con el perfil de la sesión anterior', fakeAsync(() => {
    const service = restore('PASSIVE');
    flushMicrotasks();
    const previous = http.expectOne('/api/v1/auth/me/');
    service.login('new-member').subscribe();
    http.expectOne('/api/v1/auth/login/').flush({
      access: 'new-access', refresh: 'new-refresh', user: currentProfile('JUNIOR')
    });
    expect(previous.cancelled).toBeTrue();
    expect(service.getPerfil()?.category).toBe('JUNIOR');
    expect(service.getToken()).toBe('new-access');
  }));
});
