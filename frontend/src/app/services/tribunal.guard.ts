import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';

import { AuthService, RolRbac } from './auth.service';

/**
 * Permite el acceso a la gestión operativa de expedientes únicamente
 * a los roles institucionales habilitados: Tribunal de Disciplina (TD),
 * Administrador (ADMIN) y Comisión Directiva (CD).
 * Redirige a /mis-expedientes si el usuario no tiene los permisos suficientes.
 */
@Injectable({ providedIn: 'root' })
export class TribunalGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

  canActivate(route: ActivatedRouteSnapshot, _state: RouterStateSnapshot): boolean {
    const roles: RolRbac[] = route.data?.roles || ['TD', 'ADMIN', 'CD'];
    if (this.auth.tieneRol(...roles)) {
      return true;
    }
    this.router.navigate(['/mis-expedientes']);
    return false;
  }
}
