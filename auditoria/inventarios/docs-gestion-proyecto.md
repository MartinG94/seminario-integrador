# Inventario de Auditoría — `docs-gestion-proyecto`

> **Fecha de auditoría:** 27/11/2026  
> **Modo:** Solo lectura (contrastado contra `auditoria/registro-canonico.md` y el estado actual del repositorio).  
> **Alcance:** 12 archivos en `docs/gestion-proyecto/`.

---

## 1. `docs/gestion-proyecto/ANALISIS_INTEGRAL_BACKLOG_JIRA.md`

- **Ruta:** `docs/gestion-proyecto/ANALISIS_INTEGRAL_BACKLOG_JIRA.md`
- **Líneas:** 175
- **Última modificación:** `2026-09-08`
- **Tema que cubre:** Diagnóstico inicial del repositorio (08/09/2026), hallazgos normativos y propuesta/ejecución de recarga del backlog v2 en Jira (`SCRUM-28` a `SCRUM-71`).
- **Quién lo lee:** nadie (snapshot histórico de inicio de Sprint 1).
- **Qué pasa si desaparece:** nada.
- **Clasificación:** **1. Residuo de fabricación** (diagnóstico y bitácora puntual de importación de backlog a Jira previa al inicio del desarrollo; no es entregable formal de cátedra ni documentación técnica vigente).
- **Contradicciones con el registro:**
  - Afirma que *"no existe backend Django operativo"*, que `TribunalDataService` usa colecciones mock en memoria y que no existen pruebas unitarias backend ni frontend (§1, §3.1); el registro (§2) verifica backend Django/DRF y frontend Angular operativos con 114 archivos `test_*.py` y 55 `*.spec.ts`.
  - Planifica voto nominal y mayoría de 2 votos afirmativos en Sprint 4 (§4, §6); el registro (§2, §3) indica que la votación nominal fue descartada por el PO el 07/10/2026 y reemplazada por firma colegiada de 3 representantes de años activos (4.º, 5.º y 6.º).
  - Describe un horizonte de 6 sprints (120 SP + 3 stretch) con Sprint 5 y Sprint 6 separados (§6, §11); el registro (§5.3) documenta la fusión en Sprint 5 Consolidado.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - Describe como planificados/pendientes en Sprints 5–6 la reconciliación `PuntajeAplicado` vs `PuntajeGeneral` (`SCRUM-64`), pruebas de carga de 50 usuarios (`SCRUM-65`), balance Art. 137 en PDF (`SCRUM-63`), alertas `-7/-10` (`SCRUM-62`), jurisprudencia (`SCRUM-68`) y gestión interna de casos (`PB-01`); el registro (§2) marca estos ítems como `parcial` o `no implementada`.
- **Funcionalidad implementada que debería cubrir y no cubre:** No aplica por ser un snapshot fechado el 08/09/2026 (anterior a toda la implementación de Sprints 1–5).
- **Referencias rotas:**
  - `C:\Users\mguillen\Downloads\modulo-tribunal-stack-y-modelos(2).md` (ruta local absoluta de máquina personal, inexistente en el repo).
  - Menciona `ERS`, `modelo de dominio`, `BPMN`, `estudio inicial` sin rutas explícitas; `Procesos-BPMN-SGD-AVEIT.md` y `Estudio-Inicial-SGD-AVEIT.md` no existen con esos nombres en el repo.

---

## 2. `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md`

