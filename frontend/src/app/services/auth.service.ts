import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, Subscription } from 'rxjs';
import { tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';

export type RolRbac = 'SOCIO' | 'FISCALIZADORA' | 'CD' | 'TD' | 'ADMIN';
export type MembershipCategory = 'JUNIOR' | 'SENIOR' | 'EX_TRAVELER';

export interface PerfilSocio {
  legajo: string;
  first_name: string;
  last_name: string;
  email: string;
  role: RolRbac;
  // Sólo el estado de la vista admite null mientras se confirma el perfil.
  category: MembershipCategory | null;
  category_display: string;
  subcomision: string | null;
}

export interface ConfirmedSocioProfile extends PerfilSocio {
  category: MembershipCategory;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: ConfirmedSocioProfile;
}

const ACCESS_TOKEN_KEY = 'aveit.access';
const REFRESH_TOKEN_KEY = 'aveit.refresh';
const PROFILE_KEY = 'aveit.perfil';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isCachedProfile(value: unknown): value is Omit<PerfilSocio, 'category' | 'category_display'> {
  if (!isRecord(value)) {
    return false;
  }
  const profile = value;
  const roles: readonly RolRbac[] = ['SOCIO', 'FISCALIZADORA', 'CD', 'TD', 'ADMIN'];
  return ['legajo', 'first_name', 'last_name', 'email'].every(field => typeof profile[field] === 'string')
    && roles.some(role => role === profile.role)
    && (profile.subcomision === null || typeof profile.subcomision === 'string');
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private perfilSubject = new BehaviorSubject<PerfilSocio | null>(this.leerPerfil());
  private profileHydration: Subscription | null = null;
  private sessionGeneration = 0;
  perfil$ = this.perfilSubject.asObservable();

  constructor(private http: HttpClient) {
    const token = this.getToken();
    const generation = this.sessionGeneration;
    if (token) {
      // El interceptor depende de este servicio: la petición empieza cuando
      // su construcción ya terminó y conserva el manejo HTTP vigente.
      Promise.resolve().then(() => {
        if (generation !== this.sessionGeneration || token !== this.getToken()) {
          return;
        }
        this.profileHydration = this.http
          .get<ConfirmedSocioProfile>(`${environment.apiUrl}/auth/me/`)
          .subscribe({
            next: profile => {
              if (generation === this.sessionGeneration && token === this.getToken()) {
                this.persistProfile(profile);
              }
            },
            // El interceptor resuelve 401. Red y otros errores no confirman
            // categoría ni cambian la sesión o el rol cacheado.
            error: () => {}
          });
      });
    }
  }

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
    this.cancelProfileHydration();
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
    this.cancelProfileHydration();
    localStorage.setItem(ACCESS_TOKEN_KEY, respuesta.access);
    localStorage.setItem(REFRESH_TOKEN_KEY, respuesta.refresh);
    this.persistProfile(respuesta.user);
  }

  private cancelProfileHydration(): void {
    this.sessionGeneration += 1;
    this.profileHydration?.unsubscribe();
    this.profileHydration = null;
  }

  private persistProfile(profile: ConfirmedSocioProfile): void {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
    this.perfilSubject.next(profile);
  }

  private leerPerfil(): PerfilSocio | null {
    if (!this.getToken()) {
      return null;
    }
    const crudo = localStorage.getItem(PROFILE_KEY);
    if (!crudo) {
      return null;
    }
    try {
      const cached: unknown = JSON.parse(crudo);
      return isCachedProfile(cached)
        ? { ...cached, category: null, category_display: '' }
        : null;
    } catch {
      return null;
    }
  }
}
