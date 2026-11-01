# Tareas Técnicas — Spec 007: Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

Desglose de tareas atómicas (<30 min) conforme a SDD y TDD.

---

- [x] **TS4-04.1 Dominio de composición [TDD]:**
  `backend/expedientes/domain/tribunal_composition.py`: nómina 3 + 3, incompatibilidad, apartamiento automático, suplencia y Casos A/B del Art. 95.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_domain.py` en verde.

- [x] **TS4-04.2 Nómina desde el padrón legado [TDD]:**
  Adaptador `LegacyTribunalRosterAdapter` sobre `socio_lista` (`idTipoSocio` 10/11, `user_id`, grupo); año social = `(Año Actual - 1962) - Número de Grupo` (revisión del PO, 25/10/2026), con `anoSocial` como respaldo si no hay grupo.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_roster.py` en verde.

- [x] **TS4-04.3 Modelos inmutables y migración [TDD]:**
  `ComposicionTribunal`, `IntegranteComposicion` y `ResolucionAsamblea` sólo-inserción (migración `0017`).
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_models.py` en verde.

- [x] **TS4-04.4 Servicio de aplicación [TDD]:**
  Involucrados (imputados y solicitante), consulta en vivo, estampado al pasar a `Pendiente de firma y envío`, inmovilización por Casos A/B y aviso a CD por Outbox.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_service.py` en verde.

- [x] **TS4-04.5 Inhibición y endpoints REST [TDD]:**
  `IsNotInvolvedInExpediente` (403) en decisiones de justificativos y transiciones; `GET /composicion/` y `GET/POST /resolucion-asamblea/`; supresión de apartamientos, designaciones ad hoc y constitución manual.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_api.py` en verde (200, 201, 400, 401, 403, 404, 409).

- [x] **TS4-04.6 Servicio frontend y DTOs [TDD]:**
  `obtenerComposicionTribunal`, `registrarResolucionAsamblea` y `descargarActaAsamblea` en `ExpedienteApiService`.
  *Hecho cuando:* tests Jasmine del servicio en verde.

- [x] **TS4-04.7 Inhibición visible en el detalle:**
  Remoción total del panel "Responsables del Tribunal" y de sus alertas (revisión del PO, 25/10/2026); banner de participación restringida, acciones "Aprobar", "Rechazar" y "Transicionar" ocultas al involucrado, aviso sutil de causa derivada a Asamblea y carga del acta por CD/Admin.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TS4-04.8 Verificación integral y consistencia PO:**
  Suites completas `pytest` y `Karma`, `ruff check/format`, `makemigrations --check`, build de producción y control contra `notasPO.md` y la revisión del PO sobre el PR #63.
