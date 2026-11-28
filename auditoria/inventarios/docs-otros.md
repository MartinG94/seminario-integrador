# Inventario de Auditoría — Grupo `docs-otros`

> **Fecha de auditoría:** 27/11/2026  
> **Modo:** Solo lectura sobre código, git y `auditoria/registro-canonico.md`.  
> **Alcance:** 6 documentos exactos del grupo `docs-otros`.

---

## Resumen

| Ruta | Líneas | Última modif. | Quién lo lee | Qué pasa si desaparece | Clasificación |
|---|---:|---|---|---|---|
| `docs/constitution.md` | 12 | 2026-09-08 | equipo | alguien se equivoca | 2. Pocas líneas (solapamiento parcial con `AGENTS.md`, donde `constitution.md` queda desactualizado) |
| `docs/adr/ADR-001-consumo-padron-institucional.md` | 189 | 2026-09-23 | equipo / cátedra | alguien se equivoca | 4. Vigente (con desactualizaciones puntuales frente al código actual) |
| `docs/adr/README.md` | 26 | 2026-09-23 | equipo / cátedra | alguien pregunta | 2. Pocas líneas / 3. Incompleto (solo indexa `ADR-001`) |
| `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md` | 161 | 2026-09-25 | equipo | alguien se equivoca | 3. Incompleto / parcialmente no implementado (Método 2 OAuth 2.0 no implementado en backend) |
| `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` | 76 | 2026-11-02 | equipo / usuario final (Cómputos) | alguien pregunta / alguien se equivoca | 3. Redundante con el Panel de Administración TD (`SCRUM-91`, `/admin/parametros`); este documento queda desactualizado |
| `docs/design/ranking-socios/README.md` | 60 | 2026-10-25 | nadie | nada | 1. Residuo de fabricación |

---

## 1. `docs/constitution.md`

