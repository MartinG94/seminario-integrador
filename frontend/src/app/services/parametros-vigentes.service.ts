import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, map, shareReplay, tap } from 'rxjs/operators';

import { environment } from '../../environments/environment';
import { UMBRALES_INICIALES, UmbralesVigentes } from '../ranking-socios/ranking-thresholds';

export interface UmbralesDTO {
  umbral_critico: string;
  umbral_preventivo: string;
  umbral_preventivo_activo: boolean;
}

export interface PlazosDTO {
  plazo_descargo_dias_habiles: number;
  plazo_apelacion_dias_habiles: number;
}

export const PLAZO_DESCARGO_INICIAL = 5;

function aNumero(valor: string, respaldo: number): number {
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : respaldo;
}

/**
 * Lectura de los parámetros vigentes para cualquier usuario autenticado (Spec 011).
 * Cada consulta se resuelve una vez por sesión; ante un error rigen los valores iniciales.
 */
@Injectable({ providedIn: 'root' })
export class ParametrosVigentesService {
  private readonly baseUrl = `${environment.apiUrl}/parametros`;
  private readonly umbralesSubject = new BehaviorSubject<UmbralesVigentes>({ ...UMBRALES_INICIALES });
  private umbralesRequest$: Observable<UmbralesVigentes> | null = null;
  private plazosRequest$: Observable<number> | null = null;

  constructor(private http: HttpClient) {}

  /** Último valor conocido de los umbrales (los iniciales hasta recibir la respuesta). */
  get umbralesActuales(): UmbralesVigentes {
    return this.umbralesSubject.value;
  }

  umbrales(): Observable<UmbralesVigentes> {
    if (!this.umbralesRequest$) {
      this.umbralesRequest$ = this.http.get<UmbralesDTO>(`${this.baseUrl}/umbrales/`).pipe(
        map(dto => ({
          critico: aNumero(dto.umbral_critico, UMBRALES_INICIALES.critico),
          preventivo: aNumero(dto.umbral_preventivo, UMBRALES_INICIALES.preventivo),
          preventivoActivo: dto.umbral_preventivo_activo === true
        })),
        tap(umbrales => this.umbralesSubject.next(umbrales)),
        catchError(() => {
          this.umbralesRequest$ = null;
          return of({ ...UMBRALES_INICIALES });
        }),
        shareReplay({ bufferSize: 1, refCount: true })
      );
    }
    return this.umbralesRequest$;
  }

  plazoDescargoDiasHabiles(): Observable<number> {
    if (!this.plazosRequest$) {
      this.plazosRequest$ = this.http.get<PlazosDTO>(`${this.baseUrl}/plazos/`).pipe(
        map(dto => dto.plazo_descargo_dias_habiles || PLAZO_DESCARGO_INICIAL),
        catchError(() => {
          this.plazosRequest$ = null;
          return of(PLAZO_DESCARGO_INICIAL);
        }),
        shareReplay({ bufferSize: 1, refCount: true })
      );
    }
    return this.plazosRequest$;
  }

  /** Descarta lo leído (p. ej. tras guardar un cambio desde el panel de administración). */
  invalidar(): void {
    this.umbralesRequest$ = null;
    this.plazosRequest$ = null;
  }
}
