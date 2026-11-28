# Plan de Cobertura — Inventario de Documentación SGD-AVEIT

> **Fecha:** 2026-11-27  
> **Criterio de descubrimiento:** Archivos de documentación versionados (`git ls-files`) con extensión `.md`, `.txt`, `.docx`, `.pdf` o notas/archivos `notasPO`, excluyendo `auditoria/`, `.git`, dependencias (`backend/requirements.txt`), artefactos de build y archivos legales/no-doc (`LICENSE`, `NOTICE`).  
> **Total de grupos:** 12  
> **Total de archivos:** 113  
> **Regla de partición:** Ningún grupo supera 25 archivos; cada archivo pertenece exactamente a un grupo.

---

## 1. `raiz` (5 archivos)
- `AGENTS.md`
- `DESIGN.md`
- `PLAN_SPRINT_5_CONSOLIDADO.md`
- `README.md`
- `TASK.md`

## 2. `repo-auxiliar` (6 archivos)
- `.github/ISSUE_TEMPLATE/reporte_incidencia.md`
- `.github/ISSUE_TEMPLATE/tarea_sprint.md`
- `backend/README.md`
- `frontend/CHANGELOG.md`
- `frontend/LICENSE.md`
- `frontend/README.md`

## 3. `docs-otros` (6 archivos)
- `docs/constitution.md`
- `docs/adr/ADR-001-consumo-padron-institucional.md`
- `docs/adr/README.md`
- `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md`
- `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md`
- `docs/design/ranking-socios/README.md`

## 4. `docs-analisis-proceso-actual` (9 archivos)
- `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md`
- `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md`
- `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md`
- `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Estatuto_AVEIT_Reforma_2026.pdf`
- `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2018).pdf`
- `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2026).pdf`
- `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Reglamento_Interno_Disciplina_AVEIT_2026.pdf`
- `docs/analisis-proceso-actual/sistema-actual/Rifas - Actas - Entrega - Desde cero.pdf`
- `docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md`

## 5. `docs-especificaciones` (7 archivos)
- `docs/especificaciones/ERS-SGD-AVEIT.md`
- `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md`
- `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md`
- `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md`
- `docs/especificaciones/PLANTILLA_CASO_DE_USO.md`
- `docs/especificaciones/RBAC-SGD-AVEIT.md`
- `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md`

## 6. `docs-formales` (5 archivos)
- `docs/formales/Estudio_Inicial.docx`
- `docs/formales/Estudio_Inicial.pdf`
- `docs/formales/Plan_de_Proyecto.docx`
- `docs/formales/Plan_de_Proyecto.pdf`
- `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`

## 7. `docs-gestion-proyecto` (12 archivos)
- `docs/gestion-proyecto/ANALISIS_INTEGRAL_BACKLOG_JIRA.md`
- `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md`
- `docs/gestion-proyecto/GUIA_PULL_REQUESTS.md`
- `docs/gestion-proyecto/INFORME_DIVERGENCIA_MAIN_PRESENTACION.md`
- `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md`
- `docs/gestion-proyecto/Seguimiento de Proyecto.md`
- `docs/gestion-proyecto/UAT-PR49-calendario.md`
- `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`
- `docs/gestion-proyecto/notasPO.md`
- `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md`
- `docs/gestion-proyecto/relevamiento_scrum_119_frontend_onpush_trackby.md`
- `docs/gestion-proyecto/relevamiento_scrum_120_optimizacion_orm.md`

## 8. `docs-implementacion-ia` (6 archivos)
- `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md`
- `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md`
- `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md`
- `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md`
- `docs/Implementacion IA/presentacion/02_propuesta_tribunal_disciplina.md`
- `docs/Implementacion IA/presentacion/03_propuesta_comision_directiva.md`

## 9. `docs-manual-usuario` (11 archivos)
- `docs/manual-usuario/README.md`
- `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf`
- `docs/manual-usuario/pdfs/02_Mis_Expedientes_y_Descargos.pdf`
- `docs/manual-usuario/pdfs/03_Reglamentos.pdf`
- `docs/manual-usuario/pdfs/04_Ranking_de_Socios.pdf`
- `docs/manual-usuario/pdfs/05_Calendario_Institucional.pdf`
- `docs/manual-usuario/pdfs/06_Crear_Expediente.pdf`
- `docs/manual-usuario/pdfs/07_Gestionar_Expedientes_TD.pdf`
- `docs/manual-usuario/pdfs/08_Eventos_y_Asistencia.pdf`
- `docs/manual-usuario/pdfs/09_Reportes_y_Administracion.pdf`
- `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`

## 10. `specs-001-a-005` (20 archivos)
- `specs/001-walking-skeleton/plan.md`
- `specs/001-walking-skeleton/spec.md`
- `specs/001-walking-skeleton/tasks.md`
- `specs/002-expediente-trazabilidad/plan.md`
- `specs/002-expediente-trazabilidad/spec.md`
- `specs/002-expediente-trazabilidad/tasks.md`
- `specs/003-monitorear-solicitudes-t01/spec.md`
- `specs/003-monitorear-solicitudes-t01/tasks.md`
- `specs/004-calendario-dias-habiles/plan.md`
- `specs/004-calendario-dias-habiles/spec.md`
- `specs/004-calendario-dias-habiles/tasks.md`
- `specs/004-clasificador-urgencia/plan.md`
- `specs/004-clasificador-urgencia/spec.md`
- `specs/004-clasificador-urgencia/tasks.md`
- `specs/005-evidencia-protegida/plan.md`
- `specs/005-evidencia-protegida/spec.md`
- `specs/005-evidencia-protegida/tasks.md`
- `specs/005-sanciones-reuniones-solicitudes/plan.md`
- `specs/005-sanciones-reuniones-solicitudes/spec.md`
- `specs/005-sanciones-reuniones-solicitudes/tasks.md`

## 11. `specs-006-a-009` (13 archivos)
- `specs/006-resolver-causal-t02/plan.md`
- `specs/006-resolver-causal-t02/spec.md`
- `specs/006-resolver-causal-t02/tasks.md`
- `specs/007-apartamiento-suplencia/plan.md`
- `specs/007-apartamiento-suplencia/spec.md`
- `specs/007-apartamiento-suplencia/tasks.md`
- `specs/007-visor-expediente-evidencia/plan.md`
- `specs/007-visor-expediente-evidencia/spec.md`
- `specs/007-visor-expediente-evidencia/tasks.md`
- `specs/008-apelacion-adecuacion-t01/plan.md`
- `specs/008-apelacion-adecuacion-t01/spec.md`
- `specs/008-apelacion-adecuacion-t01/tasks.md`
- `specs/009-reportes-e-informes/tasks.md`

## 12. `specs-010-a-012` (13 archivos)
- `specs/010-circuito-resolutivo-enmiendas/plan.md`
- `specs/010-circuito-resolutivo-enmiendas/spec.md`
- `specs/010-circuito-resolutivo-enmiendas/tasks.md`
- `specs/010-optimizacion-rendimiento/memory_audit_report.md`
- `specs/010-optimizacion-rendimiento/plan.md`
- `specs/010-optimizacion-rendimiento/spec.md`
- `specs/010-optimizacion-rendimiento/tasks.md`
- `specs/011-libro-mayor-mis-expedientes-publicacion/plan.md`
- `specs/011-libro-mayor-mis-expedientes-publicacion/spec.md`
- `specs/011-libro-mayor-mis-expedientes-publicacion/tasks.md`
- `specs/012-panel-administracion/plan.md`
- `specs/012-panel-administracion/spec.md`
- `specs/012-panel-administracion/tasks.md`
