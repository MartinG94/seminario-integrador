# Tasks — Spec 010: Panel de Administración (MACRO-03 / SCRUM-91)

- [x] **T1 (Backend TDD — Catálogo y validación de parámetros):** Dominio puro `core/domain/system_parameters.py` con las 9 claves, tipos, límites y mensajes en español.
- [x] **T2 (Backend TDD — Modelos de solo inserción):** `ParametroSistema` y `CambioRolTribunal` con migración `core/0001_initial.py`.
- [x] **T3 (Backend TDD — Servicio de parámetros):** Valor vigente, alta de versión con valor anterior y autor, historial y almacenamiento del plazo de apelación sobre `ParametroPlazoApelacion`.
- [x] **T4 (Backend TDD — Endpoints de parámetros):** `GET/PUT /api/v1/admin/parametros/`, historial y `GET /api/v1/parametros/adjuntos/` con RBAC `ADMIN`.
- [x] **T5 (Backend TDD — Consumo de parámetros):** Plazo de descargo, umbral preventivo, correos institucionales y límites de adjuntos leídos del servicio.
- [x] **T6 (Backend TDD — Miembros del TD):** Servicio y endpoints `GET/POST/DELETE /api/v1/admin/usuarios-td/` con auditoría inmutable.
- [x] **T7 (Frontend TDD — Servicio y ruta):** `AdminApiService`, ruta `/admin/parametros` solo `ADMIN` y entrada en el menú.
- [x] **T8 (Frontend TDD — Tarjetas de parámetros):** Pantalla con tarjetas Plazos, Umbrales, Correos y Adjuntos, guardado por parámetro e historial.
- [x] **T9 (Frontend TDD — Miembros del TD):** Tabla atómica, alta con búsqueda reactiva y revocación con confirmación.
- [x] **T10 (Frontend TDD — Límites de adjuntos en Mis Expedientes):** Reemplazo de las constantes locales por los límites vigentes.
- [x] **T11 (Verificación integral):** `pytest`, `ruff check`, `ruff format --check`, Karma, `npm run build` y control contra `notasPO.md`.
