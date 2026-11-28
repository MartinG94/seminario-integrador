# Propuesta de Destinos para Aprobación — SGD-AVEIT

> **Fecha:** 27/11/2026  
> **Instrucciones de revisión:** Marcá `[x] aprobar` por bloque o por archivo individual. Ningún archivo será movido, editado ni eliminado hasta contar con tu aprobación explícita.  
> **Total cubierto:** `113` documentos versionados (correspondencia 1:1 con [`auditoria/evaluacion_documentacion.md`](evaluacion_documentacion.md)).

---

## Decisión 1 — Gobernanza operativa, guías técnicas y `notasPO.md` (`17` archivos)

### 1A. Conservar y completar alineando al estado real del repositorio (`10` archivos)
*Dependen de actualizar referencias de votación nominal descartada, comandos reales, estado S5/S6 y completar documentación técnica.*
- [x] aprobar `AGENTS.md` → `conservar y completar` *(quitar mención residual a votación nominal en §1; crear `auditoria/archivados/LEEME.md` al archivar)*
- [x] aprobar `DESIGN.md` → `conservar y completar` *(alinear mención de votación/5 columnas y documentar centro de notificaciones PR #49)*
- [x] aprobar `README.md` → `conservar y completar` *(actualizar módulos S2–S5, quitar votación nominal/"cómputo algorítmico" y arreglar links)*
- [x] aprobar `TASK.md` → `conservar y completar` *(sincronizar con `traspaso-sprint6.md`: corregir falsos completos de alertas/PDF/RBAC y rutas rotas)*
- [x] aprobar `docs/constitution.md` → `conservar y completar` *(alinear Principio 4 y Principio 7 con `AGENTS.md` y firma colegiada)*
- [x] aprobar `.github/ISSUE_TEMPLATE/reporte_incidencia.md` → `conservar y completar` *(mantener vigente; alinear campo identificador si se usa GitHub Issues)*
- [x] aprobar `backend/README.md` → `conservar y completar` *(actualizar endpoints, `seed_demo`, `numero_socio` y corregir `cp .env.example .env`)*
- [x] aprobar `docs/adr/README.md` → `conservar y completar` *(indexar ADRs posteriores a ADR-001: Outbox, Libro Mayor, firma colegiada, Strategy, Admin)*
- [x] aprobar `docs/adr/ADR-001-consumo-padron-institucional.md` → `conservar y completar` *(ajustar timeout `60`s, firma paginada `list_socios`, quitar mención a Votación S4 y cerrar aprobación)*
- [x] aprobar `docs/especificaciones/RBAC-SGD-AVEIT.md` → `conservar y completar` *(ampliar a todos los endpoints actuales y `IsNotInvolvedInExpediente`; documentar `FISCALIZADORA` como rol vigente actual y la partición en `AUTORIDAD_SC` / `REVISORES` de `SCRUM-121` como trasladada al Sprint 6)*

### 1B. Conservar sin cambios por obligación legal MIT (`1` archivo)
- [x] aprobar `frontend/LICENSE.md` → `conservar y completar` *(mantener intacto por atribución MIT de Creative Tim; aclarar coexistencia con Apache-2.0 en documentación)*

### 1C. Conservar y recortar instrucciones obsoletas o riesgosas (`4` archivos)
*Dependen de retirar fragmentos no implementados (`OAuth 2.0`, `develop`, `VotoNominal`, SQL directo sobre `socios_socio`).*
- [x] aprobar `docs/gestion-proyecto/GUIA_PULL_REQUESTS.md` → `conservar y recortar` *(quitar referencia obsoleta a rama `develop`)*
- [x] aprobar `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md` → `conservar y recortar` *(retirar Método 2 OAuth 2.0/Gmail API no implementado y agregar `retry/` e `idempotency_key`)*
- [x] aprobar `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` → `conservar y recortar` *(retirar `UPDATE` manual sobre `socios_socio` reemplazado por `/admin/parametros` y dejar solo el alcance externo `socio_lista.idTipoSocio`)*
- [x] aprobar `docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md` → `conservar y recortar` *(ajustar encabezado "borrón y cuenta nueva" e ítem `VotoNominal` en §7 para que no contradigan `legacy_rbac.py` ni el código)*

### 1D. Decisión exclusiva del Product Owner sobre `notasPO.md` (`1` archivo)
*Bloqueado por Regla Innegociable 5 de `AGENTS.md`: requiere orden explícita del PO para editar o marcar bloques superados.*
- [ ] aprobar `docs/gestion-proyecto/notasPO.md` → `conservar y recortar` *(depurar/marcar como históricas las instrucciones de 27/09 y enunciados que inducen a error a agentes: renombre de `FISCALIZADORA`, alertas `-10`/`-7` y reportes "implementados", apelación sobre resoluciones)*

### 1E. Archivar plantilla de GitHub duplicada (`1` archivo)
- [ ] aprobar `.github/ISSUE_TEMPLATE/tarea_sprint.md` → `archivar en auditoria/archivados/` *(redundante con `AGENTS.md` y Jira; desactualizado en Python 3.11 y prefijo `[US-XX]`)*

---

## Decisión 2 — Fuentes normativas oficiales de AVEIT (`4` archivos)

*Documentación institucional de referencia (no editable). Se conserva intacta en su carpeta actual.*
- [x] aprobar `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Estatuto_AVEIT_Reforma_2026.pdf` → `conservar y completar` *(conservar sin cambios)*
- [x] aprobar `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2018).pdf` → `conservar y completar` *(conservar sin cambios)*
- [x] aprobar `docs/analisis-proceso-actual/reglamentos-aveit/NOR_REGLAMENTO PROCESAL DISCIPLINARIO (version 2026).pdf` → `conservar y completar` *(conservar sin cambios)*
- [x] aprobar `docs/analisis-proceso-actual/reglamentos-aveit/NOR_Reglamento_Interno_Disciplina_AVEIT_2026.pdf` → `conservar y completar` *(conservar sin cambios)*

---

## Decisión 3 — Entregables formales de cátedra y resolución de copias duplicadas (`15` archivos)

### 3A. Fuente única editable/maestra a conservar y completar (`6` archivos)
*Dependen de la decisión de consolidar una sola fuente por entregable para regularidad/final, manteniendo inmutables las fechas históricas ya presentadas.*
- [x] aprobar `docs/formales/Estudio_Inicial.docx` → `conservar y completar` *(traer base `v1.5.0` humana y cerrar obs. #1–#5, #23, #31 con nueva fecha)*
- [x] aprobar `docs/formales/Plan_de_Proyecto.docx` → `conservar y completar` *(limpiar restos `v1.0.1`, etiquetas de IA, `RF-09` votación, unificar `Grupo` y completar RBAC/CU/módulos en nueva versión)*
- [x] aprobar `docs/gestion-proyecto/Seguimiento de Proyecto.md` → `conservar y completar` *(incorporar v1.4.0, cierre real S4 por git, S5 Consolidado, traspaso S6 y corregir stack §2.1.5 sin alterar fechas presentadas)*
- [x] aprobar `docs/especificaciones/ERS-SGD-AVEIT.md` → `conservar y completar` *(elegida sobre `ERS_Especificacion_Requerimientos_Tribunal.md`; eliminar votación nominal, agregar apelación T01 y módulos S3–S5)*
- [x] aprobar `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` → `conservar y completar` *(eliminar `VotoNominal`, resolver contradicciones internas T02/T03 y Juniors/Seniors, agregar entidades reales)*
- [x] aprobar `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md` → `conservar y completar` *(actualizar a 6 estados, firma colegiada sin votación, stack Angular y corregir sintaxis Mermaid)*

### 3B. Copias redundantes o superadas a archivar en `auditoria/archivados/` (`9` archivos)
*Dependen de aprobar 3A: evitan tener múltiples versiones desincronizadas del mismo entregable.*
- [x] aprobar `docs/formales/Estudio_Inicial.pdf` → `archivar en auditoria/archivados/` *(exportación `v1.0.1` duplicada de `Estudio_Inicial.docx`)*
- [x] aprobar `docs/analisis-proceso-actual/TPI_Estudio_Inicial_SGD_AVEIT.md` → `archivar en auditoria/archivados/` *(borrador Markdown redundante con `Estudio_Inicial.docx`)*
- [x] aprobar `docs/formales/Plan_de_Proyecto.pdf` → `archivar en auditoria/archivados/` *(exportación obsoleta `v1.0.1` frente a `Plan_de_Proyecto.docx`)*
- [x] aprobar `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md` → `archivar en auditoria/archivados/` *(borrador Markdown redundante y desactualizado frente a `Plan_de_Proyecto.docx`)*
- [x] aprobar `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` → `archivar en auditoria/archivados/` *(recorte S3 superado por la versión S4 y los entregables actuales)*
- [x] aprobar `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` → `archivar en auditoria/archivados/` *(ERS redundante con `ERS-SGD-AVEIT.md`, inconsistente en estados y con links rotos)*
- [x] aprobar `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md` → `archivar en auditoria/archivados/` *(spec congelada con Tailwind/Triggers/5 estados y link roto `G:\My Drive`)*
- [x] aprobar `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md` → `archivar en auditoria/archivados/` *(redundante con Plan de Proyecto / Def. Producto; conserva votación nominal)*
- [x] aprobar `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md` → `archivar en auditoria/archivados/` *(spec puntual ya implementada y cubierta por `specs/005-sanciones-reuniones-solicitudes/`)*

---

## Decisión 4 — Manual de Usuario (`11` archivos)

### 4A. Conservar y completar consolidado y guía de compilación (`2` archivos)
- [ ] aprobar `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf` → `conservar y completar` *(regenerar desde `src/*.html` agregando carátula, índice, historial, propósito, configuración, alineando rol vigente `FISCALIZADORA` hasta Sprint 6 y actualizando cap. 02/04/07/08/09)*
- [ ] aprobar `docs/manual-usuario/README.md` → `conservar y completar` *(limpiar rutas locales `c:\git\...` y `G:\My Drive\...`, alinear rol vigente `FISCALIZADORA`/Reportes)*

### 4B. Retirar binarios PDF modulares redundantes (`9` archivos)
*Contienen exactamente el mismo texto que `Manual_Usuario_SGD_AVEIT_Completo.pdf` y se regeneran desde `src/*.html` con `render_pdfs.py`.*
- [ ] aprobar `docs/manual-usuario/pdfs/01_Acceso_y_Navegacion.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/02_Mis_Expedientes_y_Descargos.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/03_Reglamentos.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/04_Ranking_de_Socios.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/05_Calendario_Institucional.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/06_Crear_Expediente.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/07_Gestionar_Expedientes_TD.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/08_Eventos_y_Asistencia.pdf` → `eliminar después de un sprint sin reclamos`
- [ ] aprobar `docs/manual-usuario/pdfs/09_Reportes_y_Administracion.pdf` → `eliminar después de un sprint sin reclamos`

---

## Decisión 5 — Documentos I+D de IA (`SCRUM-76`) (`6` archivos)

*Ninguna funcionalidad de IA (`laya-service`, SLMs, RAG/CAG/MAG) está implementada en el código; se archivan juntos para no confundir el alcance real del producto.*
- [x] aprobar `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/Implementacion IA/presentacion/02_propuesta_tribunal_disciplina.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/Implementacion IA/presentacion/03_propuesta_comision_directiva.md` → `archivar en auditoria/archivados/`

---

## Decisión 6 — Residuos de fabricación y bitácoras puntuales (`15` archivos)

### 6A. Archivar bitácoras históricas de proyecto (`4` archivos)
*Tienen trazabilidad de decisiones/métricas puntuales del proyecto; pasan a archivo histórico.*
- [x] aprobar `PLAN_SPRINT_5_CONSOLIDADO.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/gestion-proyecto/ANALISIS_INTEGRAL_BACKLOG_JIRA.md` → `archivar en auditoria/archivados/`
- [x] aprobar `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/010-optimizacion-rendimiento/memory_audit_report.md` → `archivar en auditoria/archivados/`

### 6B. Eliminar después de un sprint sin reclamos los residuos puros sin valor histórico (`11` archivos)
*Plantillas de terceros sin adaptar, plantillas vacías, PDF ajeno al sistema, copias UAT duplicadas, informes efímeros de worktree/git y relevamientos previos ya absorbidos por `specs/010`.*
- [x] aprobar `frontend/CHANGELOG.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `frontend/README.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/design/ranking-socios/README.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/analisis-proceso-actual/sistema-actual/Rifas - Actas - Entrega - Desde cero.pdf` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/especificaciones/PLANTILLA_CASO_DE_USO.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/formales/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/gestion-proyecto/INFORME_DIVERGENCIA_MAIN_PRESENTACION.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/gestion-proyecto/UAT-PR49-calendario.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/gestion-proyecto/relevamiento_scrum_119_frontend_onpush_trackby.md` → `eliminar después de un sprint sin reclamos`
- [x] aprobar `docs/gestion-proyecto/relevamiento_scrum_120_optimizacion_orm.md` → `eliminar después de un sprint sin reclamos`

---

## Decisión 7 — Documentación interna SDD en `specs/` (`45` archivos restantes)

### 7A. Specs base de Sprints 1–2 (`001` y `003`) — Aprobado conservar y completar (`3` archivos)
*Decisión aprobada (`2026-11-27`): son la única especificación de Login/JWT, RBAC base, Socios, Ranking y Mis Solicitudes T01; se actualizan al código real (sin votación nominal, `numero_socio`, `backend/padron/`, `PuntajeGeneral`/`PuntajeAplicado`) en lugar de archivarse.*
- [x] aprobar `specs/001-walking-skeleton/plan.md` → `conservar y completar`
- [x] aprobar `specs/001-walking-skeleton/spec.md` → `conservar y completar`
- [x] aprobar `specs/003-monitorear-solicitudes-t01/spec.md` → `conservar y completar`

### 7B. Archivar todos los `tasks.md` de iteraciones cerradas (`15` archivos)
*Checklists de tareas atómicas ya integradas (nota: volcar primero los resúmenes de PR #78/#79 de `011` y `012` en sus `spec.md`/`plan.md` antes de moverlos).*
- [ ] aprobar `specs/001-walking-skeleton/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/002-expediente-trazabilidad/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/003-monitorear-solicitudes-t01/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/004-calendario-dias-habiles/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/004-clasificador-urgencia/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/005-evidencia-protegida/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/005-sanciones-reuniones-solicitudes/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/006-resolver-causal-t02/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/007-apartamiento-suplencia/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/007-visor-expediente-evidencia/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/008-apelacion-adecuacion-t01/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/010-circuito-resolutivo-enmiendas/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/010-optimizacion-rendimiento/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/011-libro-mayor-mis-expedientes-publicacion/tasks.md` → `archivar en auditoria/archivados/`
- [ ] aprobar `specs/012-panel-administracion/tasks.md` → `archivar en auditoria/archivados/`

### 7C. Conservar y sincronizar `spec.md` / `plan.md` vigentes + `specs/009` (`27` archivos)
*Requiere autorización explícita por Regla 5 de `AGENTS.md` (no tocar `specs/` sin pedido) para corregir rutas rotas, marcar DoD, incorporar cambios post-PR y completar `specs/009` frente al traspaso a Sprint 6.*
- [x] aprobar `specs/002-expediente-trazabilidad/plan.md` → `conservar y completar`
- [x] aprobar `specs/002-expediente-trazabilidad/spec.md` → `conservar y completar`
- [x] aprobar `specs/004-calendario-dias-habiles/plan.md` → `conservar y completar`
- [x] aprobar `specs/004-calendario-dias-habiles/spec.md` → `conservar y completar`
- [x] aprobar `specs/004-clasificador-urgencia/plan.md` → `conservar y completar`
- [x] aprobar `specs/004-clasificador-urgencia/spec.md` → `conservar y completar`
- [x] aprobar `specs/005-evidencia-protegida/plan.md` → `conservar y completar`
- [x] aprobar `specs/005-evidencia-protegida/spec.md` → `conservar y completar`
- [x] aprobar `specs/005-sanciones-reuniones-solicitudes/plan.md` → `conservar y completar`
- [x] aprobar `specs/005-sanciones-reuniones-solicitudes/spec.md` → `conservar y completar`
- [x] aprobar `specs/006-resolver-causal-t02/plan.md` → `conservar y completar`
- [x] aprobar `specs/006-resolver-causal-t02/spec.md` → `conservar y completar`
- [x] aprobar `specs/007-apartamiento-suplencia/plan.md` → `conservar y completar`
- [x] aprobar `specs/007-apartamiento-suplencia/spec.md` → `conservar y completar`
- [x] aprobar `specs/007-visor-expediente-evidencia/plan.md` → `conservar y completar`
- [x] aprobar `specs/007-visor-expediente-evidencia/spec.md` → `conservar y completar`
- [x] aprobar `specs/008-apelacion-adecuacion-t01/plan.md` → `conservar y completar`
- [x] aprobar `specs/008-apelacion-adecuacion-t01/spec.md` → `conservar y completar`
- [x] aprobar `specs/009-reportes-e-informes/tasks.md` → `conservar y completar`
- [x] aprobar `specs/010-circuito-resolutivo-enmiendas/plan.md` → `conservar y completar`
- [x] aprobar `specs/010-circuito-resolutivo-enmiendas/spec.md` → `conservar y completar`
- [x] aprobar `specs/010-optimizacion-rendimiento/plan.md` → `conservar y completar`
- [x] aprobar `specs/010-optimizacion-rendimiento/spec.md` → `conservar y completar`
- [x] aprobar `specs/011-libro-mayor-mis-expedientes-publicacion/plan.md` → `conservar y completar`
- [x] aprobar `specs/011-libro-mayor-mis-expedientes-publicacion/spec.md` → `conservar y completar`
- [x] aprobar `specs/012-panel-administracion/plan.md` → `conservar y completar`
- [x] aprobar `specs/012-panel-administracion/spec.md` → `conservar y completar`
