import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export type RolRbac = 'SOCIO' | 'FISCALIZADORA' | 'CD' | 'TD' | 'ADMIN';

export interface PerfilSocio {
  legajo: string;
  numero_socio?: number | null;
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

export interface ResetDemoResponse {
  detail: string;
  expedientes: string[];
}

const ACCESS_TOKEN_KEY = 'aveit.access';
const REFRESH_TOKEN_KEY = 'aveit.refresh';
const PROFILE_KEY = 'aveit.perfil';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private perfilSubject = new BehaviorSubject<PerfilSocio | null>(this.leerPerfil());
  perfil$ = this.perfilSubject.asObservable();

  constructor(private http: HttpClient) {}

  login(identifier: string, password?: string): Observable<LoginResponse> {
    const payload: { identifier: string; password?: string } = { identifier };
    if (password !== undefined) {
      payload.password = password;
    }
    return this.http
      .post<LoginResponse>(`${environment.apiUrl}/auth/login/`, payload)
      .pipe(tap(respuesta => this.guardarSesion(respuesta)));
  }

  logout(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(PROFILE_KEY);
    this.perfilSubject.next(null);
  }

  resetDemoDatabase(): Observable<ResetDemoResponse> {
    return this.http.post<ResetDemoResponse>(`${environment.apiUrl}/auth/reset-demo-db/`, {});
  }

  getToken(): string | null {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  }

  getPerfil(): PerfilSocio | null {
    return this.perfilSubject.value;
  }

  getCurrentUser(): PerfilSocio | null {
    return this.getPerfil();
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
