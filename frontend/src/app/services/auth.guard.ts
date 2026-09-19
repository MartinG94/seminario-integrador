import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';

import { AuthService } from './auth.service';

/**
 * Evita mostrar pantallas de la aplicación a quien no inició sesión.
 *
 * Es sólo una mejora de experiencia de usuario: cada endpoint que consuman
 * esas pantallas revalida la autorización en el servidor.
 */
@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private auth: AuthService, private router: Router) {}

  canActivate(_route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    if (this.auth.isAuthenticated()) {
      return true;
    }
    this.router.navigate(['/login'], { queryParams: { volverA: state.url } });
    return false;
  }
}
