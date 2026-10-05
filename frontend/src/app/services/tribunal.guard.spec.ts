import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthService } from './auth.service';
import { TribunalGuard } from './tribunal.guard';

describe('TribunalGuard', () => {
  let guard: TribunalGuard;
  let auth: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    auth = jasmine.createSpyObj('AuthService', ['tieneRol']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      providers: [
        TribunalGuard,
        { provide: AuthService, useValue: auth },
        { provide: Router, useValue: router },
      ]
    });

    guard = TestBed.inject(TribunalGuard);
  });

  it('permite el acceso si el socio tiene rol TD, ADMIN o CD', () => {
    auth.tieneRol.and.returnValue(true);
    expect(guard.canActivate({} as any, {} as any)).toBeTrue();
    expect(auth.tieneRol).toHaveBeenCalledWith('TD', 'ADMIN', 'CD');
  });

  it('bloquea y redirige a /mis-expedientes si el socio no tiene los roles permitidos', () => {
    auth.tieneRol.and.returnValue(false);
    expect(guard.canActivate({} as any, {} as any)).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/mis-expedientes']);
  });

  it('usa los roles declarados por la ruta cuando están presentes', () => {
    auth.tieneRol.and.returnValue(true);
    const route = { data: { roles: ['FISCALIZADORA', 'CD', 'TD'] } } as any;
    expect(guard.canActivate(route, {} as any)).toBeTrue();
    expect(auth.tieneRol).toHaveBeenCalledWith('FISCALIZADORA', 'CD', 'TD');
  });
});