- **Ruta:** `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md`
- **Líneas:** 184
- **Última modificación:** `2026-10-22`
- **Tema que cubre:** Complemento operativo de Definición de Producto para la apertura y cierre del Sprint 3 (RF-08 a RF-18, criterios Gherkin, casos de uso y trazabilidad).
- **Quién lo lee:** equipo / cátedra (fue insumo de volcado para Google Drive al cierre de S3).
- **Qué pasa si desaparece:** nada (existe versión posterior presentada a cátedra en `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`, según el registro §5.4).
- **Clasificación:** **3. Redundante con `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` (externo al repo, en Google Drive / Documentación Actual Humana) e incompleto** (queda desactualizado respecto al estado real tras Sprints 4 y 5; además promete una matriz de trazabilidad bidireccional y no incluye historias implementadas, pruebas ni resultados, observación #25 del registro §1.3).
- **Contradicciones con el registro:**
  - Indica `Grupo Nº 04` (línea 6); el registro (§3) señala la inconsistencia documental entre `Grupo 13` (`Estudio_Inicial.docx`, `Plan_de_Proyecto.docx`) y `Grupo Nº 04`.
  - Indica inicio de Sprint 3 el `08/10/2026` (línea 9) e inicio de Sprint 4 el `22/10/2026` (línea 174); el registro (§1.3 obs. #26) registra la inconsistencia de calendario frente a `07/10` y `21/10` en el calendario maestro de Seguimiento.
  - En CA-RF08.1 (línea 43) usa el estado `EN_PERIODO_DE_JUSTIFICACIONES` y fija el vencimiento a las `18:00 hs del 5º día hábil` (línea 44); el registro (§3) indica el valor canónico `justificando` en backend.
  - En §2.1 (línea 104) afirma que se reemplaza `"Comisión Fiscalizadora"` por `"Revisores de Cuentas"` *"en todas las capas del sistema"*; el registro (§3) verifica que el enum RBAC en código sigue siendo `FISCALIZADORA`.
  - En §1.2 (línea 29) indica límite de 4000 caracteres para T03, mientras en §2.2 (línea 115) indica 5000 caracteres (inconsistencia interna).
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - En §2.2 (línea 119) marca `RF-17 (Eventos, Asistencias y Sanciones 3:1)` como `100% Completado`; el registro (§2) marca eventos/asistencia como `implementada`, pero las alertas automáticas por acumulación 3:1 (`SCRUM-61`) como `parcial` (falta aviso preventivo a autoridades).
  - En §2.2 (línea 116) afirma validación RBAC y auditoría al 100%, y el registro (§1.3 obs. #27) señala falta de evidencia precisa de ejecución de pruebas sobre permisos, vencimientos y transacciones.
- **Funcionalidad implementada que debería cubrir y no cubre:** Al ser un recorte de Sprint 3, no cubre ninguna funcionalidad de Sprints 4 y 5 (Visor unificado `SCRUM-51`, Valoración T03 `SCRUM-53`, Composición TD/suplencias `SCRUM-54`, Apelación T01 `SCRUM-70`, Resolución y firmas colegiadas `SCRUM-56`/`58`/`89`, Exclusión `SCRUM-102`, Enmienda `SCRUM-103`, Libro Mayor `SCRUM-57`/`59`, Publicación protegida `SCRUM-60`, ABM Reglamentos, Reportes, Panel Admin `SCRUM-91`, Paginación/ORM/OnPush `SCRUM-87`, Manual de Usuario `SCRUM-129`).
- **Referencias rotas:**
  - `GET /api/v1/expedientes/<id>/evidencias/<file_id>/` (línea 60): ruta descrita de forma genérica; no verificada como ruta literal exacta frente a los URL patterns.
  - Menciona `"Formato Imagen 2 TD"` y `"Ref. Imagen 3 TD"` sin incluir las imágenes ni rutas a archivos de imagen en el repositorio.

---

## 3. `docs/gestion-proyecto/GUIA_PULL_REQUESTS.md`

- **Ruta:** `docs/gestion-proyecto/GUIA_PULL_REQUESTS.md`
- **Líneas:** 134
- **Última modificación:** `2026-09-09`
- **Tema que cubre:** Reglas operativas, formato de título convencional, plantilla de descripción y pautas de revisión de Pull Requests para desarrolladores y agentes IA.
- **Quién lo lee:** equipo (y agentes IA, referenciado obligatoriamente desde `AGENTS.md`).
- **Qué pasa si desaparece:** alguien se equivoca (se rompe la referencia normativa de `AGENTS.md` sobre formato de PRs y los desarrolladores/agentes pierden la plantilla estándar).
- **Clasificación:** **4. Vigente**.
- **Contradicciones con el registro:** Ninguna respecto al estado funcional o terminología del código. *(Observación menor de proceso: línea 133 menciona prohibición de `push` directo a `main` ni a `develop`, aunque el trabajo reciente se integra en ramas hacia `main` / `regularidadDocs`.)*
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:** Ninguna (es una guía de proceso Git/PR, no de producto).
- **Referencias rotas:** Ninguna (el enlace interno `#nombre-del-pull-request` es válido).

---

## 4. `docs/gestion-proyecto/INFORME_DIVERGENCIA_MAIN_PRESENTACION.md`

- **Ruta:** `docs/gestion-proyecto/INFORME_DIVERGENCIA_MAIN_PRESENTACION.md`
- **Líneas:** 126
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Análisis forense puntual de Git (14/10/2026) explicando la divergencia entre las ramas `main` y `presentacion`.
- **Quién lo lee:** nadie (diagnóstico puntual de un incidente de ramas de octubre de 2026).
- **Qué pasa si desaparece:** nada.
- **Clasificación:** **1. Residuo de fabricación** (informe de diagnóstico puntual sobre una rama temporal de presentación del 09/10/2026; no es arquitectónico, ni entregable formal de cátedra, ni aporta al código actual).
- **Contradicciones con el registro:**
  - Describe a `origin/main` detenida en el commit `73a2d8a` (11/10/2026, PR #49); el registro (§introducción) refleja el estado actual del repositorio al 23/11/2026 (`6a60167`).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna relevante fuera de su corte temporal del 14/10/2026.
- **Funcionalidad implementada que debería cubrir y no cubre:** No aplica (informe puntual de Git).
- **Referencias rotas:**
  - `[AGENTS.md](file:///d:/Proyectos-mg/seminario-integrador/AGENTS.md)` (líneas 18 y 66): enlace absoluto a ruta local inexistente `d:/Proyectos-mg/...`.
  - `docs/presentacion/GUION_ORATORIA_PNL.md`, `PRESENTACION_EJECUTIVA.md`, `deck_batch.json` y `seed_expedientes.py` (líneas 57, 88, 102, 116): no existen en el árbol de trabajo actual.

---

## 5. `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md`

- **Ruta:** `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md`
- **Líneas:** 579
- **Última modificación:** `2026-09-26`
- **Tema que cubre:** Plan de Proyecto de Software v2.0.0 para la cátedra (equipo, taxonomía SI, Scrumban, RBAC, RF-01 a RF-15, RN-01 a RN-10, RNF ISO 25010, restricciones, CU-01 y cronograma).
- **Quién lo lee:** cátedra / equipo.
- **Qué pasa si desaparece:** alguien pregunta (es la versión Markdown en el repositorio de uno de los 4 entregables obligatorios de la cátedra, aunque también existe `Plan_de_Proyecto.docx` fuera del repo).
- **Clasificación:** **3. Redundante con `Plan_de_Proyecto.docx` (externo en Documentación Actual Humana) e incompleto / desactualizado** (queda desactualizado frente a los cambios funcionales aprobados desde octubre/noviembre 2026 y las observaciones docentes posteriores).
- **Contradicciones con el registro:**
  - **N.º de Grupo:** indica `Grupo de Proyecto: Nº 04` (línea 7), mientras `Plan_de_Proyecto.docx` y `Estudio_Inicial.docx` dicen `Grupo 13` (registro §3).
  - **Historial de revisiones:** `v1.0.0` figura con fecha `18/08/2026` (línea 36) y omite `v1.0.1` del `02/09/2026`; el registro (§5.2) registra `v1.0.0` el `01/09/2026` y `v1.0.1` el `02/09/2026` en `Plan_de_Proyecto.docx`.
  - **Votación nominal:** incluye `RF-09` (*Registro Nominal de Votación del Tribunal*, línea 274), `emitirVotoNominal()` (línea 210), fila de votación nominal en matriz RBAC (línea 250) y `RN-06` con voto favorable de 2 de 3 miembros (línea 319); el registro (§1.2 obs. #23, §1.3 obs. #24, §1.4 obs. #31, §2, §3) indica que la votación nominal fue descartada por el PO el 07/10/2026 y debe eliminarse de los documentos generales.
  - **Firma colegiada (2 vs 3 firmas):** `RN-07` (línea 321) y `RNF-03` (línea 369) exigen *"al menos dos firmas"*; el registro (§1.4 obs. #33, §2, §3) establece firma colegiada de **3 integrantes** habilitados representando años sociales 4.º, 5.º y 6.º.
  - **Recusación:** `RN-06` (línea 319) habla de miembro *"recusado por parentesco o conflicto de interés"*; el Estatuto Art. 93 prohíbe la recusación y el sistema implementa apartamiento por conflicto (`SCRUM-54`, registro §2).
  - **Roles RBAC y terminología:** usa `Socio Ordinario`, `Autoridad Subcomisión`, `Comisión Fiscalizadora` (líneas 130, 240, 309, 330); el registro (§3) detalla los roles canónicos del código (`SOCIO`, `FISCALIZADORA`, `CD`, `TD`, `ADMIN`) y el renombre documental a `Revisores de Cuentas`.
  - **Stack Frontend:** línea 105 menciona `HTML5/CSS3 moderno y Tailwind CSS` y `JavaScript`; el registro (§3) confirma Angular 14.2+ + TypeScript + Angular Material (sin Tailwind).
  - **Legajo vs Número de Socio:** líneas 86–92, 98–112 y 501 usan `"Legajo"` en vez de `"Número de Socio"` (mezclado con línea 25–27 que dice `"Número de Socio"`).
  - **Triggers MySQL / tabla `auditoria_puntos`:** `RNF-02` (línea 357) y §13.1 (`R-03`) especifican triggers `BEFORE UPDATE/INSERT` y tabla `auditoria_puntos`; el registro (§2, §3) confirma que el código usa el modelo `AsientoLibroMayor` (`InsertOnly`) y `PuntajeAplicado.registrar_movimiento` en Django.
  - **Transición de estados:** `RN-05` (línea 317) y CU-01 paso 7 (línea 479) dicen que cargar un descargo transiciona inmediatamente a *"Las justificaciones están siendo revisadas"* y que no hay retrocesos; el sistema real mantiene el plazo abierto para edición/retiro hasta vencimiento y contempla enmiendas (`SCRUM-103`) y apelación/adecuación T01 (`SCRUM-70`).
  - **Cronograma Gantt (§13):** plantea 4 sprints de construcción (11/09 al 06/11) con contenidos distintos a los sprints reales ejecutados (6 sprints luego consolidados en Sprint 5).
  - **Propietario de Balance Art. 137:** asigna generación exclusiva a `Miembro TD` (`RF-14`, §6.1, `CU-05`), sin reflejar el alcance actual de `Reportes` ni la distinción de roles.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - `RF-13` y `RN-09` (alertas automáticas `-7` y `-10`): marcadas como `Must Have`; el registro (§2) las marca como `parcial` (no conectadas al flujo productivo ni con endpoint/vista).
  - `RF-14` (Balance Cuatrimestral Art. 137 exportable a **PDF**): marcado como `Must Have`; el registro (§2) lo marca como `parcial` (solo existe JSON y CSV, falta PDF).
  - `RNF-04` (pruebas de carga con 50 usuarios concurrentes en staging) y `RNF-05` (pruebas OWASP Top 10 / 100% endpoints protegidos por RBAC): el registro (§2) marca `SCRUM-65` como `no implementada` y señala 6 vistas de `reportes_views.py` sin permiso de rol específico.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - Eventos, reuniones y asistencias con patrón Strategy y acumulación 3:1 (`SCRUM-50`/`86`).
  - Calendario institucional de días hábiles (`SCRUM-45`).
  - Apelación y adecuación del Formulario T01 (`SCRUM-70`).
  - Exclusión fundada de involucrados (`SCRUM-102`) y Enmienda trazable de resoluciones (`SCRUM-103`).
  - ABM de Reglamentos con auditoría.
  - Panel de Administración de parámetros y miembros TD (`SCRUM-91`).
  - Censura médica en publicación oficial (`SCRUM-60`/`106`).
  - Causas multi-socio con resolución individualizada.
- **Referencias rotas:**
  - Menciona skills internos de generación (`/systemClassifier`, `/requirementsExtractor`, `/useCaseExtractor`, líneas 37, 117, 119, 262, 422, 424) como si fueran parte del documento formal para la cátedra.
  - Menciona `Circular Normativa 001/2026` (líneas 72, 297, 572), inexistente en el repositorio.
  - Enlace interno `#4-diagnóstico-sistémico-y-taxonomía-de-sistemas-de-información` (línea 46) no coincide con el encabezado `#4-diagnóstico-sistémico-y-taxonomía-de-sistemas-de-información-systemclassifier` (línea 117).

---

## 6. `docs/gestion-proyecto/Seguimiento de Proyecto.md`

- **Ruta:** `docs/gestion-proyecto/Seguimiento de Proyecto.md`
- **Líneas:** 796
- **Última modificación:** `2026-10-25`
- **Tema que cubre:** Documento maestro de Seguimiento de Proyecto (v1.3.0): Sprint 0 (Working Agreement, capacidad, RACI, herramientas, backlog, story map), Sprints 1–3 cerrados y apertura del Sprint 4.
- **Quién lo lee:** cátedra / equipo.
- **Qué pasa si desaparece:** alguien pregunta / alguien se equivoca (es uno de los 4 entregables obligatorios de la cátedra y es referenciado por `AGENTS.md` como artefacto de gobernanza macro).
- **Clasificación:** **3. Redundante con `Seguimiento_de_ProyectoVersionSprint4.pdf` (externo en Documentación Actual Humana) e incompleto** (en el repo está congelado en `v1.3.0` del `22/10/2026`: solo tiene apertura de Sprint 4 y plantillas vacías en §2.8 para cierre de S4, S5 y S6, quedando desactualizado frente a la versión `v1.4.0` presentada el `04/11/2026` y frente al estado real de Sprint 5).
- **Contradicciones con el registro:**
  - **Stack Frontend (§2.1.5, línea 266):** describe el frontend como *"HTML5 semántico, CSS3 modular (`tokens.css`) y Vanilla JavaScript (`view-cd.js`, `view-td.js`, `view-socio.js`)"*; el registro (§3) confirma Angular 14.2+ + TypeScript + Angular Material (contradice incluso a §2.2 del mismo archivo, que habla de Angular 14).
  - **Inconsistencia de fechas de calendario:** §2.1.1.A (líneas 119–121) indica Sprint 3 `07/10 al 20/10` y Sprint 4 `21/10 al 03/11`, mientras §2.6.1 (línea 626) dice Sprint 3 inicio `08/10/2026` y §2.7.1 (línea 723) dice Sprint 4 inicio `22/10/2026` (observación docente #26 en registro §1.3).
  - **Votación nominal en Sprint 0 (§2.1.1.A, §2.1.6 US-13, §2.1.7):** mantiene *"Votación y Firma Colegiada"* y `US-13` (*Deliberación Remota y Votación Nominal Fundada*), aunque en §2.5.2 y §2.7.1 se indica que fue descartada el 07/10/2026.
  - **Renombre Fiscalizadora → Revisores (§2.5.2, línea 603):** afirma adecuación *"en todo el código"*; el registro (§3) verifica que el enum RBAC del código sigue siendo `FISCALIZADORA`.
  - **Modelo Outbox (§2.3.2 línea 464 y §2.4.1 línea 505):** nombra el modelo como `EmailNotificationQueue`; en el código real (`backend/notifications/models.py` y registro §2) el modelo se llama `EmailOutbox` (y `EmailAttachment`).
  - **Velocidad proyectada (§2.1.6, línea 305):** usa la expresión *"Velocidad Promedio Proyectada: ~19.3 SP"* y no incorpora corte horizontal de MVP/Release ni presenta el calendario como roadmap adaptable (observaciones docentes #17, #18, #19 y #20 en registro §1.1–1.2).
  - **T03 límite de caracteres:** §2.6.1 (línea 640) dice `4000 caracteres` y §2.6.2 (línea 664) dice `5000 caracteres`.
  - **DoD (§2.1.1.D, línea 164):** exige merge a `develop`, mientras el desarrollo real integró PRs a `main`.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - En §2.2.2 y §2.4.2 y §2.6.2 declara 100% DoD cumplido (que incluye despliegue en Staging según §2.1.1.D línea 168); el registro (§2, §6) marca el despliegue en Staging (`SCRUM-66`) como `No verificable`.
  - En §2.6.2 (línea 669) declara `SCRUM-50` 100% completado con acumulación 3:1; el registro (§2) marca la alerta automática por acumulación 3:1 (`SCRUM-61`) como `parcial`.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - Cierre real del Sprint 4 (incluyendo la distinción verificada por git en registro §1.4 obs. #29 sobre qué historias estaban en `main` al 03/11 y cuáles entraron el 05/11 y 12/11).
  - Apertura y ejecución del Sprint 5 Consolidado (fusión S5+S6): emisión oficial y firmas colegiadas (`SCRUM-58`/`89`), Libro Mayor (`SCRUM-57`/`59`/`104`), publicación protegida con censura médica (`SCRUM-60`/`105`/`106`), exclusión (`SCRUM-102`), enmienda (`SCRUM-103`), ABM de Reglamentos, Reportes, Panel Admin (`SCRUM-91`), optimización paginación/OnPush/ORM (`SCRUM-87`), Manual de Usuario (`SCRUM-129`).
- **Referencias rotas:**
  - Enlaces locales absolutos inexistentes: `file:///d:/Proyectos-mg/seminario-integrador/docs/adr/ADR-001-consumo-padron-institucional.md` (línea 373), `file:///d:/Proyectos-mg/seminario-integrador/docs/gestion-proyecto/notasPO.md` (línea 416), `file:///d:/Proyectos-mg/seminario-integrador/specs/003-monitorear-solicitudes-t01/spec.md` (línea 476).
  - Archivos inexistentes en el repo: `tokens.css`, `view-cd.js`, `view-td.js`, `view-socio.js` (línea 266), `Procesos-BPMN-SGD-AVEIT.md`, `Estudio-Inicial-SGD-AVEIT.md` (línea 272), `seed_expedientes` (líneas 581, 613).
  - Modelo inexistente: `EmailNotificationQueue` (líneas 464, 505).

---

## 7. `docs/gestion-proyecto/UAT-PR49-calendario.md`

- **Ruta:** `docs/gestion-proyecto/UAT-PR49-calendario.md`
- **Líneas:** 172
- **Última modificación:** `2026-10-10`
- **Tema que cubre:** Bitácora de pruebas de aceptación (UAT), resolución de conflictos y comandos locales del worktree para el PR #49 (Calendario institucional y servicio de notificaciones).
- **Quién lo lee:** nadie (registro efímero de verificación de un PR ya mergeado en octubre de 2026).
- **Qué pasa si desaparece:** nada (las reglas permanentes de notificaciones ya están en `AGENTS.md` y el calendario está cubierto por tests automatizados).
- **Clasificación:** **1. Residuo de fabricación** (reporte operativo efímero de una sesión de review/UAT sobre un worktree local `C:\Users\Usuario\.codex\worktrees\calendario-pr49\...`).
- **Contradicciones con el registro:**
  - Afirma *"La PR #49 permanece abierta"* / *"permanece sin merge"* (líneas 17, 57), cuando el PR #49 ya fue integrado a `main` en Sprint 3.
  - En línea 7 lista el botón de demostración `FISCALIZADORA 85194` (coherente con el enum del código, pero divergente con la terminología documental `Revisores de Cuentas`).
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna (el calendario institucional y las notificaciones toast están marcadas como `implementada` en el registro §2).
- **Funcionalidad implementada que debería cubrir y no cubre:** No aplica (era específico del PR #49).
- **Referencias rotas:**
  - Ruta local de máquina personal: `C:\Users\Usuario\.codex\worktrees\calendario-pr49\seminario-integrador` (línea 14).

---

## 8. `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`

- **Ruta:** `docs/gestion-proyecto/UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`
- **Líneas:** 181
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Plan y resultados de QA/UAT para la historia `SCRUM-50 / S3-06` (reuniones, asistencia con patrón Strategy y consolidación 3:1 de apercibimientos).
- **Quién lo lee:** nadie (acta puntual de cierre de Fase 5 de la rama `feature/US-S3-06-sanciones-reuniones-solicitudes`, ya mergeada en PR #56).
- **Qué pasa si desaparece:** nada.
- **Clasificación:** **1. Residuo de fabricación** (documento de cierre de rama puntual de Sprint 3, con datos de entorno local y rutas de test desactualizadas).
- **Contradicciones con el registro:**
  - En §2.2 (línea 44) usa `"Legajo / Identificador"` en lugar del término institucional `"Número de Socio"` adoptado en Sprint 5 (registro §3).
  - En §2.1 (línea 39) menciona *"migración `0012` aplicada"*, obsoleto frente al grafo actual de migraciones.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - Ninguna grave: cubre `SCRUM-50` y la consolidación 3:1 (`WarningAccumulationService`), que el registro (§2) marca como `implementada` (la brecha parcial de `SCRUM-61` corresponde a alertas preventivas a autoridades, no reclamadas aquí).
- **Funcionalidad implementada que debería cubrir y no cubre:** No cubre el rediseño UI posterior de Eventos y Asistencia (`SCRUM-86`, Sprint 5).
- **Referencias rotas:**
  - `test_meeting_compliance.py` y `test_warning_service.py` (líneas 150–151): no existen en el repositorio.
  - `test_evento_models.py` y `test_eventos_api.py` (líneas 149, 152): citados sin subcarpeta (en el repo están en `backend/tests/expedientes/`).

---

## 9. `docs/gestion-proyecto/notasPO.md`

- **Ruta:** `docs/gestion-proyecto/notasPO.md`
- **Líneas:** 278
- **Última modificación:** `2026-11-13`
- **Tema que cubre:** Directivas acumuladas del Product Owner (27/09/2026, 07/10/2026 y 13/11/2026) sobre lenguaje UI, reglas de negocio, formatos del TD y acuerdos de Sprint 5.
- **Quién lo lee:** equipo (y obligatoriamente todos los agentes IA en tres momentos de cada tarea, por Regla Innegociable 2 de `AGENTS.md`).
- **Qué pasa si desaparece:** alguien se equivoca / se rompe algo (es el documento rector de decisiones de producto referenciado obligatoriamente por `AGENTS.md`).
- **Clasificación:** **3. Incompleto / con contradicciones internas acumuladas** (conserva tres capas cronológicas —27/09, 07/10 y 13/11— donde varias directivas iniciales quedaron superadas o contradicen el estado real del código, mientras `AGENTS.md` prohíbe editarlo sin orden explícita del PO).
- **Contradicciones con el registro:**
  - **Rol `FISCALIZADORA` vs `Revisores` (líneas 132–134):** ordena renombrar el rol en *"todo el sistema (backend RBAC, frontend, nombres de rutas, selectores, tooltips)"*; el registro (§3) confirma que en código el enum sigue siendo `FISCALIZADORA` (`backend/socios/models.py:26-33`, `auth.service.ts:8`).
  - **Apelación sobre resoluciones vs T01 (línea 254):** afirma *"Ya funciona el circuito de apelación sobre resoluciones y el ajuste del formulario T01"*; el registro (§2) verifica que `SCRUM-70` implementa apelación y adecuación del **Formulario T01** (`T01AppealService`, `ApelacionT01`, `AdecuacionT01`), mientras que las resoluciones emitidas usan **Enmienda** (`SCRUM-103`, `EnmiendaResolucion`).
  - **Votación en tabla histórica (línea 116):** la tabla del 27/09 menciona `"Dev 4 | Sala de Tribunal: votación, suplencias y resolución"`, contradiciendo la eliminación posterior de la votación nominal (líneas 183 y 252; registro §2 y §3).
  - **Legajo vs Número de Socio (línea 197 vs línea 271):** la sección del 07/10 exige individualizar socios *"por nombre y legajo"* en `SE RESUELVE`, mientras la sección del 13/11 exige usar *"Número de Socio"* en toda la UI, notificaciones y resoluciones.
- **Afirmaciones sobre funcionalidad parcial o no implementada:**
  - **Alertas de umbrales `-10` y `-7` (líneas 82 y 263):** bajo la sección `3. Reglamentos, reportes, eventos y ranking (implementado)` afirma que *"Las alertas por puntos quedaron en -10 para el umbral crítico... y -7 para el preventivo"* y *"Implementado... la lógica de alertas"*; el registro (§2) marca `SCRUM-62` como **`parcial`** porque falta conectar `ThresholdAlertEngine` al flujo productivo (`LedgerService` / `emitir_resolucion`) y exponer endpoint/vista de alertas.
  - **Reportes (líneas 90 y 261):** los presenta como implementados (con CSV), sin reflejar que el registro (§2) los marca como **`parcial`** por faltar la exportación a **PDF** del Balance Cuatrimestral Art. 137 y por carecer 6 vistas de `reportes_views.py` de permisos de rol específicos.
- **Funcionalidad implementada que debería cubrir y no cubre:**
  - La sección del 13/11 presenta en tiempo futuro (*"Vamos a..."*, §4 línea 276) ítems que el registro (§2) ya verifica como implementados: Manual de Usuario (`SCRUM-129`), optimización de paginación/OnPush/ORM (`SCRUM-87`), rediseño de Eventos (`SCRUM-86`), Panel Admin (`SCRUM-91`), Exclusión (`SCRUM-102`) y Enmienda (`SCRUM-103`).
- **Referencias rotas:**
  - Cita `"Ref. Imagen 1"`, `"Imagen 2"` e `"Imagen 3"` (líneas 162, 169, 171, 186, 191) sin archivos de imagen ni rutas asociadas en el repositorio.
  - Cita `"Circular 001/2026"` (línea 263), no versionada en el repositorio.
- **Evaluación específica obligatoria — ¿contiene instrucciones que un agente podría seguir y que hoy son incorrectas?:**
  - **Sí.** Dado que `AGENTS.md` obliga a todo agente a contrastar su trabajo contra `notasPO.md` antes, durante y al final de cada tarea, existen instrucciones concretas que inducen a error:
    1. **Renombrar `FISCALIZADORA` en todo el código (líneas 132–134):** un agente podría renombrar el enum `Role.FISCALIZADORA` en backend/frontend, rompiendo contratos existentes, migraciones y tests.
    2. **Asumir alertas `-10`/`-7` ya operativas en producción (líneas 82 y 263):** redactadas como *"implementado"*, pueden llevar a un agente a no cablearlas ni documentarlas como parciales/trasladadas al Sprint 6.
    3. **Asumir apelación sobre resoluciones emitidas (línea 254):** induce a confundir `ApelacionT01` (sobre T01) con `EnmiendaResolucion` (sobre resoluciones emitidas).
    4. **Instrucciones viejas del 27/09 sin tachar ni marcar como obsoletas:** *"Hoy muestra un número hardcodeado"* (línea 33), *"Antes de definir los límites fijos, hay que relevar el histórico de pedidos"* (línea 64), *"Dev 4: votación, suplencias y resolución"* (línea 116), *"por nombre y legajo"* (línea 197) y *"Reportes: Están en pausa... No arrancar nada acá todavía"* (línea 88, aunque tiene nota posterior en línea 90).
    5. **Conflicto de gobernanza:** `AGENTS.md` (Regla Innegociable 5) prohíbe editar `notasPO.md` salvo orden explícita del PO, por lo que estas instrucciones desactualizadas permanecen activas como mandato para agentes.

---

## 10. `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md`

- **Ruta:** `docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md`
- **Líneas:** 308
- **Última modificación:** `2026-11-13`
- **Tema que cubre:** Relevamiento técnico previo y requisitos para implementar paginación server-side DRF y `MatPaginator` en Angular (`SCRUM-118`, épica `SCRUM-87`).
- **Quién lo lee:** nadie (documento de análisis previo a una tarea ya implementada).
- **Qué pasa si desaparece:** nada (la implementación ya existe en `backend/core/pagination.py`, `frontend/src/app/models/paginated-response.model.ts` y tests).
- **Clasificación:** **1. Residuo de fabricación** (especificación/relevamiento de trabajo previo a la implementación de una subtarea ya completada en Sprint 5; redactado en tiempo futuro/pendiente y con estado AS-IS ya superado).
- **Contradicciones con el registro:**
  - Describe en §1.1 y §1.2 un estado AS-IS *"con ausencia casi total de paginación server-side"*, `RankingListView` retornando array plano sin `MatPaginator`, y marca requisitos RF-PAG-04/05/08 y RNF-PERF-01..04 como `Pendiente`; el registro (§2) verifica `SCRUM-87` (paginación) como **`implementada`** con `backend/core/pagination.py` y suites `test_pagination.py`, `test_expediente_pagination.py`, `test_evento_pagination.py`, `test_ranking_pagination.py`.
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna (se enfoca en `SCRUM-118`, ya implementada).
- **Funcionalidad implementada que debería cubrir y no cubre:** No refleja el estado final implementado (ej. `InvalidPageError`, `PaginatedAPIViewMixin`, `spanish-paginator-intl.ts`), ya que es un documento pre-implementación.
- **Referencias rotas:**
  - Referencia a `"directiva de Addy Osmani"` (líneas 35, 251, 253) como fuente externa no versionada en el repositorio.

---

## 11. `docs/gestion-proyecto/relevamiento_scrum_119_frontend_onpush_trackby.md`

- **Ruta:** `docs/gestion-proyecto/relevamiento_scrum_119_frontend_onpush_trackby.md`
- **Líneas:** 395
- **Última modificación:** `2026-11-13`
- **Tema que cubre:** Relevamiento técnico previo y plan de refactorización Angular (`OnPush`, `trackBy` y limpieza RxJS `ngOnDestroy`) para `SCRUM-119`.
- **Quién lo lee:** nadie (documento de análisis previo a una tarea ya implementada).
- **Qué pasa si desaparece:** nada (el código `frontend/src/app/utils/track-by.util.ts` y los tests `track-by.util.spec.ts`, `lifecycle-memory.spec.ts` ya están implementados).
- **Clasificación:** **1. Residuo de fabricación** (especificación de trabajo previa a la implementación de `SCRUM-119`, con checklist DoD sin marcar `[ ]` y diagnóstico AS-IS ya superado).
- **Contradicciones con el registro:**
  - Presenta la SPA en estado AS-IS sin `OnPush` (94.4%), sin `trackBy` (92%) y con checklist DoD §6 completamente sin marcar (`[ ]`); el registro (§2) verifica `SCRUM-87` (`OnPush`, `trackBy`) como **`implementada`** con tests en `track-by.util.spec.ts` y `lifecycle-memory.spec.ts`.
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:** No refleja el resultado final implementado ni la verificación post-refactor.
- **Referencias rotas:**
  - `D:\Proyectos-mg\skills\addyOsmaniSkills\SKILL.md` (línea 244): ruta absoluta a disco local inexistente en el repositorio.

---

## 12. `docs/gestion-proyecto/relevamiento_scrum_120_optimizacion_orm.md`

- **Ruta:** `docs/gestion-proyecto/relevamiento_scrum_120_optimizacion_orm.md`
- **Líneas:** 498
- **Última modificación:** `2026-11-13`
- **Tema que cubre:** Relevamiento técnico previo y plan de optimización Django ORM (`select_related`, `Prefetch` con `defer`, anotaciones y subqueries) para `SCRUM-120`.
- **Quién lo lee:** nadie (documento de análisis previo a una tarea ya implementada).
- **Qué pasa si desaparece:** nada (la optimización y `backend/tests/expedientes/test_orm_performance.py` ya están implementados).
- **Clasificación:** **1. Residuo de fabricación** (diagnóstico y plan previo a la implementación de `SCRUM-120`, con criterios de aceptación §8 sin marcar `[ ]` y referencias a skills internos de generación como `ormMaster`, `requirementsExtractor`, `qualityScenarioSpecifier` y `backendTesting`).
- **Contradicciones con el registro:**
  - Describe como estado actual (AS-IS) los patrones N+1 (62 queries en eventos, 101 en antecedentes, carga de BLOB en listados) y deja el checklist §8 sin marcar (`[ ]`); el registro (§2) verifica `SCRUM-87` (optimización de consultas ORM) como **`implementada`** con `test_orm_performance.py`.
- **Afirmaciones sobre funcionalidad parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que debería cubrir y no cubre:** No documenta el estado final verificado tras la implementación.
- **Referencias rotas:**
  - `sistema_actual_legado_schema.sql` (línea 392): citado sin ruta relativa completa (existe en `docs/analisis-proceso-actual/sistema-actual/sistema_actual_legado_schema.sql`).
  - Nombres de skills internos (`ormMaster`, `requirementsExtractor`, `qualityScenarioSpecifier`, `backendTesting`) inexistentes como documentos en el repo.

---

## Decisiones pendientes

1. **Destino y actualización de `docs/gestion-proyecto/notasPO.md`:** Requiere decisión explícita del Product Owner (por Regla Innegociable 5 de `AGENTS.md`) sobre si se autoriza depurar/actualizar `notasPO.md` para eliminar instrucciones que hoy inducen a error a agentes IA (renombre de `FISCALIZADORA` en código, estado "implementado" de alertas `-10`/`-7` y de reportes, mención de apelación sobre resoluciones, y bloques históricos del 27/09).
2. **Fuente única de los entregables formales de cátedra (`PLAN_DE_PROYECTO_SGD_AVEIT.md` y `Seguimiento de Proyecto.md`):** Definir si las versiones Markdown dentro de `docs/gestion-proyecto/` se mantendrán sincronizadas como fuente canónica en el repositorio frente a los archivos externos (`Plan_de_Proyecto.docx`, `Seguimiento_de_ProyectoVersionSprint4.pdf` y `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`) o si se archivarán en `auditoria/archivados/` por redundancia.
3. **Unificación del número de grupo (`Grupo 13` vs `Grupo Nº 04`):** `PLAN_DE_PROYECTO_SGD_AVEIT.md` y `DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` indican `Grupo Nº 04`, mientras los entregables externos `Estudio_Inicial.docx` y `Plan_de_Proyecto.docx` indican `Grupo 13`. No se resuelve con el código; requiere confirmación del equipo.
4. **Archivo de los 7 documentos clasificados como Residuo de fabricación:** Confirmar traslado a `auditoria/archivados/` (con registro en `auditoria/archivados/LEEME.md`) de `ANALISIS_INTEGRAL_BACKLOG_JIRA.md`, `INFORME_DIVERGENCIA_MAIN_PRESENTACION.md`, `UAT-PR49-calendario.md`, `UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`, `relevamiento_scrum_118_paginacion.md`, `relevamiento_scrum_119_frontend_onpush_trackby.md` y `relevamiento_scrum_120_optimizacion_orm.md`, así como de `DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` por redundancia con la versión S4.
5. **Política sobre la referencia a `develop` en `GUIA_PULL_REQUESTS.md`:** Confirmar si el proyecto sigue usando rama `develop` o si solo utiliza `main`, para alinear la regla de protección de ramas en dicha guía vigente.
