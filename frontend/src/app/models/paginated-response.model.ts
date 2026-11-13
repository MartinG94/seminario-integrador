/**
 * Interfaz genérica canónica para respuestas paginadas de la API REST (DRF).
 * Define el contrato estándar de 7 campos según el requerimiento EARS-U01
 * de la especificación 010 (SCRUM-87 / SCRUM-118).
 */
export interface PaginatedResponse<T> {
  count: number;
  total_pages: number;
  current_page: number;
  page_size: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Parámetros estándar para peticiones paginadas a la API REST.
 */
export interface PaginationParams {
  page?: number;
  page_size?: number;
  ordering?: string;
  search?: string;
  estado?: string;
  urgencia?: string;
  concepto?: string;
  socio?: string;
  socio_legajo?: string;
  fecha_desde?: string;
  fecha_hasta?: string;
}

/**
 * Parámetros específicos para la consulta paginada del ranking de socios.
 */
export interface RankingPaginationParams extends PaginationParams {
  categoria?: 'ACTIVO' | 'PASIVO' | '';
  subcomision?: string;
  grupo?: string;
  reconciliado?: boolean;
  solo_alertas?: boolean;
  all?: boolean;
}

