# Conflictos y Pendientes de Resolución — SGD-AVEIT

> **Regla:** Todo conflicto que no se resuelva automáticamente con el orden de autoridad (`código y tests > auditoria/registro-canonico.md > resto de la documentación`) se registra aquí sin elegir unilateralmente.

---

## 2026-11-27 — Desfasajes detectados en el chequeo contra Jira (`SCRUM`)

1. **`SCRUM-62` (Alertas umbral `-10` / `-7`):**
   - **Conflicto:** En Jira figura `Finalizado` (`05/11/2026`), pero en el código (`backend/ranking/domain/threshold_alerts.py`) el motor no está invocado desde `LedgerService` ni desde la emisión de resoluciones.
   - **Estado actual por orden de autoridad:** Se mantiene en [`traspaso-sprint6.md`](traspaso-sprint6.md) como parcial / trasladada al Sprint 6.
   - **Pendiente:** Confirmar con el equipo/PO si se reabre `SCRUM-62` o se crea un ticket de integración para Sprint 6.

2. **División del rol `FISCALIZADORA` en `AUTORIDAD_SC` y `REVISORES` + vista `403` (`SCRUM-92` / `SCRUM-121` / `SCRUM-122`):**
   - **Conflicto:** En Jira (`SCRUM-121` y `SCRUM-122`, `Por hacer` bajo `SCRUM-92` en `Testing-Calidad`) se especifica reemplazar `Role.FISCALIZADORA` por `AUTORIDAD_SC` y `REVISORES` (con migración en `backend/socios/models.py`) y agregar una página dedicada de error `403` en Angular; en el código del repositorio sigue vigente `Role.FISCALIZADORA` (`backend/socios/models.py` y `auth.service.ts`), mientras que el Manual de Usuario muestra `REVISORES` y `Seguimiento §2.5.2` menciona el renombre.
   - **Resolución (`2026-11-27`, D-02):** Se mantiene `FISCALIZADORA` como rol vigente en la versión actual del sistema/documentación y se traslada formalmente la partición en `AUTORIDAD_SC` + `REVISORES` (y vista `403`) al Sprint 6 en [`traspaso-sprint6.md`](traspaso-sprint6.md).

3. **Ítems de `Seguimiento S4` eliminados de Jira sin reemplazo explícito:**
   - **Conflicto:** Al reestructurar el tablero en `MACRO-01`–`MACRO-08` el `05/11/2026`, desaparecieron de Jira los tickets `SCRUM-61` (alerta preventiva por acumulación de apercibimientos 3:1) y las pruebas de carga (`50 usuarios`, `p95 ≤ 500 ms / 1.5 s`, antes en `SCRUM-65`), sin quedar cubiertos en las subtareas `SCRUM-99`–`SCRUM-129`.
   - **Pendiente:** Confirmar si ambos ítems pasan formalmente al Sprint 6 con nuevos tickets o si se descartan de común acuerdo con el PO.

4. **Tickets antiguos eliminados y consolidados bajo `MACRO-08` (`SCRUM-97`):**
   - **Referencia:** `SCRUM-63` (parte PDF), `SCRUM-64`, `SCRUM-66`, `SCRUM-67` y `SCRUM-68` fueron eliminados de Jira y consolidados en `SCRUM-124` (Balance PDF), `SCRUM-125` (Jurisprudencia), `SCRUM-126` (Migración/Reconciliación) y `SCRUM-127` (Staging/Homologación), todos en estado `Por hacer`.
   - **Pendiente:** Sincronizar los IDs de Jira en la documentación de Seguimiento cuando se actualice el cierre de Sprint 5 / apertura de Sprint 6.

5. **Desincronización administrativa de estados en Jira respecto al código ya integrado:**
   - `SCRUM-129` (Manual de Usuario) figura `Por hacer` en Jira, aunque ya fue entregado en `docs/manual-usuario/` (commit `6a60167` del `23/11/2026`).
   - `SCRUM-89` (`MACRO-01`), `SCRUM-59` (`MACRO-02`) y `SCRUM-91` (`MACRO-03`) figuran `Finalizado`, pero sus subtareas (`SCRUM-99` a `SCRUM-109`) permanecen `Por hacer`.
   - `SCRUM-86` (`MACRO-04`, rediseño Eventos) figura `En curso` con `SCRUM-110` a `SCRUM-113` en `Por hacer`, y `SCRUM-93` (`MACRO-05`) figura `En curso` con `SCRUM-116` y `SCRUM-117` en `Testing-Calidad`, aunque ambos ya están implementados e integrados en `main`.
   - **Pendiente:** Actualizar los estados administrativos del tablero Jira para alinearlos con el estado real del repositorio.

---

## 2026-11-27 — Pendientes de la ejecución de edición controlada (D-03)

6. **Entregables binarios en Word (`docs/formales/Estudio_Inicial.docx` y `docs/formales/Plan_de_Proyecto.docx`):**
   - **Estado:** Aprobados en 3A de `propuesta-destinos.md` para conservar y completar, pero no editados programáticamente para no corromper estilos, carátulas ni tablas nativas de Word y porque requieren integración manual con las versiones humanas más recientes (`v1.5.0` / `v2.0.0`).
   - **Pendiente:** Actualizar manualmente en Microsoft Word/LibreOffice alineando los 6 estados canónicos, firma colegiada sin votación nominal, categorías `Pasivo` (1.º–3.º) / `Activo` (4.º–6.º), vigencia de `FISCALIZADORA` en Sprint 5 y funcionalidades trasladadas al Sprint 6, preservando inmutables las fechas de versiones ya presentadas (Regla 13).

7. **Documentos no aprobados (`[ ]`) en `auditoria/propuesta-destinos.md` (sin modificar por respeto al alcance aprobado):**
   - `docs/manual-usuario/*` (10 archivos; `docs/manual-usuario/README.md` conserva rutas locales `G:\My Drive\...` y el manual menciona `REVISORES` en lugar de `FISCALIZADORA`).
   - `.github/ISSUE_TEMPLATE/tarea_sprint.md`.
   - `specs/010-optimizacion-rendimiento/memory_audit_report.md`.
   - Los 15 archivos `specs/*/tasks.md` del bloque 7B.
   - **Pendiente:** Definir en una próxima pasada si se aprueban sus destinos en `propuesta-destinos.md`.

8. **Cuarentena de archivos 6B (`auditoria/archivados/cuarentena/`):**
   - Los 11 archivos del bloque 6B fueron movidos a cuarentena (sin borrado, conforme a la Regla 9 de `AGENTS.md`).
   - **Pendiente:** Evaluar su disposición definitiva tras un sprint completo sin reclamos.
