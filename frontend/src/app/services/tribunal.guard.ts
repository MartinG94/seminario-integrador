import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';

import { AuthService, RolRbac } from './auth.service';

/**
 * Permite el acceso a la gestión operativa de expedientes únicamente
 * a los roles institucionales habilitados para la ruta protegida.
 * Redirige a /403 si el socio está suspendido o carece del rol requerido.
 */
@Injectable({ providedIn: 'root' })
export class TribunalGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, _state: RouterStateSnapshot): boolean {
    if (this.auth.isSuspended()) {
      this.router.navigate(['/403']);
      return false;
    }

    const roles: RolRbac[] = route.data?.roles || ['TD', 'ADMIN', 'CD'];
    if (this.auth.tieneRol(...roles)) {
      return true;
    }
    this.router.navigate(['/403']);
    return false;
  }
}
