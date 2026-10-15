/**
 * Tipos y modelos para Gestión de Eventos Institucionales,
 * Marcación de Asistencia y Apercibimientos Reglamentarios (Spec 005 / SCRUM-50 / S3-06).
 */

export type CategoriaEvento = 'REUNION' | 'ACTIVIDAD';

export type SubtipoReunion =
  | 'ORDINARIA'
  | 'EXTRAORDINARIA'
  | 'ASAMBLEA'
  | 'PLENARIO';

export type SubtipoActividad =
  | 'MANTENIMIENTO'
  | 'VOLUNTARIADO'
  | 'JORNADA'
  | 'EVENTO_SOCIAL'
  | 'GUARDIA';

export type SubtipoEvento = SubtipoReunion | SubtipoActividad;

export type ModalidadEvento =
  | 'PRESENCIAL_SEDE'
  | 'PRESENCIAL_EXTERNA'
  | 'VIRTUAL';

export type ModoConvocatoria =
  | 'GRUPO'
  | 'SUBCOMISION'
  | 'ESTADO_SOCIAL'
  | 'PERSONALIZADA';

export type EstadoSocialConvocado = 'JUNIORS' | 'SENIORS';

export type EstadoEvento =
  | 'CREADO'
  | 'NOTIFICADO'
  | 'EN_CURSO'
  | 'ABIERTO'
  | 'FINALIZADO'
  | 'ANULADO'
  | 'PROGRAMADA'
  | 'CERRADA'
  | 'CANCELADA';

export type EstadoAsistenciaEvento =
  | 'PRESENTE'
  | 'AUSENTE_INJUSTIFICADO'
  | 'TARDANZA_LEVE'
  | 'TARDANZA_GRAVE'
  | 'RETIRO_ANTICIPADO'
  | 'JUSTIFICADO';

export type MetodoCapturaAsistencia = 'MANUAL' | 'BIOMETRICO';

export type EstadoRegistroApercibimiento =
  | 'PENDIENTE'
  | 'CONSOLIDADO'
  | 'ANULADO';

export interface ConvocadoAsistenciaDTO {
  socio_id: number;
  socio_nombre: string;
  socio_legajo: string;
  socio_email?: string;
  socio_subcomision?: string;
  estado_asistencia: EstadoAsistenciaEvento;
  motivo: string;
  minutos_tardanza: number;
  minutos_retiro_anticipado: number;
  metodo_captura: MetodoCapturaAsistencia;
  hora_registro?: string | null;
  hora_salida?: string | null;
  observaciones?: string;
  procesado_disciplinario?: boolean;
  expediente_generado_id?: number | null;
  apercibimiento_generado_id?: number | null;
}

export interface AsistenciaEvento {
  id?: number | string;
  evento?: number | string;
  socio_id: number;
  socio_nombre?: string;
  socio_legajo?: string;
  socio_email?: string;
  socio_subcomision?: string;
  estado_asistencia: EstadoAsistenciaEvento;
  hora_registro?: string | null;
  hora_salida?: string | null;
  minutos_tardanza?: number;
  minutos_retiro_anticipado?: number;
  metodo_captura?: MetodoCapturaAsistencia;
  dispositivo_id?: string | null;
  motivo: string;
  observaciones?: string;
  procesado_disciplinario?: boolean;
  expediente_generado_id?: number | null;
  apercibimiento_generado_id?: number | null;
  created_at?: string;
}

