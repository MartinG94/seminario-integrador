
- [x] **TPB-02.11 Rediseño del Modal de Detalle de Expediente según boceto PO (SCRUM-70 / PR #64) [TDD]:**
  Cabecera con Exp: <n>/<YYYY> y título centrado, metadatos, sección de Reglamentación, recuadro de Motivo, tabla de 6 columnas (Involucrados y justificaciones con Estado de Descargo Leído/No Leído/Sin descargo, Puntaje Final y navegación Ver Descargo) y validación de botones en el pie (Generar Resolución, Firmar Resolución, Ver Resolución).
  *Hecho cuando:* 63 tests Karma y 11 tests Pytest de detalle en verde.
# Tareas Técnicas — Spec 008: Tramitar Apelación y Adecuación del T01 (PB-02)

Desglose de tareas atómicas (<30 min) conforme a SDD y TDD.

---

- [x] **TPB-02.1 Dominio de apelación y adecuación [TDD]:**
  `backend/expedientes/domain/t01_appeal.py` (plazo, texto, cambios, agravamiento, afectados y signo de puntos).
  *Hecho cuando:* `backend/tests/expedientes/test_t01_appeal_domain.py` en verde.

- [x] **TPB-02.2 Modelos inmutables y migración [TDD]:**
  `ParametroPlazoApelacion`, `PeriodoApelacion`, `ApelacionT01` y `AdecuacionT01` sólo-inserción.
  *Hecho cuando:* `backend/tests/expedientes/test_t01_appeal_models.py` en verde.

- [x] **TPB-02.3 Plazo parametrizado y períodos por socio [TDD]:**
  Apertura al entrar a `justificando`, plazo efectivo en transición y job de vencimiento.
  *Hecho cuando:* `backend/tests/expedientes/test_t01_appeal_periods.py` en verde.

- [x] **TPB-02.4 Servicio de apelación y adecuación [TDD]:**
  Apelación versionada con constancia, rechazo de T02/T03, adecuación con mail de motivos y reapertura aprobada por el TD.
  *Hecho cuando:* `backend/tests/expedientes/test_t01_appeal_service.py` en verde.

- [x] **TPB-02.5 Endpoints REST y permisos [TDD]:**
  Parámetro del plazo, apelación, adecuación e historial del T01.
  *Hecho cuando:* `backend/tests/expedientes/test_t01_appeal_api.py` en verde.

- [x] **TPB-02.6 Servicio frontend y DTOs [TDD]:**
  Métodos en `ExpedienteApiService`.
  *Hecho cuando:* tests Jasmine del servicio en verde.

- [x] **TPB-02.7 Apelación en "Mis Expedientes":**
  Botón "Apelar" en lugar de "Descargo" para expedientes de T01, edición en plazo e historial propio.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TPB-02.8 Debate y adecuación en el detalle del TD:**
  Apelaciones recibidas, formulario de adecuación con autocompletado de socios, nuevo período opcional e historial.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TPB-02.9 Parámetro del plazo en "Calendario Institucional":**
  Consulta y edición del plazo de apelación para TD y Administración.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TPB-02.10 Verificación integral y consistencia PO:**
  Suites `pytest` y `Karma`, `ruff`, build y control contra `notasPO.md`.
