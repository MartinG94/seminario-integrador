import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface HolidayDto {
  id: number;
  fecha: string;
  descripcion: string;
  creado_por: number | null;
  creado_por_nombre: string;
  created_at: string;
}

export interface CreateHolidayRequest {
  fecha: string;
  descripcion: string;
}

export interface CalcularPlazoRequest {
  start_at: string;
  business_days: number;
}

export interface DiaExcluido {
  date: string;
  reason: string;
}

export interface DiaHabilComputado {
  day_number: number;
  date: string;
  weekday: string;
}

export interface CalcularPlazoResponse {
  start_at: string;
  business_days: number;
  deadline: string;
  dias_habiles_computados: DiaHabilComputado[];
  dias_excluidos: DiaExcluido[];
}

@Injectable({ providedIn: 'root' })
export class CalendarioApiService {
  private readonly baseUrl = `${environment.apiUrl}/expedientes/calendario`;

  constructor(private http: HttpClient) {}

  getFeriados(year?: number, month?: number, ordering?: 'fecha' | '-fecha'): Observable<HolidayDto[]> {
    let params = new HttpParams();
    if (year != null) { params = params.set('year', year.toString()); }
    if (month != null) { params = params.set('month', month.toString()); }
    if (ordering != null) { params = params.set('ordering', ordering); }
    return this.http.get<HolidayDto[]>(`${this.baseUrl}/feriados/`, { params });
  }

  addFeriado(payload: CreateHolidayRequest): Observable<HolidayDto> {
    return this.http.post<HolidayDto>(`${this.baseUrl}/feriados/`, payload);
  }

  calcularPlazo(payload: CalcularPlazoRequest): Observable<CalcularPlazoResponse> {
    return this.http.post<CalcularPlazoResponse>(`${this.baseUrl}/calcular-plazo/`, payload);
  }
}