export interface EventoInstitucional {
  id: number | string;
  titulo: string;
  descripcion?: string;
  categoria: CategoriaEvento;
  tipo: SubtipoEvento;
  modalidad: ModalidadEvento;
  ubicacion?: string | null;
  lugar?: string;
  fecha_publicacion?: string;
  fecha_programada: string; // inicio obligatoria
  fecha_fin?: string | null; // estrictamente opcional
  fecha_hora_cierre_efectivo?: string | null;
  fecha_reporte?: string | null;
  tolerancia_tardanza_minutos?: number;
  tolerancia_retiro_minutos?: number;
  estado: EstadoEvento;
  modo_convocatoria: ModoConvocatoria;
  grupo_convocado?: string | null;
  subcomision_id?: number | null;
  subcomision_nombre?: string | null;
  es_obligatoria?: boolean;
  es_sancionable?: boolean;
  motivo_no_sancionable?: string | null;
  detalle_tarea?: string | null;
  puntos_sancion?: number | string | null;
  motivo_cancelacion?: string | null;
  estado_social_convocado?: EstadoSocialConvocado | string | null;
  convocante_id?: number | null;
  convocante_nombre?: string | null;
  reportado_por_id?: number | null;
  asistencias?: AsistenciaEvento[];
  total_convocados?: number;
  total_presentes?: number;
  total_ausentes?: number;
  created_at?: string;
  updated_at?: string;
}

export interface RegistroApercibimiento {
  id: number;
  socio_id: number;
  socio_nombre?: string;
  socio_legajo?: string;
  origen_tipo: string;
  asistencia_id?: number | null;
  expediente_origen_id?: number | null;
  solicitud_t01_id?: string | null;
  fecha_hecho: string;
  motivo: string;
  articulo_reglamento: string;
  estado: EstadoRegistroApercibimiento;
  lote_consolidacion?: string | null;
  expediente_sancion_id?: number | null;
  fecha_consolidacion?: string | null;
  actor_registro: string;
  created_at: string;
}

export interface CrearEventoPayload {
  titulo: string;
  descripcion?: string;
  categoria: CategoriaEvento;
  tipo: SubtipoEvento;
  modalidad: ModalidadEvento;
  ubicacion?: string;
  lugar?: string;
  fecha_programada: string;
  fecha_fin?: string | null;
  modo_convocatoria: ModoConvocatoria;
  grupo_convocado?: string;
  subcomision_id?: number | null;
  estado_social_convocado?: EstadoSocialConvocado | string;
  detalle_tarea?: string;
  puntos_sancion?: number;
  notificar?: boolean;
  socios_ids?: number[];
  tolerancia_tardanza_minutos?: number;
  tolerancia_retiro_minutos?: number;
}

export interface ReportarAsistenciaItemPayload {
  socio_id: number;
  estado_asistencia: EstadoAsistenciaEvento;
  motivo: string;
  minutos_tardanza?: number;
  minutos_retiro_anticipado?: number;
  metodo_captura?: MetodoCapturaAsistencia;
  hora_registro?: string | null;
}

export interface ReportarAsistenciaPayload {
  estrategia?: MetodoCapturaAsistencia;
  asistencias: ReportarAsistenciaItemPayload[];
  cerrar_evento?: boolean;
}

export interface ReportarAsistenciaResultadoDetalle {
  socio_id: number;
  socio_nombre?: string;
  socio_legajo?: string;
  estado_asistencia: EstadoAsistenciaEvento;
  motivo?: string;
  resultado: 'OK' | 'APERCIBIMIENTO_CREADO' | 'EXPEDIENTE_CREADO' | 'APERCIBIMIENTO_CONSOLIDADO' | 'SIN_SANCION';
  expediente_id?: number | null;
  numero_expediente?: string | null;
  apercibimiento_id?: number | null;
  puntos_sancion?: number;
  descripcion?: string;
}

export interface ReportarAsistenciaResponse {
  mensaje?: string;
  evento_id: number | string;
  estado_evento: EstadoEvento;
  es_sancionable?: boolean;
  motivo_no_sancionable?: string | null;
  asistencias_procesadas: number;
  expedientes_generados: number;
  apercibimientos_generados: number;
  apercibimientos_consolidados?: number;
  detalles?: ReportarAsistenciaResultadoDetalle[];
}

export interface EventoFiltros {
  categoria?: CategoriaEvento;
  tipo?: SubtipoEvento;
  estado?: EstadoEvento;
  modo_convocatoria?: ModoConvocatoria;
  mis_eventos?: boolean;
  search?: string;
  page?: number;
}
