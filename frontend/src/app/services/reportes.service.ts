import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface KpisT01 {
  expedientes_generados: number;
  socios_alcanzados: number;
  puntos_aprobados_positivos: number;
  puntos_aprobados_negativos: number;
  tiempo_vida_promedio_dias: number;
}

export interface ClasificacionItem {
  clasificacion: string;
  label: string;
  cantidad: number;
}

export interface GrupoItem {
  grupo: string;
  porcentaje: number;
  cantidad: number;
}

export interface PuntoItem {
  puntaje: number;
  cantidad: number;
}

export interface MetricasT01DTO {
  kpis: KpisT01;
  expedientes_por_clasificacion: ClasificacionItem[];
  distribucion_por_grupo: GrupoItem[];
  distribucion_puntos: PuntoItem[];
}

export interface KpisReuniones {
  expedientes_generados: number;
  socios_alcanzados: number;
  puntos_por_inasistencias: number;
}

export interface CategoriaReunionItem {
  categoria: string;
  cantidad: number;
}

export interface ProporcionAprobacionItem {
  tipo: string;
  porcentaje: number;
  cantidad: number;
}

export interface SociosPorGrupoItem {
  grupo: string;
  cantidad: number;
}

export interface MetricasReunionesDTO {
  kpis: KpisReuniones;
  expedientes_por_categoria: CategoriaReunionItem[];
  proporcion_aprobacion: ProporcionAprobacionItem[];
  socios_por_grupo: SociosPorGrupoItem[];
}

export interface SubcomisionItemDTO {
  id: number;
  nombre: string;
}

export interface IntraVsInterItem {
  tipo: string;
  cantidad: number;
  porcentaje: number;
  color: string;
}

export interface ParticipacionSubcomisionItem {
  subcomision: string;
  porcentaje: number;
  color: string;
}

export interface SocioSubcomisionRow {
  posicion: number;
  legajo: string;
  apellido: string;
  nombre: string;
  grupo: string;
  puntos_asignados_ciclo: number;
  puntos_totales: number;
}

export interface MetricasSubcomisionDTO {
  subcomision: {
    id: number;
    nombre: string;
    color_hex: string;
  };
  kpis: {
    puntaje_ciclo_t01: number;
    total_socios: number;
  };
  distribucion_puntos: PuntoItem[];
  intra_vs_inter: IntraVsInterItem[];
  participacion_otras_subcomisiones: ParticipacionSubcomisionItem[];
  tabla_socios: SocioSubcomisionRow[];
}

export interface RecordAbsoluto {
  socio_numero: number;
  nombre_completo: string;
  legajo: string;
  subcomision: string;
  grupo: string;
  puntaje_maximo: number;
  periodo: string;
  distincion: string;
}

export interface TopHistoricoItem {
  posicion: number;
  socio_numero: number;
  nombre_completo: string;
  subcomision: string;
  puntaje_historico: number;
  record_destacado: boolean;
}

export interface SerieAnualItem {
  anio: number;
  cantidad: number;
}

export interface HistoricoRecordsDTO {
  record_absoluto: RecordAbsoluto;
  top_historico: TopHistoricoItem[];
  kpis: {
    total_expedientes_historicos: number;
    anios_registrados: string;
  };
  serie_anual: SerieAnualItem[];
  distribucion_historica_puntos: PuntoItem[];
}

@Injectable({
  providedIn: 'root'
})
export class ReportesService {
  private readonly baseUrl = `${environment.apiUrl}/expedientes/reportes`;

  constructor(private http: HttpClient) {}

  getMetricasT01(subcomisionId?: number): Observable<MetricasT01DTO> {
    let params = new HttpParams();
    if (subcomisionId) {
      params = params.set('subcomision_id', subcomisionId.toString());
    }
    return this.http.get<MetricasT01DTO>(`${this.baseUrl}/t01/`, { params });
  }

  getMetricasReuniones(subcomisionId?: number): Observable<MetricasReunionesDTO> {
    let params = new HttpParams();
    if (subcomisionId) {
      params = params.set('subcomision_id', subcomisionId.toString());
    }
    return this.http.get<MetricasReunionesDTO>(`${this.baseUrl}/reuniones/`, { params });
  }

  getSubcomisiones(): Observable<SubcomisionItemDTO[]> {
    return this.http.get<SubcomisionItemDTO[]>(`${this.baseUrl}/subcomisiones/`);
  }

  getMetricasSubcomision(subcomisionId?: number): Observable<MetricasSubcomisionDTO> {
    let params = new HttpParams();
    if (subcomisionId) {
      params = params.set('subcomision_id', subcomisionId.toString());
    }
    return this.http.get<MetricasSubcomisionDTO>(`${this.baseUrl}/subcomision/`, { params });
  }

  getHistoricoYRecords(): Observable<HistoricoRecordsDTO> {
    return this.http.get<HistoricoRecordsDTO>(`${this.baseUrl}/historico-records/`);
  }

  actualizarClasificacion(expedienteId: number, clasificacion: string): Observable<any> {
    return this.http.patch<any>(`${environment.apiUrl}/expedientes/${expedienteId}/clasificacion/`, {
      clasificacion
    });
  }
}
