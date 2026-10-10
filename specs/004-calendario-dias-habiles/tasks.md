# Tareas — Spec 004: SCRUM-45 / S3-01 (Calendario institucional de días hábiles)

## Correcciones autorizadas por el PO — PR #49

- [x] **R1. Calendario operativo único y migración auditable:** Importar inhábiles vigentes preservando auditoría y evidencia histórica; validar integridad y congelamiento de deadlines. Corregir exclusivamente las fechas oficiales de la carga inicial aprobadas por el usuario.
- [x] **R2. API y cómputo unificados (TDD):** Lectura autenticada sin versiones, alta ADMIN/CD/TD, fecha >= hoy institucional, autoría del servidor, duplicados controlados y proveedor común para simulador y expedientes.
- [x] **R3. UX/UI simplificada (TDD):** Crear Feriado, orden por Fecha, Año/Mes, auditoría visible, sin tipo/condición/versiones y tokens canónicos. Descartar simulaciones obsoletas durante un alta y conservar fechas de calendario en otras zonas horarias.
- [x] **R4. Regresión, auditoría de par y entorno UAT:** Backend 505/505, frontend 153/153, dominio 99%, build y Ruff en verde; migraciones sin drift. Auditoría cerrada, chequeo PO y localhost disponible. Lint Angular limitado por builder TSLint ausente, documentado en la guía UAT.
- [x] **R5. Ajustes visuales de UAT:** Mantener Año y Mes en la misma fila y alinear las etiquetas e inputs del simulador en escritorio. Verificar 320/393 px, suite frontend 153/153, compilación y revisión de par sin hallazgos. UAT aprobada por el usuario el 10/10/2026.

## Segunda review del PM — PR #49

- [x] **R6. Actualización y reaplicación segura (TDD):** Ocho casos de importación/migración en MySQL aislado; recorridos 0008→0010 y rollback/reaplicación, auditoría intacta y GET sembrado/vacío. HTTP real 200 para los cinco roles; migraciones históricas conservadas.
- [x] **R7. Presentación y recuperación (TDD):** Alta blanca con radio de 8 px, controles y botones alineados con estilo institucional, estados centrados fuera del scroll de tabla y reintento real. Bloquear altas mientras la carga está pendiente/fallida para evitar mostrar un calendario parcial.
- [x] **R8. Regresión y auditoría final:** Backend 510/510, frontend 156/156, build/Ruff y migraciones en verde; DESIGN.md lint con 0 errores. Auditoría sin hallazgos, viewports 1306/768/393/320 px y recuperación por Reintentar verificados. Localhost activo; UAT aprobada por el usuario el 10/10/2026.

## Implementación original (antecedente)

- [x] **T1. Modelos ORM y Dominio de Calendario:** Implementar los modelos `CalendarioVersion` y `FeriadoExcepcion` en `backend/expedientes/models.py` con sus enums, restricciones de unicidad y auditoría (CA2). Vincular `Expediente.calendario_version` con ForeignKey protegida (CA3).
- [x] **T2. Adaptador de Infraestructura y Cálculo de Plazos:** Implementar `DbHolidayProvider` en `backend/expedientes/domain/holiday_provider.py` que consulta feriados por versión de calendario. Actualizar `Expediente.iniciar_plazo_descargo` para asociar y congelar la versión activa o pasada explícitamente (CA1, CA3, CA4).
- [x] **T3. Migraciones y Carga Inicial de Feriados 2026 (Seeder):** Generar migraciones de esquema y migración de datos para crear la Versión 1 ("Calendario Oficial AVEIT 2026") y poblar los 16 feriados oficiales de 2026.
- [x] **T4. Tests de Dominio y Persistencia (TDD Backend):** Crear `backend/tests/expedientes/test_calendar_models.py` para probar la inmutabilidad de la versión en el expediente, exclusión de fines de semana/feriados, y preservación de zona horaria (CA1, CA2, CA3, CA4).
- [x] **T5. Serializers y Permisos RBAC de Calendario:** Implementar `CalendarioVersionSerializer`, `FeriadoExcepcionSerializer`, `CalcularPlazoSerializer` y el permiso `CanManageCalendar` (ADMIN, CD, TD) en `backend/expedientes/`.
- [x] **T6. Endpoints REST de Calendario (TDD Backend):** Implementar vistas y router en `backend/expedientes/` para listar versiones, crear nueva versión auditada, listar feriados y calcular plazos. Crear `backend/tests/expedientes/test_calendar_api.py` verificando RBAC y cálculos.
- [x] **T7. DTOs y Servicio Angular (`CalendarioApiService`):** Crear interfaces tipadas y servicio Angular en `frontend/src/app/services/calendario-api.service.ts` con sus tests unitarios en Jasmine.
- [x] **T8. Componente Angular e Interfaz de Usuario:** Crear componente `CalendarioInstitucionalComponent` en `frontend/src/app/calendario-institucional/`, con vista de feriados, simulador de plazos interactivo en tiempo real y formulario modal para nuevas excepciones/versiones conforme a `DESIGN.md`. Registrar ruta y enlace en sidebar para autoridades.
- [x] **T9. Verificación Integral, Cobertura y Consistencia PO:** Ejecutar suite completa `pytest` y `npm test`, linters (`ruff` y `ng lint`), verificar consistencia con `notasPO.md` y preparar el levantamiento en localhost.
