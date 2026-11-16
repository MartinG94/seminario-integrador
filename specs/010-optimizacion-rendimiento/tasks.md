# Tareas Técnicas — Spec 010: Optimización Integral de Rendimiento (SCRUM-87)
## MACRO-06: Rendimiento de RAM, CPU y Base de Datos (Sprint 5)

Desglose de tareas atómicas (< 30 min) organizadas en tajadas verticales (Vertical Slices) conforme a la metodología Spec-Driven Development (SDD) y desarrollo guiado por pruebas (TDD).

---

### Slice 1: Fundaciones y Contratos Base (Backend & Frontend)

- [x] **T-87.01 Contrato de Paginación Canónico Backend [TDD]:**  
  Implementar `backend/core/pagination.py` con `StandardResultsSetPagination(PageNumberPagination)` (`page_size=20`, `max_page_size=100`, envolvente con 7 campos y manejo de errores RFC 9457 para 404).  
  *Hecho cuando:* `backend/tests/core/test_pagination.py` valida envolvente `{ count, total_pages, current_page, page_size, next, previous, results }`, límite rígido de 100 y 404 estructurado.

- [x] **T-87.02 Modelo de Paginación Frontend e Interfaz Genérica [TDD]:**  
  Implementar `frontend/src/app/models/paginated-response.model.ts` definiendo la interfaz genérica `PaginatedResponse<T>`.  
  *Hecho cuando:* Archivo de modelo creado y consumido exitosamente en compilación y pruebas TypeScript.

- [x] **T-87.03 Utilitario Universal `TrackByUtils` Frontend [TDD]:**  
  Implementar `frontend/src/app/utils/track-by.util.ts` con funciones de comparación puras `byId`, `bySocio`, `byExpediente`, `byValue`.  
  *Hecho cuando:* `frontend/src/app/utils/track-by.util.spec.ts` pasa en verde con 100% de cobertura.

---

### Slice 2: Optimización de Persistencia y Eliminación de N+1 (SCRUM-120)

- [x] **T-87.04 Suite Base de Rendimiento ORM y Límites de Queries [TDD]:**  
  Crear `backend/tests/expedientes/test_orm_performance.py` con fixtures y capturas iniciales usando `django_assert_num_queries` y `CaptureQueriesContext`.  
  *Hecho cuando:* Los tests fallan en rojo (RED) evidenciando los patrones N+1 en eventos, antecedentes y carga de binarios BLOB.

- [x] **T-87.05 Optimización de Eventos Institucionales (Eliminación de N+1) [TDD]:**  
  Refactorizar `EventoInstitucionalViewSet.get_queryset()` con anotaciones condicionales `total_convocados_calc`, `total_presentes_calc`, `total_ausentes_calc` y actualizar `EventoInstitucionalSerializer` para priorizar los valores anotados.  
  *Hecho cuando:* `test_eventos_listing_queries_are_constant` pasa en verde en $\le 3$ consultas SQL ($O(1)$).

- [x] **T-87.06 Diferimiento de Binarios BLOB en Evidencias de Expedientes [TDD]:**  
  Refactorizar `EXPEDIENTE_LIST_PREFETCH` en `backend/expedientes/views/__init__.py` utilizando `Prefetch("evidencias", queryset=EvidenciaDescargo.objects.defer("contenido_blob").select_related("socio"))`.  
  *Hecho cuando:* `test_expedientes_listing_defers_binary_blob` pasa en verde confirmando que `contenido_blob` no figura en ninguna sentencia SQL de listado.

- [x] **T-87.07 Optimización de Catálogo de Antecedentes con Subquery [TDD]:**  
  Refactorizar `AntecedenteT03View` y `build_expedientes_referenciados_detalle` en `backend/expedientes/services/t03_valuation_service.py` con `Subquery` correlacionada indexada sobre `CambioEstadoExpediente` para fecha de emisión.  
  *Hecho cuando:* `test_antecedentes_catalogo_single_query` pasa en verde con exactamente 1 consulta SQL para 100 antecedentes (reducción del 99%).

- [x] **T-87.08 Batching en Reportes y Precarga de Subcomisiones [TDD]:**  
  Refactorizar `ReportesService.obtener_metricas_subcomision` para batching sobre `tribunal_puntajegeneral` y asegurar `select_related("subcomision")` en el prefetch de socios involucrados en causas.  
  *Hecho cuando:* `test_subcomision_metrics_batch_query` pasa en verde con 1 query batch.

