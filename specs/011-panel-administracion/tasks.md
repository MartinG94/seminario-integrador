# Tasks — Spec 011: Panel de Administración (MACRO-03 / SCRUM-91)

- [x] **T1 (Backend TDD — Catálogo y validación de parámetros):** Dominio puro `core/domain/system_parameters.py` con las 9 claves, tipos, límites y mensajes en español.
- [x] **T2 (Backend TDD — Modelos de solo inserción):** `SystemParameterChange` y `TribunalRoleChange` con migración `core/0001_parametros_sistema_y_rol_tribunal.py`.
- [x] **T3 (Backend TDD — Servicio de parámetros):** Valor vigente, alta de versión con valor anterior y autor, historial y almacenamiento del plazo de apelación sobre `ParametroPlazoApelacion`.
- [x] **T4 (Backend TDD — Endpoints de parámetros):** `GET/PUT /api/v1/admin/parametros/`, historial y `GET /api/v1/parametros/adjuntos/` con RBAC `ADMIN`.
- [x] **T5 (Backend TDD — Consumo de parámetros):** Plazo de descargo, umbral preventivo, correos institucionales y límites de adjuntos leídos del servicio.
- [x] **T6 (Backend TDD — Miembros del TD):** Servicio y endpoints `GET/POST/DELETE /api/v1/admin/usuarios-td/` con auditoría inmutable.
- [x] **T7 (Frontend TDD — Servicio y ruta):** `AdminApiService`, ruta `/admin/parametros` solo `ADMIN` y entrada en el menú.
- [x] **T8 (Frontend TDD — Tarjetas de parámetros):** Pantalla con tarjetas Plazos, Umbrales, Correos y Adjuntos, guardado por parámetro e historial.
- [x] **T9 (Frontend TDD — Miembros del TD):** Tabla atómica, alta con búsqueda reactiva y revocación con confirmación.
- [x] **T10 (Frontend TDD — Límites de adjuntos en Mis Expedientes):** Reemplazo de las constantes locales por los límites vigentes.
- [x] **T11 (Verificación integral):** `pytest`, `ruff check`, `ruff format --check`, Karma, `npm run build` y control contra `notasPO.md`.
- [x] **T12 (Revisión PR #78 — Integración con `main`):** Merge de `origin/main` con conflictos resueltos (`TASK.md`, vistas de expedientes y `MisExpedientesComponent` con `OnPush` + `markForCheck`), spec renombrada a `011-` y migración `core` sin reutilizar `0001_initial`.
- [x] **T13 (Revisión PR #78 — Parámetros consumidos en todas las vistas) [TDD]:** `GET /api/v1/parametros/umbrales/` y `/plazos/`; Ranking (resaltado, conteo y filtro `solo_alertas` en servidor), Mis Expedientes y `TribunalDataService` usan los umbrales vigentes y el switch preventivo; textos de plazo de descargo sin "5 días hábiles" fijo; tope de comprobantes configurable en `PresentarDescargoSerializer` y cuota transaccional en `EvidenciaUploadView`.
- [x] **T14 (Revisión PR #78 — Miembros del TD) [TDD]:** `N° de Socio` real (`numero_socio`), búsqueda de candidatos en servidor sin límite de página, indicador de carga y "Sin coincidencias", corrección del crash al seleccionar en el autocompletado y verificación de `user.is_active`.
- [x] **T15 (Revisión PR #78 — Diseño, accesibilidad y tipado):** Tokens oscuros de `primary`/`danger`/estados y `on-*` en `DESIGN.md`, `color-scheme`, panel de diálogo tokenizado, CSS mobile-first, objetivos táctiles de 44 px, `lang="es"`, roles de diálogo en Mis Expedientes y `strict: true` en TypeScript.
