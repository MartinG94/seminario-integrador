# Evaluación Unificada de Documentación — SGD-AVEIT

> **Fecha:** 27/11/2026  
> **Fuentes consolidadas:** Los 12 inventarios en `auditoria/inventarios/*.md` (`113` documentos versionados) contrastados contra `auditoria/registro-canonico.md`.  
> **Modo:** Solo lectura (no se mueve ni elimina ningún archivo hasta aprobación).  
> **Destinos posibles:** `conservar y completar` · `conservar y recortar` · `archivar en auditoria/archivados/` · `eliminar después de un sprint sin reclamos`.

---

## 1. Resumen Cuantitativo por Destino Propuesto

| Destino propuesto | Cantidad | Alcance resumido |
|---|---:|---|
| `conservar y completar` | 53 | Documentos rectores, entregables formales maestros, manual consolidado, ADRs, normas oficiales AVEIT y `spec.md`/`plan.md` vigentes a sincronizar (incluyendo `001` y `003`). |
| `conservar y recortar` | 5 | Documentos útiles que contienen secciones obsoletas o instrucciones peligrosas/erróneas a depurar (`notasPO.md`, `GUIA_PULL_REQUESTS.md`, guías de config, legado). |
| `archivar en auditoria/archivados/` | 35 | Copias redundantes descartadas, documentos I+D no implementados (`SCRUM-76`), `tasks.md` cerrados y bitácoras de gestión históricas. |
| `eliminar después de un sprint sin reclamos` | 20 | Residuos puros de plantilla Creative Tim, reportes efímeros de PR/ramas, plantillas vacías, PDFs derivados de `src/*.html` y relevamientos previos ya absorbidos por `specs/010`. |
| **Total** | **113** | **100% de los documentos inventariados** |

---

## 2. Resolución de Duplicados y Redundancias

