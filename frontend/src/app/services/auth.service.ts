import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export type RolRbac = 'SOCIO' | 'FISCALIZADORA' | 'CD' | 'TD' | 'ADMIN';

export interface PerfilSocio {
  legajo: string;
  first_name: string;
  last_name: string;
  email: string;
  role: RolRbac;
  category: 'PASSIVE' | 'ACTIVE';
  category_display: string;
  subcomision: string | null;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: PerfilSocio;
}

const ACCESS_TOKEN_KEY = 'aveit.access';
const REFRESH_TOKEN_KEY = 'aveit.refresh';
const PROFILE_KEY = 'aveit.perfil';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private perfilSubject = new BehaviorSubject<PerfilSocio | null>(this.leerPerfil());
  perfil$ = this.perfilSubject.asObservable();

  constructor(private http: HttpClient) {}

  login(identifier: string, password: string): Observable<LoginResponse> {
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login/`, { identifier, password })
      .pipe(tap(respuesta => this.guardarSesion(respuesta)));
  }

  logout(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(PROFILE_KEY);
    this.perfilSubject.next(null);
  }

  getToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getPerfil(): PerfilSocio | null {
    return this.perfilSubject.value;
  }

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  }

  /**
   * Sólo sirve para mostrar u ocultar elementos de la interfaz. La decisión
   * vinculante la toma el backend en cada petición: un rol que llegue a una
   * ruta que no le corresponde recibe 403 igual.
   */
  tieneRol(...roles: RolRbac[]): boolean {
    const perfil = this.getPerfil();
    return perfil !== null && roles.includes(perfil.role);
  }

  private guardarSesion(respuesta: LoginResponse): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, respuesta.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, respuesta.refresh);
    localStorage.setItem(PROFILE_KEY, JSON.stringify(respuesta.user));
    this.perfilSubject.next(respuesta.user);
  }

  private leerPerfil(): PerfilSocio | null {
    const crudo = localStorage.getItem(PROFILE_KEY);
    if (!crudo) {
      return null;
    }
    try {
      return JSON.parse(crudo) as PerfilSocio;
    } catch {
      return null;
    }
  }
}
