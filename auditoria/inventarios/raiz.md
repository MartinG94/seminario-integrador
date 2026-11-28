# Inventario de Auditoría — Grupo `raiz`

> **Fecha de relevamiento:** 27/11/2026  
> **Fuente de contraste:** `auditoria/registro-canonico.md` y verificación directa en el repositorio (modo solo lectura).  
> **Archivos auditados:** 5 (`AGENTS.md`, `DESIGN.md`, `PLAN_SPRINT_5_CONSOLIDADO.md`, `README.md`, `TASK.md`).

---

## Tabla Resumen

| Ruta | Líneas | Última modificación (`git log`) | Tema que cubre (una línea) | Quién lo lee | Qué pasa si desaparece | Clasificación |
| :--- | :---: | :---: | :--- | :--- | :--- | :--- |
| `AGENTS.md` | 113 | `2026-10-15` *(modificado en working tree)* | Guía operativa obligatoria, comandos, convenciones y reglas innegociables para agentes de IA y desarrolladores. | equipo | alguien se equivoca | **4. Vigente** |
| `DESIGN.md` | 324 | `2026-11-22` | Sistema de diseño canónico institucional (tokens claro/oscuro, tipografía, componentes Material Dashboard PRO y WCAG 2.2 AA). | equipo | alguien se equivoca | **4. Vigente** |
| `PLAN_SPRINT_5_CONSOLIDADO.md` | 300 | `2026-11-05` | Plan técnico y de gestión previo a la ejecución del Sprint 5 Consolidado (8 Macro-Historias y 5 paquetes de trabajo). | nadie *(histórico del equipo)* | nada | **1. Residuo de fabricación** *(y **3. Redundante / desactualizado** frente a `TASK.md` y `specs/010`–`012`)* |
| `README.md` | 292 | `2026-09-25` | Presentación institucional del repositorio, contexto AVEIT, funcionalidades, flujo procesal, stack, estructura de carpetas y equipo. | equipo / cátedra | alguien pregunta | **3. Incompleto** *(promete ser la guía principal del repositorio y quedó desactualizado en Sprint 1)* |
| `TASK.md` | 529 | `2026-11-23` | Hoja de ruta macro de Sprints y bitácora granular de tareas atómicas ejecutadas bajo SDD. | equipo | alguien se equivoca | **3. Incompleto / desactualizado** *(tabla macro y checks con afirmaciones desalineadas respecto del código; redundante parcialmente con `specs/*/tasks.md`)* |

---

## Fichas Detalladas

### 1. `AGENTS.md`

