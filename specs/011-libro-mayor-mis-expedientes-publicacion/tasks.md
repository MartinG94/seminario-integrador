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