- **Ruta:** `docs/constitution.md`
- **Líneas:** 12
- **Última modificación:** `2026-09-08`
- **Tema que cubre:** Principios innegociables de gobernanza técnica, normativa y terminológica del proyecto SGD-AVEIT bajo metodología SDD.
- **Quién lo lee:** equipo (referenciado como lectura obligatoria en `AGENTS.md`, `README.md`, `specs/` y documentos de gestión/relevamiento).
- **Qué pasa si desaparece:** alguien se equivoca (se pierde la definición formal de Principio 8 `Pasivo`/`Activo` vs. vigencia, el requisito WCAG 2.2 AA y el umbral del 80% de cobertura, además de quedar referencias rotas en `AGENTS.md`, `README.md` y `specs/`).
- **Clasificación:** `2. Pocas líneas` (pese a sus 12 líneas, sigue siendo citado como documento rector y su eliminación induciría errores) con solapamiento parcial tipo `3. Redundante con AGENTS.md` (donde `docs/constitution.md` queda desactualizado respecto a `AGENTS.md` en la excepción de nomenclatura del esquema legacy).
- **Contradicciones con el registro:**
  - **Principio 4** menciona *"control de mayorías"* dentro de la lógica jurídica y procesal; el registro canónico (§1.3 #24, §2 y §3) indica que la votación nominal fue descartada por el PO el 07/10/2026 y reemplazada por firma colegiada de 3 integrantes habilitados (4.º, 5.º y 6.º año) en `Resolucion.firmantes`.
  - **Principio 7** exige que todas las tablas y migraciones estén en inglés sin excepción; el registro canónico (§2 y §3) y el código vigente mantienen nombres en español en tablas legadas (`socio_lista`, `tribunal_puntajeaplicado`) y en tablas del propio sistema (`expedientes_asiento_libro_mayor`, `expedientes_descargo`, `core_parametro_sistema`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **Principio 4** (*"alertas escalonadas"*) y **Principio 6** (*"umbrales de alarma: 7 puntos preventiva, 10 puntos crítica de pérdida automática de condición de socio según el Art. 93 del Reglamento Interno"*): el registro canónico (§2) clasifica las alertas automáticas por umbrales críticos `-10` y preventivos `-7` (`SCRUM-62` / `US-17`) como **parcial** (el motor existe en `backend/ranking/domain/threshold_alerts.py`, pero falta conectarlo a `LedgerService`/`emitir_resolucion` y exponer endpoint/vista de alertas).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Por su naturaleza de constitución de principios generales, no enumera módulos; sin embargo, no refleja el principio de respeto prioritario al esquema de base de datos legacy ni la definición vigente de firma colegiada por los 3 años sociales activos (4.º, 5.º y 6.º) sin votación nominal.
- **Referencias rotas:** Ninguna (`specs/` y `DESIGN.md` existen en la raíz del repositorio).

---

## 2. `docs/adr/ADR-001-consumo-padron-institucional.md`

- **Ruta:** `docs/adr/ADR-001-consumo-padron-institucional.md`
- **Líneas:** 189
- **Última modificación:** `2026-09-23`
- **Tema que cubre:** Decisión arquitectónica (ADR-001) de acceso de sólo lectura al padrón institucional MySQL mediante Capa Anticorrupción (Arquitectura Hexagonal) en `backend/padron/`.
- **Quién lo lee:** equipo / cátedra (citado directamente en docstrings de `backend/padron/adapters.py`, `domain.py`, `factory.py`, `models.py`, `ports.py`, `services.py`, además de `specs/005-sanciones-reuniones-solicitudes/spec.md` y `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Qué pasa si desaparece:** alguien se equivoca (se pierde la documentación de la trampa semántica `socio_estado` vs. `category`, el manejo del valor centinela `codSubcomision = 99`, las reglas de transformación de `legajo`/`dni`/`email`/`membership_status` y la justificación de no duplicar tablas ni alterar el DDL legado; además quedan citas huérfanas en 6 archivos de `backend/padron/`).
- **Clasificación:** `4. Vigente` (con desactualizaciones puntuales respecto al estado actual del código y del producto).
- **Contradicciones con el registro:**
  - **§4.1 ítem 1 (línea 109):** afirma que `get_by_id` es consumido por los módulos de *"Expedientes (Sprint 2), Ranking (Sprint 1) y **Votación (Sprint 4)**"*. El registro canónico (§1.3 #24, §2 y §3) establece que la votación nominal fue descartada por el PO el 07/10/2026 y no existe módulo de votación.
  - **§6 (`LOW-001`, líneas 171–174):** afirma que `backend/core/settings.py` define `"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "3"))` y `"read_timeout": int(os.getenv("DB_READ_TIMEOUT", "3"))` para *fail-fast* a los 3 segundos. En el código vigente (`backend/core/settings.py:124-125`), ambos valores por defecto son `"60"` segundos.
  - **§4 (línea 78):** documenta `list_socios(filtros: Dict) -> List[SocioInstitucionalDTO]`, mientras que el código vigente (`backend/padron/ports.py:44-53`) recibe argumentos tipados individuales (`search`, `subcomision_id`, `category`, `is_active`, `membership_status`, `page`, `page_size`) y retorna `PaginatedSociosDTO`.
  - **§6 (`BLK-003` y `LOW-002`, líneas 165–170):** describe en tiempo futuro conflictos pendientes con la rama `SCRUM-38` (`backend/ranking/models.py` con modelos duplicados `Socio`, `Subcomision`, `SocioEstudio` y enums `"ACTIVO"`/`"PASIVO"`), conflicto ya resuelto en `main` (`backend/ranking/models.py` solo define `PuntajeGeneral` y `PuntajeAplicado`).
  - **§7 (línea 189):** mantiene la aprobación del Product Owner como *"Pendiente de homologación formal en Sprint Review"* sin fecha de cierre.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Menciona en §4.1 ítem 1 el módulo de **"Votación (Sprint 4)"**, que el registro canónico (§2) marca como **no implementada (descartada por PO)**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - `PaginatedSociosDTO` (paginación SQL nativa en `PadronRepositoryInterface.list_socios`, `backend/padron/domain.py:87`) y `DbTribunalConditionProvider` (`backend/padron/adapters.py:848`) no figuran en el diagrama ni en la especificación del puerto de §4.
- **Referencias rotas:**
  - Referencia en §6 (`BLK-003` y `LOW-002`) a modelos duplicados `Socio`, `Subcomision`, `SocioEstudio` y enums en español dentro de `backend/ranking/models.py` (rama histórica `SCRUM-38`), ya inexistentes en el archivo actual.
  - El resto de rutas, clases y endpoints citados (`backend/padron/`, `PadronRepositoryInterface`, `DatabasePadronAdapter`, `MockPadronAdapter`, `SocioInstitucionalDTO`, `SubcomisionDTO`, `HealthStatusDTO`, `SocioCategoryEnum`, `MembershipStatusEnum`, `PASSIVE_SOCIAL_YEARS`, `ACTIVE_SOCIAL_YEARS`, `logging.getLogger('padron.adapter')`, `/api/v1/padron/health/`, `backend/core/settings.py`) existen en el código.

---

## 3. `docs/adr/README.md`

- **Ruta:** `docs/adr/README.md`
- **Líneas:** 26
- **Última modificación:** `2026-09-23`
- **Tema que cubre:** Índice cronológico y estructura estándar MADR del directorio de Decisiones de Arquitectura (`docs/adr/`).
- **Quién lo lee:** equipo / cátedra.
- **Qué pasa si desaparece:** alguien pregunta (se pierde el índice del directorio y la plantilla MADR acordada).
- **Clasificación:** `2. Pocas líneas` (índice y guía de estructura) y `3. Incompleto` (promete contener el *"registro cronológico y formal de las Decisiones Arquitectónicas de Relevancia adoptadas para la plataforma"*, pero únicamente lista `ADR-001` del 19/09/2026).
- **Contradicciones con el registro:** Ninguna.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No registra ADRs para decisiones arquitectónicas adoptadas después del 19/09/2026 que sí están implementadas según el registro canónico (§2 y §3): eliminación de votación nominal y firma colegiada, patrón Transactional Outbox de notificaciones (`backend/notifications/`), libro mayor inmutable `InsertOnlyModel` (`AsientoLibroMayor` + `PuntajeAplicado`), patrón Strategy para asistencia a eventos (`SCRUM-50`), ni gestión auditable de parámetros y roles TD (`SCRUM-91`).
- **Referencias rotas:** Ninguna (`ADR-001-consumo-padron-institucional.md` existe en el mismo directorio).

---

## 4. `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md`

- **Ruta:** `docs/configuracion/GUIA_CONFIGURACION_GMAIL.md`
- **Líneas:** 161
- **Última modificación:** `2026-09-25`
- **Tema que cubre:** Instructivo para configurar el despacho de correos con Gmail / Google Workspace vía SMTP (App Password) o Google Cloud Console (OAuth 2.0) y verificar el endpoint de notificaciones.
- **Quién lo lee:** equipo (referenciado explícitamente desde `.env.example:49`).
- **Qué pasa si desaparece:** alguien se equivoca (al configurar las variables `.env` de correo SMTP y verificar el despacho local, además de quedar rota la referencia en `.env.example:49`).
- **Clasificación:** `3. Incompleto` / parcialmente no implementado (el Método 1 SMTP y la prueba `curl` coinciden con el backend, pero el Método 2 OAuth 2.0 / Gmail API describe una integración no implementada en el código).
- **Contradicciones con el registro:**
  - **§1 (línea 16) y §3 (líneas 50–110):** afirman que el **Método 2: Google Cloud Console (OAuth 2.0 / Gmail API)** es una alternativa compatible con el backend usando `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `GOOGLE_REFRESH_TOKEN`. En el código real (`backend/core/settings.py:240-242`), esas tres variables solo están declaradas en `settings.py` y no son consumidas en ningún módulo; `backend/notifications/services.py` utiliza únicamente `django.core.mail.EmailMultiAlternatives` (SMTP estándar).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - El registro canónico (§2) marca *Notificaciones transaccionales* como **implementada** (Outbox + reintentos + `process_email_queue`), pero no respalda la existencia de un adaptador OAuth 2.0 / Gmail API ni de un callback OAuth de Google.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - `POST /api/v1/notifications/email/retry/` (`RetryEmailQueueView`), la autorización alternativa por usuario administrador (`HasInternalServiceKeyOrAdmin`) y el soporte de `idempotency_key` en `POST /api/v1/notifications/email/` no aparecen documentados en §5.
- **Referencias rotas:**
  - `http://localhost:8000/api/v1/auth/google/callback/` (línea 90): **endpoint inexistente** en `backend/`.
  - `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (líneas 132–134): variables definidas en `backend/core/settings.py:240-242` sin ningún consumidor en el código.
  - El resto de referencias (`EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_TIMEOUT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, `INTERNAL_SERVICE_KEY`, `X-Internal-Service-Key`, `/api/v1/notifications/email/`, `notifications_email_outbox`, `process_email_queue`) existen en el código.

---

## 5. `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md`

- **Ruta:** `docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md`
- **Líneas:** 76
- **Última modificación:** `2026-11-02`
- **Tema que cubre:** Procedimiento manual de la Subcomisión de Cómputos (`Role.ADMIN`) para habilitar y revocar temporalmente miembros de un Tribunal de Disciplina ad-hoc mediante SQL directo.
- **Quién lo lee:** equipo / usuario final (administradores de la Subcomisión de Cómputos).
- **Qué pasa si desaparece:** alguien pregunta / alguien se equivoca (no tiene referencias entrantes en el repositorio, pero cubre el caso de Tribunal ad-hoc por Asamblea; a la vez, seguirlo hoy induce a ejecutar SQL manual sin auditoría sobre `socios_socio` y usando la columna equivocada).
- **Clasificación:** `3. Redundante` con la gestión de miembros TD del Panel de Administración (`SCRUM-91` / `MACRO-03`, `backend/core/services/tribunal_members.py`, `frontend/src/app/pages/admin/parametros/`); **`docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md` queda desactualizado** en todo lo referido a `socios_socio` (conserva contenido no cubierto por el panel únicamente en los `UPDATE` sobre la base legada externa `socio_lista.idTipoSocio`).
- **Contradicciones con el registro:**
  - **§2.B (líneas 35–44) y §4 (líneas 68–72):** instruyen modificar el rol `TD` mediante SQL directo `UPDATE socios_socio SET role = 'TD' WHERE legajo = '<NRO_SOCIO>'` (y `SET role = 'SOCIO'` al revocar). Esto contradice dos puntos del registro canónico y del código:
    1. El registro canónico (§3, *"Identificador de Socio"*) y `backend/socios/models.py:46-47` diferencian `numero_socio` de `legajo`; la consulta SQL compara `legajo` contra `<NRO_SOCIO>`.
    2. El registro canónico (§2) marca como **implementada** la gestión de miembros TD desde el Panel de Administración (`SCRUM-91` / `MACRO-03`, `TribunalMemberService.assign/revoke`, auditoría inmutable `TribunalRoleChange` en `core_cambio_rol_tribunal`), lo cual reemplaza la edición manual de `socios_socio`.
  - **§3 (líneas 52 y 54):** referencia los códigos de estado en mayúsculas (`PENDIENTE_CORREOS`, `EMITIDO`), mientras que el registro canónico (§3) y `EstadoExpedienteEnum` (`backend/expedientes/models.py:28-36`) usan valores en minúsculas (`pendiente_correos`, `emitido`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - El flujo implementado en `/admin/parametros` (`GET/POST /api/v1/admin/usuarios-td/`, `DELETE /api/v1/admin/usuarios-td/<socio_id>/`) y el registro de auditoría `core_cambio_rol_tribunal` (`TribunalRoleChange`).
- **Referencias rotas:**
  - No hay archivos ni tablas inexistentes (`socio_lista`, `socios_socio`, `Role.ADMIN`, `Role.TD`, `expedientes_composicion_tribunal`, `expedientes_integrante_composicion` e `InsertOnlyModel` existen en el código/esquema), aunque el predicado `WHERE legajo = '<NRO_SOCIO>'` cruza dos columnas distintas de `socios_socio`.

---

## 6. `docs/design/ranking-socios/README.md`

- **Ruta:** `docs/design/ranking-socios/README.md`
- **Líneas:** 60
- **Última modificación:** `2026-10-25`
- **Tema que cubre:** Guía de transferencia (handoff) de maquetas visuales generadas con Stitch MCP / Better Design para el rediseño de la pantalla `ranking-socios`.
- **Quién lo lee:** nadie (sin referencias entrantes en el repositorio; fue redactado como guía previa a la implementación de una vista ya construida).
- **Qué pasa si desaparece:** nada (la vista `frontend/src/app/ranking-socios/` ya está implementada con tests en `ranking-socios.component.spec.ts` y evolucionó más allá de esta maqueta).
- **Clasificación:** `1. Residuo de fabricación` (artefacto temporal de diseño/handoff generado durante la creación de mockups; no es arquitectónico ni formal, ni sirve a contenido presentable).
- **Contradicciones con el registro:**
  - **§2.2 ítem 6 (línea 31):** refiere a *"socios Juniors de 1.° y 2.° año social"*. El registro canónico (§3, *"Categorías de Socio"*) y el código (`backend/socios/models.py:21-23`, `backend/padron/domain.py:17-27`) establecen las categorías `PASSIVE` (*Pasivo*, años sociales **1, 2 y 3**) y `ACTIVE` (*Activo*, años sociales **4, 5 y 6**).
  - **§2.2 ítem 3 (línea 28):** describe `N° de Socio` como *"Legajo numérico"*, contradiciendo la distinción `numero_socio` vs. `legajo` del registro canónico (§3).
  - **§2.3 (línea 36):** declara la constante fija `RANKING_THRESHOLDS = { cese: -10, alerta: -7 }`; en el código vigente (`frontend/src/app/ranking-socios/ranking-thresholds.ts`), los umbrales se leen dinámicamente vía `ParametrosVigentesService` con fallback `UMBRALES_INICIALES = { critico: -10, preventivo: -7, preventivoActivo: false }` (el umbral preventivo es configurable y puede estar desactivado).
  - **§2.2 ítem 8 (línea 33) y §3 ítem 3 (línea 60):** indican un único diálogo por fila (`ExpedientesSocioDialogComponent`); el código actual (`frontend/src/app/ranking-socios/ranking-socios.component.ts:202,217`) integra además `SocioLegajoDialogComponent` (Legajo Integral).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Consumo dinámico de umbrales desde `/api/v1/parametros/umbrales/` (`SCRUM-91`), modal de Legajo Integral (`SocioLegajoDialogComponent`) y optimizaciones `OnPush` / `TrackByUtils` (`SCRUM-87`).
- **Referencias rotas:**
  - `RANKING_THRESHOLDS` (línea 36): **símbolo inexistente** en `frontend/src/app/ranking-socios/` (reemplazado por `UMBRALES_INICIALES` en `ranking-thresholds.ts`).
  - Los demás archivos y símbolos mencionados (`ranking-socios-mockup.png`, `ranking-socios-mockup.html`, `DESIGN.md`, `docs/gestion-proyecto/notasPO.md`, `ExpedientesSocioDialogComponent`, `.row-alerta`, `.row-cese`) existen en el repositorio.

---

## Decisiones pendientes

1. **`docs/constitution.md`:** Definir si se mantiene como archivo rector separado frente a `AGENTS.md` (resolviendo las divergencias en "control de mayorías" y nomenclatura en inglés de tablas) o si se unifica la gobernanza en un único documento.
2. **`docs/adr/ADR-001-consumo-padron-institucional.md`:** Definir si se conserva como registro histórico inmutable de septiembre 2026 o si se actualiza/adenda para reflejar el cierre de aprobación del PO, los defaults reales de timeout (`60` vs. `3` s en `backend/core/settings.py`), la firma paginada de `list_socios` y la eliminación de la referencia al módulo descartado *"Votación (Sprint 4)"*.
3. **`docs/adr/README.md`:** Definir si el directorio `docs/adr/` incorporará ADRs para las decisiones arquitectónicas posteriores a `ADR-001` (firma colegiada sin votación, Outbox de notificaciones, libro mayor `InsertOnlyModel`, Strategy de eventos, panel de parámetros/TD) o si quedará acotado al registro actual.
4. **`docs/configuracion/GUIA_CONFIGURACION_GMAIL.md`:** Definir si el Método 2 (Google Cloud Console OAuth 2.0 / Gmail API y `/api/v1/auth/google/callback/`) corresponde a alcance pendiente para Sprint 6 o si queda fuera del alcance del sistema.
5. **`docs/configuracion/PROCEDIMIENTO_COMPUTOS_TD_ADHOC.md`:** Definir si el procedimiento se reemplaza por la operatoria del Panel de Administración (`/admin/parametros`, `SCRUM-91`) para el rol `TD` en `socios_socio` y si la intervención manual sobre `socio_lista.idTipoSocio` sigue siendo requerida en el entorno de AVEIT.
6. **`docs/design/ranking-socios/README.md`:** Definir el archivo/traslado a `auditoria/archivados/` de este `README.md` (y sus maquetas `ranking-socios-mockup.png` y `ranking-socios-mockup.html`) al tratarse de un residuo de fabricación ya superado por la implementación.
