# Tareas Técnicas — Spec 007: Gestionar Apartamiento y Suplencia conforme al Estatuto (S4-04)

Desglose de tareas atómicas (<30 min) conforme a SDD y TDD.

---

- [x] **TS4-04.1 Dominio de composición [TDD]:**
  Implementar `backend/expedientes/domain/tribunal_composition.py` (nómina 3 + 3, incompatibilidad, apartamiento, suplencia, caso ad hoc y validación de designados).
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_domain.py` en verde.

- [x] **TS4-04.2 Nómina desde el padrón legado [TDD]:**
  Adaptador `LegacyTribunalRosterAdapter` sobre `socio_lista` (`idTipoSocio` 10/11, `anoSocial`, `user_id`, grupo).
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_roster.py` en verde.

- [x] **TS4-04.3 Modelos inmutables y migración [TDD]:**
  `ApartamientoTribunal`, `DesignacionAdHoc`, `ComposicionTribunal` e `IntegranteComposicion` sólo-inserción.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_models.py` en verde.

- [x] **TS4-04.4 Servicio de aplicación [TDD]:**
  `TribunalCompositionService` (consulta, apartamiento propio, designación ad hoc, constitución) y guarda en `ExpedienteWorkflowService`.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_service.py` en verde.

- [x] **TS4-04.5 Endpoints REST y permisos [TDD]:**
  `GET /composicion/` y `POST /composicion/{apartamientos,designaciones-ad-hoc,constituir}/`.
  *Hecho cuando:* `backend/tests/expedientes/test_tribunal_composition_api.py` en verde (200, 201, 400, 401, 403, 404, 409).

- [x] **TS4-04.6 Servicio frontend y DTOs [TDD]:**
  Métodos de composición en `ExpedienteApiService`.
  *Hecho cuando:* tests Jasmine del servicio en verde.

- [x] **TS4-04.7 Panel "Composición del Tribunal" en el detalle:**
  Responsables 1–3 con pie de firma, apartamientos y causas, aviso ad hoc, apartamiento propio, designación ad hoc con autocompletado de socios y constitución.
  *Hecho cuando:* tests Karma del componente en verde.

- [x] **TS4-04.8 Verificación integral y consistencia PO:**
  Suites completas `pytest` y `Karma`, `ruff check/format`, `makemigrations --check` y control contra `notasPO.md`.