---

### Slice 3: Paginación Server-Side y Rendimiento de Ranking de Socios (SCRUM-118 + SCRUM-119)

- [x] **T-87.09 Paginación Server-Side en `RankingListView` [TDD]:**  
  Integrar `StandardResultsSetPagination` en `RankingListView` (`backend/ranking/views.py`), soportando `page`, `page_size`, `ordering` y `search` sobre el queryset reconciliado.  
  *Hecho cuando:* `backend/tests/ranking/test_ranking_pagination.py` pasa en verde verificando la respuesta paginada de 20 registros.

- [x] **T-87.10 Adaptación del Servicio Frontend `ranking.service.ts` [TDD]:**  
  Actualizar `obtenerRanking()` en `frontend/src/app/services/ranking.service.ts` para enviar parámetros de paginación y mapear la respuesta a `PaginatedResponse<RankingSocio>`.  
  *Hecho cuando:* Tests unitarios de `ranking.service.spec.ts` pasan en verde.

- [x] **T-87.11 Refactorización OnPush, trackBy y MatPaginator en `RankingSociosComponent` [TDD]:**  
  Configurar `ChangeDetectionStrategy.OnPush`, eliminar getters computados de ordenamiento/filtrado (`sociosOrdenados`, `sociosPaginados`), implementar `recalcularVista()`, vincular `MatPaginator` con reseteo a página 1 en filtros, e implementar `takeUntil(this.destroy$)` en `ngOnDestroy`.  
  *Hecho cuando:* Tests Karma de `ranking-socios.component.spec.ts` pasan en verde y se certifica INP < 150 ms sin Layout Thrashing.

---

### Slice 4: Paginación Server-Side y Rendimiento en Tablero y Gestión de Expedientes (SCRUM-118 + SCRUM-119)

- [x] **T-87.12 Paginación Server-Side en `ExpedienteCollectionView` y `MisExpedientesView` [TDD]:**  
  Inyectar `StandardResultsSetPagination` en `GET /api/v1/expedientes/gestion/` y `GET /api/v1/expedientes/mis-expedientes/`.  
  *Hecho cuando:* `backend/tests/expedientes/test_expediente_pagination.py` pasa en verde con 200 OK y 404 estructurado ante páginas fuera de rango.

- [x] **T-87.13 Adaptación de Servicios Frontend `tribunal-data.service.ts` y `expediente-api.service.ts` [TDD]:**  
  Actualizar métodos de consulta de expedientes para consumir y retornar `PaginatedResponse<Expediente>`.  
  *Hecho cuando:* Tests unitarios de servicios pasan en verde.

- [x] **T-87.14 Refactorización OnPush, trackBy y MatPaginator en `GestionarExpedientesComponent` [TDD]:**  
  Configurar `ChangeDetectionStrategy.OnPush`, incorporar `MatPaginator` al pie de la tabla exploradora, añadir `trackBy` en 13 iteraciones `*ngFor` y unificar desuscripciones en `takeUntil(this.destroy$)`.  
  *Hecho cuando:* Tests Karma de `gestionar-expedientes.component.spec.ts` pasan en verde con desmonte limpio.

- [x] **T-87.15 Refactorización OnPush, trackBy y MatPaginator en `MisExpedientesComponent` [TDD]:**  
  Configurar `ChangeDetectionStrategy.OnPush`, incorporar `MatPaginator`, añadir `trackBy` en 6 iteraciones, aislar el ticker `interval(1000)` con `markForCheck()` y desuscribir en `ngOnDestroy`.  
  *Hecho cuando:* Tests Karma de `mis-expedientes.component.spec.ts` pasan en verde.

---

### Slice 5: Refactorización Transversal OnPush, trackBy y Ciclo de Vida en Componentes Restantes (SCRUM-119)

- [x] **T-87.16 Optimización de `SolicitarPuntosComponent` y `AsistenciaEventoComponent` [TDD]:**  
  Configurar `ChangeDetectionStrategy.OnPush`, `trackBy` en tablas de convocados e involucrados, y protección de ciclo de vida con `takeUntil(this.destroy$)`.  
  *Hecho cuando:* Tests Karma de ambos componentes pasan en verde.

