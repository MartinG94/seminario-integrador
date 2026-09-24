import { HttpClientTestingModule } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot } from '@angular/router';

import { AuthGuard } from './auth.guard';
import { AuthService } from './auth.service';

describe('AuthGuard', () => {
  let guard: AuthGuard;
  let auth: AuthService;
  let router: Router;

  const estado = { url: '/gestionar-expedientes' } as RouterStateSnapshot;
  const ruta = {} as ActivatedRouteSnapshot;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    guard = TestBed.inject(AuthGuard);
    auth = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
    spyOn(router, 'navigate');
  });

  it('permite el paso a una sesión iniciada', () => {
    spyOn(auth, 'isAuthenticated').and.returnValue(true);

    expect(guard.canActivate(ruta, estado)).toBeTrue();
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('redirige al login recordando el destino', () => {
    spyOn(auth, 'isAuthenticated').and.returnValue(false);

    expect(guard.canActivate(ruta, estado)).toBeFalse();
    expect(router.navigate).toHaveBeenCalledWith(['/login'], {
      queryParams: { volverA: '/gestionar-expedientes' }
    });
  });
});
