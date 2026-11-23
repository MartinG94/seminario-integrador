# Tasks — Spec 011: Libro Mayor, Mis Expedientes y Publicación (MACRO-02 / SCRUM-59)

- [x] **T1 (Backend TDD — Dominio del libro mayor):** `ranking/domain/ledger.py` con regla 3:1, clasificación del impacto y hash encadenado.
- [x] **T2 (Backend TDD — Modelo de auditoría):** `AsientoLibroMayor` de solo inserción, migración e inserción controlada en `PuntajeAplicado`.
- [x] **T3 (Backend TDD — Impacto por socio):** Resolución del impacto individual desde descargos, valoraciones y solicitud; el proveedor deja de usar ±0,25.
- [x] **T4 (Backend TDD — Asientos al emitir):** `LedgerService` invocado por `emitir_resolucion()` con idempotencia y regla 3:1.
- [x] **T5 (Backend TDD — Saldo del socio):** `GET /mis-expedientes/saldo/` y `puntos_aplicados` / `medida_aplicada` en Mis Expedientes.
- [x] **T6 (Backend TDD — Aislamiento):** Descargos, comprobantes y resolución no emitida ocultos en Mis Expedientes para cualquier rol.
- [x] **T7 (Backend TDD — Censura de salud):** `expedientes/domain/medical_redaction.py` reutilizado por el visor.
- [x] **T8 (Backend TDD — Publicación):** Endpoints JSON y PDF con permisos, impactos visibles por rol y auditoría de consulta.
- [x] **T9 (Frontend TDD — Servicio):** DTOs y métodos `obtenerMiSaldo`, `obtenerResolucionPublicada` y `descargarResolucionPublicadaPdf`.
- [x] **T10 (Frontend TDD — Mis Expedientes):** Saldo y pendientes del libro mayor, puntos aplicados y sin lista local de respaldo.
- [x] **T11 (Frontend TDD — Modal de resolución):** Lectura de la publicación y descarga del PDF desde el detalle.
- [x] **T12 (Verificación integral):** `pytest`, `ruff check`, `ruff format --check`, Karma, `npm run build` y control contra `notasPO.md`.
- [x] **T13 (Revisión PR #79 — Integración con `main`):** Conflictos resueltos (`models.py`, `resolution_service.py`, Mis Expedientes), migración de merge `0031` y `0032` (asiento `REVERSION`, auditoría de consulta de solo inserción con tipo de acceso).
- [x] **T14 (Revisión PR #79 — Libro mayor) [TDD]:** Impacto con exclusión fundada y puntaje ratificado, proveedor alineado al cálculo por socio (valoraciones T03, descargos vigentes), `numero_socio` obligatorio, motor 3:1 único (`WarningAccumulationService`) sin doble conteo, enmiendas Opción B por `LedgerService.registrar_enmienda`, bloqueo por resolución, hash con todos los campos y verificador de cadena.
- [x] **T15 (Revisión PR #79 — Aislamiento y publicación) [TDD]:** Vista de imputado sin depender de `?origen=` (detalle, versiones y comprobantes), valoración reservada hasta la emisión, título censurado, publicación sin identificadores internos, PDF con título, fecha, reglamentos, impactos e integridad, `Content-Disposition` saneado y `nosniff`, y censura de salud por palabra con abreviaturas.
- [x] **T16 (Revisión PR #79 — Frontend):** Modal de resolución con foco, Esc, `inert`, bloqueo de scroll y descarte de respuestas obsoletas; descarga de PDF robusta; colores con tokens de `DESIGN.md` y modo oscuro.