- [x] **T-87.17 Optimización de `ReportesComponent`, `CalendarioInstitucionalComponent` y `VisorExpedienteComponent` [TDD]:**  
  Configurar `ChangeDetectionStrategy.OnPush`, `trackBy` en gráficos/tablas/timelines y eliminación de recálculos continuos en plantillas.  
  *Hecho cuando:* Tests Karma de los componentes pasan en verde.

- [x] **T-87.18 Paginación en `EventoInstitucionalViewSet` y Adaptación de `evento.service.ts` [TDD]:**  
  Habilitar `pagination_class = StandardResultsSetPagination` en eventos institucionales y adaptar `evento.service.ts` para procesar `PaginatedResponse<EventoInstitucional>`.  
  *Hecho cuando:* Tests de eventos en backend y frontend pasan en verde.

---

### Slice 6: Verificación Integral de Calidad, Auditoría de Memoria y Consistencia PO

- [x] **T-87.19 Auditoría de Memoria y Detección de Fugas en Frontend (Heap Profiling):**  
  Ejecutar prueba de 20 ciclos de navegación bajo Chrome Headless CDP (`/ranking-socios` ➔ `/gestionar-expedientes` ➔ `/mis-expedientes` ➔ `/eventos-asistencia` ➔ `/reportes`) verificando Heap delta en estado estable $\le 0.5\text{ MB}$ y cero nodos DOM desconectados.  
  *Hecho cuando:* Perfil de memoria documentado en `memory_audit_report.md` (`+0.2515 MB` en primera corrida / `+0.2527 MB` en re-auditoría QA Ciclos 10→20, `0` detached DOM) y conforme a RNF-03.

- [x] **T-87.20 Verificación de Inmutabilidad del Esquema Legacy (Regla 6):**  
  Ejecutar inspección de `python manage.py makemigrations --dry-run` certificando CERO migraciones sobre tablas legacy (`socio_*`, `tribunal_*`) y `managed = False` inalterado.  
  *Hecho cuando:* Reporte de no-alteración DDL confirmado ("No changes detected").

- [x] **T-87.21 Validación de Consistencia con Notas del PO y Sistema de Diseño:**  
  Verificar ordenamientos de saldo/grupo, modal de detalle de socios, modal de involucrados en causas y notificaciones centrales de 10s (PR #49).  
  *Hecho cuando:* Lista de chequeo contra `notasPO.md` y `DESIGN.md` satisfecha al 100%.

- [x] **T-87.22 Ejecución de Suites Completas y Linter:**  
  Ejecutar `pytest -q`, `ruff check .`, `ruff format --check backend/`, `npm test`, `npx tsc --skipLibCheck --noEmit` y `npx ng build --configuration production`.  
  *Hecho cuando:* Suites en verde (`pytest`: `1387 passed, 8 skipped` MySQL-only en SQLite local; `ruff check .`: exit `0`; `ruff format --check backend/`: exit `0` sobre 235 archivos; Karma `672/672 SUCCESS`; `tsc --skipLibCheck --noEmit`: exit `0`; `ng build --configuration production`: exit `0`).

---

## Definición de Terminado (DoD) Global para la Épica SCRUM-87

1. **Paginación Universal:** Todos los endpoints de colección retornan la envolvente estándar `{ count, total_pages, current_page, page_size, next, previous, results }` con `page_size <= 100`.
2. **Componentes Optimizados:** 100% de componentes principales bajo `ChangeDetectionStrategy.OnPush`, 100% de `*ngFor` con `trackBy`, y 0 getters computados impuros en plantillas.
3. **Cero Fugas de Memoria:** Todas las suscripciones protegidas con `takeUntil(this.destroy$)`; Heap delta $\le 0.5\text{ MB}$ tras 10 navegaciones cíclicas y 0 detached DOM nodes.
4. **Persistencia $O(1)$:** Eventos $\le 3$ queries, Antecedentes $= 1$ query, Expedientes con binarios diferidos (`defer("contenido_blob")`).
5. **Regla Innegociable 6:** Cero DDL sobre tablas preexistentes del padrón y ranking; `managed = False` preservado.
6. **Notas del PO y PR #49:** Consistencia total con ordenamientos de saldo/grupo, múltiples imputados y notificaciones de 10s.
7. **Suites en Verde:** `pytest` y `npm test` finalizan sin fallos ni regresiones.
