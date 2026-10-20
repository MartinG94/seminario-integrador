# Tareas Técnicas — Spec 006: Resolver Causal T02 con Fundamento Trazable (S4-02)

Desglose de tareas atómicas (<30 min) conforme a SDD y TDD.

---

- [x] **TS4-02.1 Dominio de decisión por causal [TDD]:**
  Implementar `backend/expedientes/domain/causal_resolution.py` (regla sugerida, exigencia y validación de fundamento).
  *Hecho cuando:* `backend/tests/expedientes/test_causal_resolution_domain.py` en verde.

- [x] **TS4-02.2 Modelo inmutable y migración [TDD]:**
  Implementar `DecisionCausalDescargo` con versión única por descargo, bloqueo de modificación y eliminación, y su migración.
  *Hecho cuando:* `backend/tests/expedientes/test_causal_resolution_models.py` en verde.

- [x] **TS4-02.3 Servicio de aplicación [TDD]:**
  Implementar `CausalResolutionService` (etapa procesal, T02, evidencia vigente, versión y copia del descargo).
  *Hecho cuando:* `backend/tests/expedientes/test_causal_resolution_service.py` en verde.

- [x] **TS4-02.4 Endpoints REST y permisos [TDD]:**
  `GET`/`POST /api/v1/expedientes/{id}/descargos/{descargo_id}/decisiones/` con permiso exclusivo TD para registrar y decisiones visibles sólo para autoridades en el detalle.
  *Hecho cuando:* `backend/tests/expedientes/test_causal_resolution_api.py` en verde (201, 400, 401, 403, 404, 409).

- [x] **TS4-02.5 Servicio frontend y DTOs [TDD]:**
  Métodos `obtenerDetalleExpediente`, `listarDecisionesCausal` y `registrarDecisionCausal` en `ExpedienteApiService`.
  *Hecho cuando:* tests Jasmine del servicio en verde.

- [x] **TS4-02.6 Panel "Causales T02" en el detalle del TD:**
  Aceptar/Rechazar por causal, fundamento obligatorio según regla, comprobantes valorados e historial de versiones con autor y fecha. Avisos por el servicio central de notificaciones.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TS4-02.7 Verificación integral y consistencia PO:**
  Suites completas `pytest` y `Karma`, `ruff check/format` y control contra `notasPO.md`.

- [x] **TS4-02.8 Revisión PR — Rendimiento y consistencia [TDD]:**
  Calcular la regla sugerida en memoria, prefetch de decisiones en todas las vistas del listado y criterio único `evidence_belongs_to` para comprobantes vigentes.
  *Hecho cuando:* `TestRendimientoListado` y `TestDetalleInvolucradosYEvidencia` en verde.

- [x] **TS4-02.9 Revisión PR — Pruebas de aislamiento [TDD]:**
  Descargo de otro expediente (404), comprobante de otro imputado (400), T03 (400), historial para ADMIN (200) y anónimo (401).
  *Hecho cuando:* `TestAislamientoMultiactor` y los nuevos casos de `test_causal_resolution_api.py` en verde.

- [x] **TS4-02.10 Revisión PR — Evaluación en dos pasos en el detalle:**
  Tabla de Involucrados (notasPO §4) con "Evaluar justificación", panel con "Ver comprobante" (descarga segura S3-04), Aprobar/Desaprobar, fundamento accesible con contador e historial consultable por TD, CD y Administrador tras la emisión.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TS4-02.11 Revisión PR — Datos de prueba:**
  Escenarios EXP-0901/2026 a EXP-0904/2026 en `seed_production_data`.
  *Hecho cuando:* `backend/tests/test_seed_causal_t02.py` en verde.