- **Ruta:** `AGENTS.md`
- **Líneas:** 113
- **Última modificación (`git log -1 --format=%ad --date=short -- AGENTS.md`):** `2026-10-15` *(presenta modificaciones locales sin commitear en working tree correspondientes a las reglas 7 a 13 de Gobernanza de Documentación y Auditoría).*
- **Tema que cubre (una línea):** Guía operativa obligatoria, comandos, convenciones y reglas innegociables para agentes de IA y desarrolladores.
- **Quién lo lee:** equipo (desarrolladores humanos y agentes de IA).
- **Qué pasa si desaparece:** alguien se equivoca (se pierden las reglas de SDD, inmutabilidad de `notasPO.md`, cadencia de `Seguimiento de Proyecto.md`, feedback centralizado PR #49 y reglas de auditoría).
- **Clasificación:** **4. Vigente**.
- **Contradicciones con el registro:**
  - *Votación nominal colegiada:* El documento (línea 9) describe la plataforma como destinada a *"votación nominal colegiada del Tribunal de Disciplina"*. El registro canónico (§1.3 #24, §2 y §3) establece que la votación nominal individual fue **no implementada (descartada por PO el 07/10/2026)** y reemplazada por un editor unificado de resolución con firma colegiada de 3 integrantes habilitados (4.º, 5.º y 6.º año) en `Resolucion.firmantes`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Menciona *"votación nominal colegiada del Tribunal de Disciplina"* (línea 9), marcada como **no implementada (descartada por PO)** en el registro (§2).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - En su descripción general del proyecto (§1, línea 9) no refleja el mecanismo vigente de firma colegiada sin votación nominal. No corresponde que liste el catálogo completo de módulos por ser una guía operativa.
- **Referencias rotas:**
  - `auditoria/archivados/LEEME.md` (línea 98): el archivo no existe actualmente en el repositorio.
- **Específico de `notasPO`:** Aplica como regla de gobernanza: exige lectura previa (Regla 1), verificación en tres momentos —inicio, durante y cierre— (Regla 2 y §5.3) e inmutabilidad estricta de `docs/gestion-proyecto/notasPO.md` (Regla 5).

---

### 2. `DESIGN.md`

- **Ruta:** `DESIGN.md`
- **Líneas:** 324
- **Última modificación (`git log -1 --format=%ad --date=short -- DESIGN.md`):** `2026-11-22`
- **Tema que cubre (una línea):** Sistema de diseño canónico institucional (tokens claro/oscuro, tipografía, componentes Material Dashboard PRO y WCAG 2.2 AA).
- **Quién lo lee:** equipo (desarrolladores frontend y agentes de IA).
- **Qué pasa si desaparece:** alguien se equivoca (se pierden los tokens canónicos obligatorios referenciados por `AGENTS.md`, la paleta semántica claro/oscuro y las prohibiciones estrictas de UI).
- **Clasificación:** **4. Vigente**.
- **Contradicciones con el registro:**
  - *Votación colegiada / votar:* El documento menciona *"Votación colegiada"* (§2.3, línea 268) y *"Acciones directas sobre la tarjeta (revisar, votar, dictaminar)"* (§4.4, línea 308). El registro canónico (§2 y §3) confirma que no existe votación nominal (descartada por el PO) y que la decisión se instrumenta por editor unificado y firma colegiada.
  - *Número de columnas del tablero Kanban:* El documento (§4.4, línea 306) indica *"5 columnas claramente diferenciadas"*. El registro canónico (§2 y §3) confirma el ciclo procesal de **6 estados** oficiales del expediente (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`/`pendiente_firma`, `emitido`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - En §2.3 (líneas 265–266) refiere a *"Alerta preventiva (-7 puntos)"* y *"Límite crítico (-10 puntos)"*, funcionalidad marcada como **parcial** en el registro (§2: motor de dominio implementado pero no conectado al flujo productivo ni expuesto en endpoint/vista).
  - En §2.3 (línea 268) refiere a *"balance cuatrimestral"*, marcado como **parcial** en el registro (§2: falta exportación a PDF y permisos de rol en 6 vistas).
  - En §2.3 y §4.4 refiere a *"Votación colegiada"* / *"votar"*, marcada como **no implementada (descartada por PO)**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No especifica el componente ni los tokens del centro de notificaciones transitorias (`NotificationCenter`, abajo a la derecha, duración 10 s, botón X accesible, visibilidad sobre modales y `prefers-reduced-motion`) exigido por el PM en PR #49 y reglado en `AGENTS.md` (solo hay una mención genérica a *"toast notifications"* en §5, línea 318).
- **Referencias rotas:**
  - Ninguna (`frontend/src/assets/scss/core/_aveit-tribunal.scss` existe).
- **Específico de `notasPO`:** N/A.

---

### 3. `PLAN_SPRINT_5_CONSOLIDADO.md`

- **Ruta:** `PLAN_SPRINT_5_CONSOLIDADO.md`
- **Líneas:** 300
- **Última modificación (`git log -1 --format=%ad --date=short -- PLAN_SPRINT_5_CONSOLIDADO.md`):** `2026-11-05`
- **Tema que cubre (una línea):** Plan técnico y de gestión previo a la ejecución del Sprint 5 Consolidado (8 Macro-Historias y 5 paquetes de trabajo).
- **Quién lo lee:** nadie *(artefacto de planificación previa de una sesión `/grill-me` del 05/11/2026; el seguimiento efectivo quedó en `TASK.md` y `specs/010`–`012`)*.
- **Qué pasa si desaparece:** nada.
- **Clasificación:** **1. Residuo de fabricación** *(y **3. Redundante / desactualizado** frente a `TASK.md`, `specs/010-optimizacion-rendimiento/`, `specs/010-circuito-resolutivo-enmiendas/`, `specs/011-libro-mayor-mis-expedientes-publicacion/` y `specs/012-panel-administracion/`, quedando `PLAN_SPRINT_5_CONSOLIDADO.md` desactualizado respecto de lo implementado).*
- **Contradicciones con el registro:**
  - *Modelo de Libro Mayor:* El documento (líneas 38, 168, 183–185) propone `TransaccionPuntos` en `backend/ranking/models.py`. El registro canónico (§2 y §3) confirma que el código implementa `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly) y `PuntajeAplicado` (`tribunal_puntajeaplicado` legado).
  - *Estados previos a `Emitido`:* El documento (línea 37) enumera solo 4 estados (`creado`, `justificando`, `revision_resolucion`, `pendiente_firma`), omitiendo `espera_resolucion` y usando el alias visual frontend `pendiente_firma` en lugar del estado backend `pendiente_correos` (registro §3).
  - *Modelo de parámetros y guard de administración:* El documento (líneas 199–200, 216) especifica `ParametroSistema` en `backend/core/models/parametros.py` y protección de ruta con `AdminGuard`. En el código real (registro §2) existen `SystemParameterChange` y `TribunalRoleChange` en `backend/core/models.py` y se utiliza `TribunalGuard`.
  - *Estructura del Manual de Usuario:* El documento (líneas 240–247) proyecta `docs/manual-usuario/MANUAL_DE_USUARIO_SGD_AVEIT.md` con **6 capítulos**. El registro canónico (§2 y §5.5) verifica un manual modular de **9 capítulos HTML + PDFs** (`docs/manual-usuario/src/01_*.html`..`09_*.html` y `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`).
  - *Mapeo de claves Jira (`SCRUM-57` a `SCRUM-68`):* En §1 (líneas 13–15) y §3.1 (líneas 82–108), asigna `SCRUM-61` a publicación oficial protegida, `SCRUM-64` a balances cuatrimestrales, `SCRUM-65` a jurisprudencia, `SCRUM-67` a hardening/E2E y `SCRUM-68` a homologación; en el registro canónico (§2), `SCRUM-61` corresponde a alertas 3:1, `SCRUM-63` a reportes/balance Art. 137, `SCRUM-64` a reconciliación bidireccional, `SCRUM-65` a hardening/carga, `SCRUM-66` a staging, `SCRUM-67` a homologación y `SCRUM-68` a repositorio de precedentes.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Incluye dentro del alcance del Sprint 5 consolidado (*"hay que terminar para este sprint"*) ítems que el registro (§2) clasifica como **parciales**, **no implementados** o **no verificables**:
    - Exportación a PDF del Balance Cuatrimestral (`SCRUM-124` / `SCRUM-64` en el plan) — **parcial**.
    - Repositorio de jurisprudencia histórica (`SCRUM-125` / `SCRUM-65` en el plan) — **parcial**.
    - Migración y reconciliación de datos legados (`SCRUM-126` / `SCRUM-66` en el plan) — **no implementada** (`SCRUM-64` en registro) / **no verificable** (`SCRUM-66`).
    - Hardening RBAC y pruebas de carga/E2E (`N-08` / `SCRUM-67` en el plan) — **no implementada** (`SCRUM-65` en registro; 6 vistas de reportes sin permiso de rol y sin scripts de carga).
    - Verificación universal de los 10 disparadores de correo (`N-12` / `SCRUM-123`) — **no existe** `email_verification_service.py` ni dicha suite universal (registro §2).
    - Promoción de casos internos a T01 (`PB-01` / `SCRUM-128`) — **no implementada**.
    - Homologación y Staging (`SCRUM-127` / `SCRUM-68` en el plan) — **No verificable**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Al ser un documento de planificación previa nunca actualizado tras la ejecución, no refleja qué Macro-Historias fueron efectivamente implementadas ni el traspaso de pendientes al Sprint 6.
- **Referencias rotas:**
  - `backend/expedientes/models/enmienda.py` (inexistente; `EnmiendaResolucion` vive en `backend/expedientes/models.py`).
  - `backend/expedientes/views/enmienda_views.py` (inexistente; la vista vive en `backend/expedientes/resolution_views.py`).
  - `backend/core/services/email_verification_service.py` (inexistente).
  - `backend/core/models/parametros.py` (inexistente; modelos en `backend/core/models.py`).
  - `AdminGuard` (`frontend/src/app/services/admin.guard.ts` inexistente).
  - `docs/gestion-proyecto/MATRIZ_DE_PERMISOS_RBAC.md` (inexistente).
  - `backend/tests/test_rbac_permissions.py` (inexistente; existe `backend/tests/test_rbac.py`).
  - `backend/tests/test_causal_resolution.py` (inexistente; existen `backend/tests/expedientes/test_causal_resolution_api.py` y `test_causal_resolution_service.py`).
  - `backend/tests/test_exclusion_involucrado.py` (ruta incorrecta; existe en `backend/tests/expedientes/test_exclusion_involucrado.py`).
  - `backend/tests/test_enmienda_resolucion.py` (ruta incorrecta; existe en `backend/tests/expedientes/test_enmienda_resolucion.py`).
  - `docs/manual-usuario/MANUAL_DE_USUARIO_SGD_AVEIT.md` (inexistente; el manual está en `docs/manual-usuario/src/` y `docs/manual-usuario/pdfs/`).
- **Específico de `notasPO`:** N/A (documenta acuerdos de una sesión `/grill-me` con el PO, sin citar ni modificar `notasPO.md`).

---

### 4. `README.md`

- **Ruta:** `README.md`
- **Líneas:** 292
- **Última modificación (`git log -1 --format=%ad --date=short -- README.md`):** `2026-09-25`
- **Tema que cubre (una línea):** Presentación institucional del repositorio, contexto AVEIT, funcionalidades, flujo procesal, stack, estructura de carpetas y equipo.
- **Quién lo lee:** equipo y cátedra.
- **Qué pasa si desaparece:** alguien pregunta (es la portada estándar del repositorio).
- **Clasificación:** **3. Incompleto** *(promete ser la presentación y guía principal del repositorio, pero quedó congelado en Sprint 1 —25/09/2026— con contenido obsoleto y omisión de módulos y carpetas creados en Sprints 2 a 5).*
- **Contradicciones con el registro:**
  - *Votación nominal del TD:* Afirma *"deliberación y votación remota"* (línea 46), *"emitir votos nominales fundados"* (línea 86), *"Votación nominal de los miembros del TD"* (línea 99) y *"votación del TD"* en el diagrama de estados (línea 115). El registro canónico (§1.3 #24, §2 y §3) confirma que la votación nominal fue **descartada por el PO el 07/10/2026** y reemplazada por editor unificado y firma colegiada.
  - *Expresión "cómputo algorítmico":* Usa *"cómputo algorítmico"* (líneas 47 y 100), expresión observada por la cátedra en Sprint 0 (registro §1.1 #8).
  - *Metodología:* Declara *"Scrum"* (líneas 7 y 282), mientras que el registro (§1.1 #14 y §5.1–5.2) consigna la formalización de **Scrumban** (y SDD en `AGENTS.md`).
  - *Estado de `backend/` y `specs/`:* La estructura de carpetas describe `backend/` como *"(Spec 001 - En desarrollo)"* (línea 192) y lista únicamente `specs/001-walking-skeleton/` (línea 226), omitiendo el desarrollo completado hasta Sprint 5 (114 tests backend, 55 specs frontend, `specs/002` a `012`, `docs/manual-usuario/`, `docs/Implementacion IA/`, `auditoria/`).
  - *Inconsistencia interna en Balances:* Línea 102 titula *"Generador de Balances Cuatrimestrales"* pero describe *"períodos semestrales"*.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Presenta como funcionalidades del sistema sin aclarar estado real:
    - *"Votación nominal de los miembros del TD"* (líneas 46, 86, 99, 115) — **no implementada (descartada por PO)**.
    - *"Sistema de Alertas Escalonadas (7 pts preventivo y 10 pts crítico)"* (líneas 48 y 101) — **parcial** (registro §2).
    - *"Emisión instantánea de Balances Cuatrimestrales de Auditoría Interna (Art. 137)"* (líneas 49, 87, 102) — **parcial** (registro §2: sin exportación PDF y con brecha RBAC en 6 vistas).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - En §Funcionalidades Principales y §Estructura del Repositorio omite módulos implementados verificados en el registro (§2):
    - Calendario Institucional y cálculo de plazos en días hábiles (`/calendario-institucional`).
    - Gestión de Eventos, Reuniones y Asistencia (`/eventos-asistencia`).
    - ABM de Reglamentos (`/reglamentos`).
    - Apelación y adecuación de T01 (`SCRUM-70`), Visor Autorizado Unificado (`SCRUM-51`), Composición/Apartamiento/Suplencia (`SCRUM-54`), Exclusión fundada (`SCRUM-102`) y Enmienda de resoluciones (`SCRUM-103`).
    - Panel de Administración de parámetros y miembros TD (`/admin/parametros`).
    - Manual de Usuario modular (`docs/manual-usuario/`).
    - Comandos básicos de levantamiento y ejecución del proyecto (`docker compose`, tests).
- **Referencias rotas:**
  - `docs/analisis-proceso-actual/modulo-tribunal-stack-y-modelos.md` (línea 209): archivo inexistente.
  - Enlaces internos de los badges en líneas 6–10 (`#contexto-académico`, `#metodología-de-desarrollo`, `#stack-tecnológico`): no coinciden con los encabezados reales del documento (`## 🏛 Contexto Institucional (A.V.E.I.T.)`, `## 🚀 Metodología de Trabajo`, `## 💻 Arquitectura y Stack Tecnológico`).
- **Específico de `notasPO`:** N/A (no referencia `docs/gestion-proyecto/notasPO.md`).

---

### 5. `TASK.md`

- **Ruta:** `TASK.md`
- **Líneas:** 529
- **Última modificación (`git log -1 --format=%ad --date=short -- TASK.md`):** `2026-11-23`
- **Tema que cubre (una línea):** Hoja de ruta macro de Sprints y bitácora granular de tareas atómicas ejecutadas bajo SDD.
- **Quién lo lee:** equipo (desarrolladores y agentes de IA; exigido por `AGENTS.md` §4 Regla 5 y §5.4).
- **Qué pasa si desaparece:** alguien se equivoca (es el registro operativo obligatorio de avance atómico indicado por `AGENTS.md`).
- **Clasificación:** **3. Incompleto / desactualizado** *(redundante parcialmente con `specs/*/tasks.md`; su tabla de Roadmap Macro y varios casilleros `[x]` contradicen el estado verificado en el registro canónico, y omite bloques de trabajo implementados).*
- **Contradicciones con el registro:**
  - *Sprint 5 marcado como "Completado" (`SCRUM-57` a `SCRUM-62`):* El Roadmap Macro (línea 16) marca Sprint 5 como `Completado` incluyendo `SCRUM-61` y `SCRUM-62` (*"motor de alertas automáticas (7 pts y 10 pts)"*). El registro canónico (§2) clasifica tanto `SCRUM-61` (alertas 3:1) como `SCRUM-62` (alertas `-10`/`-7`) como **parciales** (motor no conectado a `LedgerService`/`emitir_resolucion`, sin endpoint/vista de alertas, y sin aviso previo al descuento en 3:1).
  - *Exportación a PDF en Reportes (`TS6-01.5`, línea 419):* Marca `[x]` incluyendo *"exportación CSV/PDF"*. El registro canónico (§2) verifica que **falta la exportación a PDF** del Balance Cuatrimestral Art. 137 (solo existen JSON y CSV).
  - *Permisos RBAC en Reportes (`TS6-01.3`, línea 417):* Marca `[x]` la restricción `CanViewReportes`. El registro canónico (§2) verifica que 6 vistas en `backend/expedientes/views/reportes_views.py` solo exigen `IsAuthenticated` sin permiso de rol específico.
  - *Modelo `TransaccionPuntos` en Sprint 1 (`T4`, línea 57):* Declara la creación del modelo `TransaccionPuntos`. En el código vigente (registro §2 y §3), el libro mayor usa `AsientoLibroMayor` y `PuntajeAplicado`.
  - *Inconsistencia interna en Sección 19 (`SCRUM-89`, línea 483):* Indica `Estado: Plan Aprobado con PO (12/11/2026) — Listo para Inicio`, pero todas las tareas `T10.1` a `T10.8` figuran marcadas `[x]`.
  - *Estructura de Sprints 5 y 6:* El Roadmap Macro (líneas 16–17) mantiene Sprint 5 (20 SP) y Sprint 6 (24 SP) como iteraciones separadas sin reflejar la fusión en Sprint 5 Consolidado (44 SP / 36 SP netos) ni el traspaso formal de pendientes al Sprint 6 registrado en el registro canónico (§1.4 #30 y §5.3).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Marca Sprint 5 completo con `SCRUM-61` y `SCRUM-62` y todos los ítems `TS5-06.1` a `TS5-06.4` como `[x]` (líneas 16 y 424–432), cuando el registro (§2) marca las alertas `-10`/`-7` y 3:1 como **parciales**.
  - Marca `TS6-01.5` como `[x]` afirmando *"exportación CSV/PDF"* (línea 419), cuando el registro (§2) marca el Balance Cuatrimestral Art. 137 como **parcial** por falta de exportación PDF.
  - Marca `TS6-01.3` como `[x]` afirmando RBAC en reportes (línea 417), cuando el registro (§2) marca RBAC como **parcial** por 6 vistas de reportes sin permiso de rol.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No incluye secciones de desglose atómico para funcionalidades verificadas como implementadas en el registro (§2):
    - ABM de Reglamentos (`backend/expedientes/views/reglamento_views.py`, `frontend/src/app/reglamentos/`).
    - Rediseño UI de Eventos de Sprint 5 (`SCRUM-86` / `MACRO-04`; solo registra el bloque original `SCRUM-50` de Sprint 3).
    - Estandarización de Número de Socio y atomicidad de tablas (`SCRUM-93` / `MACRO-05`).
    - Manual de Usuario modular (`SCRUM-129`).
- **Referencias rotas:**
  - `backend/tests/expedientes/test_meeting_compliance.py` (línea 221): archivo inexistente.
  - `backend/tests/expedientes/test_warning_service.py` (línea 223): archivo inexistente.
  - `backend/tests/expedientes/test_meeting_notice_service.py` (línea 225): archivo inexistente.
  - `backend/expedientes/serializers.py` (línea 257): inexistente como archivo (el módulo es el paquete `backend/expedientes/serializers/`).
  - `backend/expedientes/views.py` (línea 258): inexistente como archivo (el módulo es el paquete `backend/expedientes/views/`).
  - `backend/expedientes/migrations/0017_auditoria_consulta_expediente.py` (línea 327): inexistente (la migración `0017` real es `0017_apelacion_adecuacion_t01.py`).
  - `backend/expedientes/migrations/0020_expediente_concepto.py` (línea 415): inexistente (la migración `0020` real es `0020_expediente_titulo.py`).
  - Migración `0026` atribuida a `puntaje_ratificado` (línea 485): la migración `0026` real es `0026_valoracion_t03_y_expedientes_referenciados.py`.
- **Específico de `notasPO`:** Aplica solo como referencia de verificación (citado en tareas cerradas como punto de contraste sin alterar su contenido).

---

## Decisiones pendientes

1. **Destino de `PLAN_SPRINT_5_CONSOLIDADO.md`:** Definir si se archiva en `auditoria/archivados/` como residuo de planificación previa de Sprint 5 (respetando la Regla 9 de `AGENTS.md` de no borrar archivos) o si se conserva en raíz con advertencia explícita de estado histórico.
2. **Alcance y rol de `TASK.md` frente a `specs/*/tasks.md` y `auditoria/traspaso-sprint6.md`:** Definir si `TASK.md` debe mantenerse como espejo consolidado del Roadmap Macro y de todas las specs o acotarse exclusivamente al índice de tareas activas del sprint en curso para evitar divergencias con el registro canónico.
3. **Actualización de `README.md` para presentación de regularidad:** Definir si `README.md` será actualizado al estado real de Sprint 5 / traspaso Sprint 6 (eliminando menciones a votación nominal, actualizando árbol de carpetas y agregando comandos de ejecución) como parte de los entregables presentables ante la cátedra.
4. **Cobertura de notificaciones globales PR #49 en `DESIGN.md`:** Definir si la especificación visual del centro de notificaciones (toasts de 10 s abajo a la derecha) se incorpora formalmente a `DESIGN.md` o permanece únicamente como regla operativa en `AGENTS.md`.
5. **Creación de `auditoria/archivados/LEEME.md`:** Referenciado en `AGENTS.md` (Regla 9) pero todavía inexistente en el repositorio; definir en qué paso de la auditoría se inicializa.