| Conjunto redundante | Documento que queda | Documentos que se archivan / retiran | Motivo |
|---|---|---|---|
| **Estudio Inicial** (`docs/formales/Estudio_Inicial.docx`, `docs/formales/Estudio_Inicial.pdf`, `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md`) | `docs/formales/Estudio_Inicial.docx` *(conservar y completar)* | `docs/formales/Estudio_Inicial.pdf` *(archivar en auditoria/archivados/)*<br>`docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md` *(archivar en auditoria/archivados/)* | Mantiene una sola fuente editable formal (sincronizada con la `v1.5.0` humana y cerrando observaciones docentes #1–#5, #23, #31 en nueva versión fechada); el `.pdf` es una exportación duplicada `v1.0.1` y el `.md` es un borrador desincronizado. |
| **Plan de Proyecto** (`docs/formales/Plan_de_Proyecto.docx`, `docs/formales/Plan_de_Proyecto.pdf`, `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md`) | `docs/formales/Plan_de_Proyecto.docx` *(conservar y completar)* | `docs/formales/Plan_de_Proyecto.pdf` *(archivar en auditoria/archivados/)*<br>`docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md` *(archivar en auditoria/archivados/)* | Queda el `.docx` como única fuente editable formal (limpiando restos `v1.0.1`, etiquetas de IA, `RF-09` votación nominal y completando RBAC/CU/módulos en nueva versión); el `.pdf` quedó congelado en `v1.0.1` y el `.md` diverge en historial/grupo. |
| **Definición de Producto** (`docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` vs entregas externas S4) | *(A consolidar en entregable formal de Definición del Producto actualizado)* | `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` *(archivar en auditoria/archivados/)* | El recorte de Sprint 3 quedó superado por `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` y por los avances de Sprint 5. |
| **ERS** (`docs/especificaciones/ERS-SGD-AVEIT.md` vs `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md`) | `docs/especificaciones/ERS-SGD-AVEIT.md` *(conservar y completar)* | `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` *(archivar en auditoria/archivados/)* | `ERS-SGD-AVEIT.md` tiene el catálogo completo `RF-01..RF-19` y está referenciado en `Seguimiento de Proyecto.md` y `TASK.md`; la segunda ERS arrastra 5 estados, contradicciones internas y enlaces rotos `G:\My Drive`. |
| **UAT `SCRUM-50`** (`docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` vs `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`) | *(Ninguno activo; cubierto por tests `test_qa_e2e_eventos_sanciones.py`)* | `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` *(archivar en auditoria/archivados/)*<br>`docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` *(eliminar después de un sprint sin reclamos)* | Es el mismo reporte QA puntual de rama duplicado en dos carpetas; nunca debió alojarse en `docs/formales/`. Se deja una copia en archivo histórico y se retira la copia duplicada. |
| **Manual de Usuario PDFs** (`01_...pdf`..`09_...pdf` vs `Manual_Usuario_SGD_AVEIT_Completo.pdf`) | `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf` *(conservar y completar)* | `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf` .. `09_Reportes_y_Administracion.pdf` *(eliminar después de un sprint sin reclamos)* | El consolidado es la concatenación exacta con 0 diferencias de los 9 PDFs individuales y todos se regeneran desde `src/*.html` con `render_pdfs.py` + `merge_pdfs.py`. |
| **Propuestas IA `SCRUM-76`** (`01`–`03` técnicos vs `presentacion/01`–`03` memorandos) | *(Ninguno activo en producto; todo `SCRUM-76` es I+D no implementado)* | Los 6 archivos de `docs/Implementacion IA/` *(archivar en auditoria/archivados/)* | Los 3 memorandos de `presentacion/` duplican el contenido técnico de `01`–`03` con contradicciones entre sí y menciones a votación nominal; al no haber código de IA implementado, todo el bloque pasa a archivo histórico I+D. |
| **Plantillas de Issues** (`.github/ISSUE_TEMPLATE/tarea_sprint.md` vs `AGENTS.md` / Jira) | `AGENTS.md` *(conservar y completar)* | `.github/ISSUE_TEMPLATE/tarea_sprint.md` *(archivar en auditoria/archivados/)* | `tarea_sprint.md` duplica convenciones de `AGENTS.md` quedando desactualizado en Python 3.11 y prefijo `[US-XX]`. |
| **Gestión de TD Ad-Hoc** (`docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` vs Panel Admin `/admin/parametros`) | Panel Admin `SCRUM-91` (`/admin/parametros`) + documento recortado para legado | Recorte dentro de `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` *(conservar y recortar)* | La gestión de `socios_socio` ahora se realiza desde `/admin/parametros` con auditoría; solo subsiste como útil la nota sobre `socio_lista.idTipoSocio` en la BD legada. |
| **Rediseño Eventos** (`docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md` vs `specs/005-sanciones-reuniones-solicitudes/spec.md`) | `specs/005-sanciones-reuniones-solicitudes/spec.md` *(conservar y completar)* | `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md` *(archivar en auditoria/archivados/)* | Cumplió su ciclo de especificación puntual previa; la spec `005-sanciones-reuniones-solicitudes` concentra la especificación EARS y RBAC del módulo. |
| **Optimización de Rendimiento `SCRUM-87`** (`relevamiento_scrum_118..120.md` vs `specs/010-optimizacion-rendimiento/`) | `specs/010-optimizacion-rendimiento/spec.md` y `plan.md` *(conservar y completar)* | `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md`, `119_frontend_onpush_trackby.md`, `120_optimizacion_orm.md` *(eliminar después de un sprint sin reclamos)* | Los 3 relevamientos previos a la ejecución quedaron absorbidos por `specs/010-optimizacion-rendimiento/` y los tests implementados. |
| **Plan Sprint 5** (`PLAN_SPRINT_5_CONSOLIDADO.md` vs `TASK.md` / `specs/010`–`012` / `traspaso-sprint6.md`) | `TASK.md` *(conservar y completar)* y `specs/010`–`012` | `PLAN_SPRINT_5_CONSOLIDADO.md` *(archivar en auditoria/archivados/)* | Documento previo de planificación (`05/11/2026`) desactualizado respecto de los modelos y rutas reales implementadas. |

---

## 3. Tabla Maestra Unificada (`113` archivos)

| # | Archivo | Quién lo lee | Qué pasa si desaparece | Clasificación | Destino propuesto |
|---:|---|---|---|---|---|
| 1 | `AGENTS.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 2 | `DESIGN.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 3 | `PLAN_SPRINT_5_CONSOLIDADO.md` | nadie | nada | 1. Residuo de fabricación / 3. Redundante con `TASK.md` y `specs/010`–`012` | `archivar en auditoria/archivados/` |
| 4 | `README.md` | equipo / cátedra | alguien pregunta | 3. Incompleto | `conservar y completar` |
| 5 | `TASK.md` | equipo | alguien se equivoca | 3. Incompleto / desactualizado | `conservar y completar` |
| 6 | `.github/ISSUE_TEMPLATE/reporte_incidencia.md` | equipo | nada | 4. Vigente | `conservar y completar` |
| 7 | `.github/ISSUE_TEMPLATE/tarea_sprint.md` | equipo | nada | 3. Redundante con `AGENTS.md` (desactualizado) | `archivar en auditoria/archivados/` |
| 8 | `backend/README.md` | equipo / cátedra | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 9 | `frontend/CHANGELOG.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 10 | `frontend/LICENSE.md` | nadie / auditoría legal | alguien se equivoca | 4. Vigente (2. Pocas líneas — aviso MIT obligatorio) | `conservar y completar` *(mantener sin cambios por licencia MIT)* |
| 11 | `frontend/README.md` | nadie / equipo | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 12 | `docs/constitution.md` | equipo | alguien se equivoca | 2. Pocas líneas / solapamiento con `AGENTS.md` | `conservar y completar` |
| 13 | `docs/adr/ADR-001-consumo-padron-institucional.md` | equipo / cátedra | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 14 | `docs/adr/README.md` | equipo / cátedra | alguien pregunta | 2. Pocas líneas / 3. Incompleto | `conservar y completar` |
| 15 | `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md` | equipo | alguien se equivoca | 3. Incompleto (Método 2 OAuth no implementado) | `conservar y recortar` |
| 16 | `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` | equipo / usuario final | alguien pregunta / se equivoca | 3. Redundante con `/admin/parametros` (`SCRUM-91`, desactualizado) | `conservar y recortar` |
| 17 | `docs/design/ranking-socios/README.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 18 | `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md` | equipo / cátedra | alguien pregunta | 3. Redundante con Plan de Proyecto / Def. Producto (desactualizado) | `archivar en auditoria/archivados/` |
| 19 | `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md` | equipo / cátedra | alguien pregunta | 3. Incompleto / desactualizado | `conservar y completar` |
| 20 | `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md` | cátedra / equipo | alguien pregunta | 3. Redundante con `docs/formales/Estudio_Inicial.docx` | `archivar en auditoria/archivados/` |
| 21 | `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Estatuto_AVEIT_Reforma_2026.pdf` | equipo / cátedra | alguien se equivoca | 4. Vigente | `conservar y completar` *(conservar sin cambios; fuente normativa oficial)* |
| 22 | `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2018).pdf` | equipo / cátedra | alguien pregunta | 4. Vigente | `conservar y completar` *(conservar sin cambios; fuente normativa histórica)* |
| 23 | `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2026).pdf` | equipo / cátedra | alguien se equivoca | 4. Vigente | `conservar y completar` *(conservar sin cambios; fuente normativa oficial)* |
| 24 | `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Reglamento_Interno_Disciplina_AVEIT_2026.pdf` | equipo / cátedra | alguien se equivoca | 4. Vigente | `conservar y completar` *(conservar sin cambios; fuente normativa oficial)* |
| 25 | `docs/analisis-proceso-actual/sistema-actual/Rifas - Actas - Entrega - Desde cero.pdf` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 26 | `docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md` | equipo | alguien se equivoca | 4. Vigente (contradicciones puntuales en encabezado y §7) | `conservar y recortar` |
| 27 | `docs/especificaciones/ERS-SGD-AVEIT.md` | equipo / cátedra | alguien pregunta | 3. Redundante con `ERS_Especificacion_Requerimientos_Tribunal.md` e incompleto | `conservar y completar` |
| 28 | `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` | equipo / nadie | alguien pregunta | 3. Redundante con `ERS-SGD-AVEIT.md` (desactualizado) | `archivar en auditoria/archivados/` |
| 29 | `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md` | cátedra / equipo | nada | 3. Incompleto | `archivar en auditoria/archivados/` |
| 30 | `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` | cátedra / equipo | alguien pregunta | 3. Incompleto | `conservar y completar` |
| 31 | `docs/especificaciones/PLANTILLA_CASO_DE_USO.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 32 | `docs/especificaciones/RBAC-SGD-AVEIT.md` | equipo | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 33 | `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md` | equipo | nada | 4. Vigente (cubierto por `specs/005-sanciones-reuniones-solicitudes/`) | `archivar en auditoria/archivados/` |
| 34 | `docs/formales/Estudio_Inicial.docx` | cátedra / equipo | alguien pregunta | 3. Redundante e incompleto (`v1.0.1` vs `v1.5.0` humana) | `conservar y completar` |
| 35 | `docs/formales/Estudio_Inicial.pdf` | cátedra / nadie | nada | 3. Redundante con `docs/formales/Estudio_Inicial.docx` | `archivar en auditoria/archivados/` |
| 36 | `docs/formales/Plan_de_Proyecto.docx` | cátedra / equipo | alguien pregunta | 3. Redundante e incompleto (`v2.0.0` con restos `v1.0.1`) | `conservar y completar` |
| 37 | `docs/formales/Plan_de_Proyecto.pdf` | nadie | nada | 3. Redundante con `docs/formales/Plan_de_Proyecto.docx` (congelado `v1.0.1`) | `archivar en auditoria/archivados/` |
| 38 | `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` | equipo | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 39 | `docs/gestion-proyecto/ANALISIS_INTEGRAL_BACKLOG_JIRA.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 40 | `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` | equipo / cátedra | nada | 3. Redundante con `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` e incompleto | `archivar en auditoria/archivados/` |
| 41 | `docs/gestion-proyecto/GUIA_PULL_REQUESTS.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y recortar` |
| 42 | `docs/gestion-proyecto/INFORME_DIVERGENCIA_MAIN_PRESENTACION.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 43 | `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md` | cátedra / equipo | alguien pregunta | 3. Redundante con `Plan_de_Proyecto.docx` (desactualizado) | `archivar en auditoria/archivados/` |
| 44 | `docs/gestion-proyecto/Seguimiento de Proyecto.md` | cátedra / equipo | alguien pregunta / se equivoca | 3. Redundante con `Seguimiento S4` externo e incompleto | `conservar y completar` |
| 45 | `docs/gestion-proyecto/UAT-PR49-calendario.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 46 | `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 47 | `docs/gestion-proyecto/notasPO.md` | equipo | alguien se equivoca / se rompe algo | 3. Incompleto / con contradicciones internas acumuladas | `conservar y recortar` *(solo con autorización explícita del PO)* |
| 48 | `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 49 | `docs/gestion-proyecto/relevamiento_scrum_119_frontend_onpush_trackby.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 50 | `docs/gestion-proyecto/relevamiento_scrum_120_optimizacion_orm.md` | nadie | nada | 1. Residuo de fabricación | `eliminar después de un sprint sin reclamos` |
| 51 | `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` | equipo | alguien pregunta | 4. Vigente (solo I+D `SCRUM-76` no implementado) | `archivar en auditoria/archivados/` |
| 52 | `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md` | equipo | alguien pregunta | 4. Vigente (solo I+D `SCRUM-76` no implementado) | `archivar en auditoria/archivados/` |
| 53 | `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md` | equipo | alguien pregunta | 4. Vigente (solo I+D `SCRUM-76` no implementado) | `archivar en auditoria/archivados/` |
| 54 | `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md` | equipo / nadie | alguien pregunta | 3. Redundante con `01` y `02` | `archivar en auditoria/archivados/` |
| 55 | `docs/Implementacion IA/presentacion/02_propuesta_tribunal_disciplina.md` | equipo / nadie | alguien pregunta | 3. Redundante con `01` y `03` (mantiene votación nominal) | `archivar en auditoria/archivados/` |
| 56 | `docs/Implementacion IA/presentacion/03_propuesta_comision_directiva.md` | equipo / nadie | alguien pregunta | 3. Redundante con `01` y `presentacion/01` | `archivar en auditoria/archivados/` |
| 57 | `docs/manual-usuario/README.md` | equipo | alguien se equivoca | 4. Vigente (rutas locales hardcodeadas) | `conservar y completar` |
| 58 | `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 59 | `docs/manual-usuario/pdfs/02_Mis_Expedientes_y_Descargos.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` e incompleto | `eliminar después de un sprint sin reclamos` |
| 60 | `docs/manual-usuario/pdfs/03_Reglamentos.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 61 | `docs/manual-usuario/pdfs/04_Ranking_de_Socios.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 62 | `docs/manual-usuario/pdfs/05_Calendario_Institucional.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 63 | `docs/manual-usuario/pdfs/06_Crear_Expediente.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 64 | `docs/manual-usuario/pdfs/07_Gestionar_Expedientes_TD.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` e incompleto | `eliminar después de un sprint sin reclamos` |
| 65 | `docs/manual-usuario/pdfs/08_Eventos_y_Asistencia.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` e incompleto | `eliminar después de un sprint sin reclamos` |
| 66 | `docs/manual-usuario/pdfs/09_Reportes_y_Administracion.pdf` | usuario final / cátedra | alguien pregunta | 3. Redundante con `Manual_Usuario_SGD_AVEIT_Completo.pdf` | `eliminar después de un sprint sin reclamos` |
| 67 | `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf` | usuario final / cátedra | alguien pregunta | 3. Incompleto (faltan secciones de guía de cátedra y capítulos desactualizados) | `conservar y completar` |
| 68 | `specs/001-walking-skeleton/plan.md` | equipo | nada | 3. Desactualizado / redundante con código y registro | `conservar y completar` |
| 69 | `specs/001-walking-skeleton/spec.md` | equipo | alguien pregunta | 3. Desactualizado / incompleto | `conservar y completar` |
| 70 | `specs/001-walking-skeleton/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 71 | `specs/002-expediente-trazabilidad/plan.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` *(mantener como snapshot vigente)* |
| 72 | `specs/002-expediente-trazabilidad/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` *(mantener como snapshot vigente)* |
| 73 | `specs/002-expediente-trazabilidad/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 74 | `specs/003-monitorear-solicitudes-t01/spec.md` | equipo | alguien pregunta | 3. Desactualizado / incompleto | `conservar y completar` |
| 75 | `specs/003-monitorear-solicitudes-t01/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 76 | `specs/004-calendario-dias-habiles/plan.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` *(mantener vigente)* |
| 77 | `specs/004-calendario-dias-habiles/spec.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` *(mantener vigente)* |
| 78 | `specs/004-calendario-dias-habiles/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 79 | `specs/004-clasificador-urgencia/plan.md` | equipo | alguien pregunta | 3. Desactualizado en referencias de rutas | `conservar y completar` |
| 80 | `specs/004-clasificador-urgencia/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 81 | `specs/004-clasificador-urgencia/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 82 | `specs/005-evidencia-protegida/plan.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` *(mantener vigente)* |
| 83 | `specs/005-evidencia-protegida/spec.md` | equipo | alguien pregunta | 3. Incompleto / desactualizado en DoD | `conservar y completar` |
| 84 | `specs/005-evidencia-protegida/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 85 | `specs/005-sanciones-reuniones-solicitudes/plan.md` | equipo | alguien se equivoca | 3. Desactualizado en rutas frontend y tests | `conservar y completar` |
| 86 | `specs/005-sanciones-reuniones-solicitudes/spec.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 87 | `specs/005-sanciones-reuniones-solicitudes/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 88 | `specs/006-resolver-causal-t02/plan.md` | equipo | alguien pregunta | 3. Incompleto | `conservar y completar` |
| 89 | `specs/006-resolver-causal-t02/spec.md` | equipo | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 90 | `specs/006-resolver-causal-t02/tasks.md` | equipo | nada | 4. Vigente (checklist histórico cerrado) | `archivar en auditoria/archivados/` |
| 91 | `specs/007-apartamiento-suplencia/plan.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 92 | `specs/007-apartamiento-suplencia/spec.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 93 | `specs/007-apartamiento-suplencia/tasks.md` | equipo | nada | 4. Vigente (checklist histórico cerrado) | `archivar en auditoria/archivados/` |
| 94 | `specs/007-visor-expediente-evidencia/plan.md` | equipo | alguien pregunta | 3. Incompleto | `conservar y completar` |
| 95 | `specs/007-visor-expediente-evidencia/spec.md` | equipo | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 96 | `specs/007-visor-expediente-evidencia/tasks.md` | equipo | nada | 2. Pocas líneas (checklist cerrado con migración rota) | `archivar en auditoria/archivados/` |
| 97 | `specs/008-apelacion-adecuacion-t01/plan.md` | equipo | alguien se equivoca | 4. Vigente | `conservar y completar` |
| 98 | `specs/008-apelacion-adecuacion-t01/spec.md` | equipo | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 99 | `specs/008-apelacion-adecuacion-t01/tasks.md` | equipo | nada | 3. Incompleto / desordenado (`TPB-02.11` stub) | `archivar en auditoria/archivados/` |
| 100 | `specs/009-reportes-e-informes/tasks.md` | equipo | alguien pregunta | 3. Incompleto (único archivo sin `spec.md`/`plan.md` y declara parciales como terminados) | `conservar y completar` |
| 101 | `specs/010-circuito-resolutivo-enmiendas/plan.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 102 | `specs/010-circuito-resolutivo-enmiendas/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 103 | `specs/010-circuito-resolutivo-enmiendas/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 104 | `specs/010-optimizacion-rendimiento/memory_audit_report.md` | equipo / cátedra | alguien pregunta | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 105 | `specs/010-optimizacion-rendimiento/plan.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 106 | `specs/010-optimizacion-rendimiento/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 107 | `specs/010-optimizacion-rendimiento/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 108 | `specs/011-libro-mayor-mis-expedientes-publicacion/plan.md` | equipo | alguien se equivoca | 3. Incompleto | `conservar y completar` |
| 109 | `specs/011-libro-mayor-mis-expedientes-publicacion/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 110 | `specs/011-libro-mayor-mis-expedientes-publicacion/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
| 111 | `specs/012-panel-administracion/plan.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 112 | `specs/012-panel-administracion/spec.md` | equipo | alguien pregunta | 4. Vigente | `conservar y completar` |
| 113 | `specs/012-panel-administracion/tasks.md` | nadie | nada | 1. Residuo de fabricación | `archivar en auditoria/archivados/` |
