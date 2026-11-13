# Plan Técnico de Implementación Consolidado — SCRUM-118
## Paginación Server-Side en Backend (DRF) y Frontend (Angular 14)

> **Épica:** SCRUM-87 (MACRO-06: Optimización Integral de Rendimiento de la Plataforma - RAM, CPU y Base de Datos)  
> **Subtarea:** SCRUM-118: S5-06.1 - Paginación server-side en Backend y Frontend  
> **Autor / Rol:** Tech Lead Orchestrator del Equipo SCRUM-118  
> **Especialistas Participantes:** Dev Frontend Senior, Dev Backend Senior, DBA Senior  
> **Fecha:** 12 de Noviembre de 2026  
> **Estado:** Aprobado para Planificación e Implementación SDD  
> **Artefactos Base Armonizados:**
> - [draft_frontend_118.md](file:///D:/Proyectos-mg/seminario-integrador/specs/010-optimizacion-rendimiento/draft_frontend_118.md)
> - [draft_backend_118.md](file:///D:/Proyectos-mg/seminario-integrador/specs/010-optimizacion-rendimiento/draft_backend_118.md)
> - [draft_dba_118.md](file:///D:/Proyectos-mg/seminario-integrador/specs/010-optimizacion-rendimiento/draft_dba_118.md)
> - [relevamiento_scrum_118_paginacion.md](file:///D:/Proyectos-mg/seminario-integrador/docs/gestion-proyecto/relevamiento_scrum_118_paginacion.md)

---

## 1. Resumen Ejecutivo y Objetivos

La tarea **SCRUM-118** ataca el cuello de botella más crítico de transferencia de datos y consumo de memoria del sistema SGD-AVEIT. En el estado actual:
1. El backend entrega nóminas completas sin fraccionar (515 socios en `/api/v1/ranking/` y el histórico acumulado en `/api/v1/expedientes/`), generando payloads de hasta 260 KB y alta retención de memoria en workers de Gunicorn.
2. El frontend procesa colecciones completas en memoria cliente, realizando ordenamiento y filtrado en el *main thread*, lo que degrada las métricas de rendimiento web (LCP > 2.5 s e INP > 250 ms en dispositivos móviles).

Este plan técnico consolida y armoniza los aportes de los tres especialistas del equipo (Frontend, Backend y DBA), estableciendo una arquitectura desacoplada, tipada, reactiva y de alto desempeño bajo la metodología **Spec-Driven Development (SDD)**.

---

## 2. Contratos Canónicos de API REST Estandarizados

### 2.1. Estructura de la Envolvente JSON Canónica

Toda consulta de colección paginada en el SGD-AVEIT responderá indefectiblemente con la siguiente envolvente JSON de primer nivel:

```json
{
  "count": 515,
  "total_pages": 26,
  "current_page": 1,
  "page_size": 20,
  "next": "http://localhost:8000/api/v1/ranking/?page=2&page_size=20",
  "previous": null,
  "results": [
    {
      "id": 101,
      "nroSocio": 101,
      "legajo": "54321",
      "nombre": "Carlos",
      "apellido": "Alonso",
      "categoria": "ACTIVO",
      "subcomision": "Cómputos",
      "grupo": "G57",
      "saldo": 10.0,
      "saldoHistorico": 10.0,
      "saldoPuntajeGeneral": 10.0,
      "diferencia": 0.0,
      "reconciliado": true
    }
  ]
}
```

### 2.2. Parámetros de Consulta (Query Parameters) Aceptados

| Parámetro | Tipo | Requerido | Valor por Defecto | Restricciones / Validación | Descripción |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `page` | `integer` | No | `1` | Mínimo: `1`. Si `page > total_pages` $\to$ `404 Not Found`. | Índice de página solicitada (base 1). |
| `page_size` | `integer` | No | `20` | Mínimo: `1`, Techo rígido: `100`. | Registros devueltos por página. |
| `ordering` | `string` | No | Vía configuración | Lista separada por comas (`-saldo,apellido`). | Criterio de ordenamiento global en BD. |
| `search` | `string` | No | `null` | Sanitizado, longitud mínima 2 caracteres. | Término de búsqueda textual. |
| `categoria` | `string` | No | `null` | `'ACTIVO'`, `'PASIVO'`. | Filtro societario estatutario. |
| `subcomision`| `string/int`| No | `null` | Nombre o ID de subcomisión. | Filtro de área de trabajo. |
| `estado` | `string` | No | `null` | Estados válidos de expediente (Art. 12). | Filtro de estado de tramitación. |
| `urgencia` | `string` | No | `null` | `'baja'`, `'normal'`, `'urgente'`. | Filtro de prioridad procesal. |
| `legajo` | `string` | No | `null` | Alfanumérico. | Filtro por legajo del socio involucrado. |

### 2.3. Semántica de Errores y Casos Borde (RFC 9457)

1. **Página fuera de rango (`page > total_pages` o `page < 1`):**
   - **Código HTTP:** `404 Not Found`.
   - **Cuerpo JSON:**
     ```json
     {
       "type": "https://errors.aveit.org.ar/invalid-page",
       "title": "Página no encontrada",
       "status": 404,
       "detail": "Página inválida. La página solicitada no contiene resultados."
     }
     ```
2. **Parámetro no numérico (`page=abc`):**
   - **Código HTTP:** `404 Not Found` (o `400 Bad Request` controlado).
3. **Solicitud de tamaño abusivo (`page_size=500`):**
   - **Comportamiento:** Se aplica el techo rígido `max_page_size = 100` sin arrojar error; se devuelven 100 registros con `"page_size": 100`.

### 2.4. Estrategia Híbrida de Compatibilidad hacia Atrás

Para salvaguardar la suite preexistente de tests (`test_ranking_api.py`, `test_expedientes.py`) durante la transición:
- Si la petición **NO** incluye ni `page` ni `page_size`, las vistas pueden mantener de forma transitoria la devolución de lista plana si así lo requieren clientes legados, o bien se activa la paginación universal una vez actualizados los fixtures de test.
- Las llamadas desde el frontend Angular 14 **siempre enviarán explícitamente** `?page=X&page_size=Y`, garantizando la recepción garantizada de la envolvente canónica.

---

## 3. Matriz de Integración y Flujo Reactivo de Datos

### 3.1. Flujo Unidireccional y Reactivo de Datos (RxJS & DRF)

```
[ Usuario interactúa con la UI ]
       │ (Cambia página en MatPaginator / Escribe en buscador / Ordena columna)
       ▼
[ Componente Angular (RankingSociosComponent / GestionarExpedientesComponent) ]
       │ paramsSubject$.next(nuevosParametros)
       ▼
[ Pipe Reactivo RxJS ]
       │ debounceTime(150ms) -> distinctUntilChanged() -> switchMap()
       ▼
[ Servicio Angular (RankingService / ExpedienteApiService) ]
       │ HttpClient.get<PaginatedResponse<T>>('/api/v1/...', { params })
       ▼
[ Red HTTP / REST API Gateway ]
       │ GET /api/v1/ranking/?page=2&page_size=20&ordering=-saldo
       ▼
[ Backend Django REST Framework (APIView + StandardResultsSetPagination) ]
       │ 1. Valida parámetros y límites (max_page_size=100)
       │ 2. Aplica filtros y ordenamiento global sobre QuerySet
       ▼
[ Motor Relacional MySQL 8.0 (InnoDB) ]
       │ Query 1: SELECT COUNT(*) FROM socios WHERE ... (Usa índices cubrientes)
       │ Query 2: SELECT ... FROM socios WHERE ... ORDER BY ... LIMIT 20 OFFSET 20
       ▼
[ Envolvente Serializada Canónica ]
       │ Response({ count: 515, total_pages: 26, current_page: 2, results: [...] })
       ▼
[ Componente Angular ]
       │ Recibe PaginatedResponse<T>
       │ Actualiza: this.socios = res.results; this.totalRegistros = res.count;
       ▼
[ Renderizado Optimizado en DOM ]
       │ Renderiza estrictamente 20 nodos DOM.
       │ Zero layout-thrashing. INP < 100ms.
```

### 3.2. Máquina de Estados de Paginación en Frontend

| Evento Disparador | Acción en Estado Local | Efecto en `page` | Petición Emitida al Backend |
| :--- | :--- | :---: | :--- |
| **Inicio (`ngOnInit`)** | Carga inicial por defecto | `1` | `?page=1&page_size=20&ordering=-saldo` |
| **Cambio de Página (`onCambioPagina`)** | Actualiza `pageIndex` | `event.pageIndex + 1` | `?page=N&page_size=20&...` |
| **Cambio de Tamaño (`pageSize`)** | Actualiza `pageSize` | `1` (Reseteo) | `?page=1&page_size=N&...` |
| **Modificación de Filtro / Búsqueda** | Actualiza `search` / `categoria` | `1` (Reseteo Forzoso) | `?page=1&search=X&...` |
| **Clic en Cabecera de Columna** | Alterna asc/desc/null | Conserva o `1` | `?page=1&ordering=campo&...` |
| **Error HTTP 404/500 de API** | Activa `catchError`, vacía lista | Conserva | Dispara `NotificationService.error(...)` |

---

## 4. Estrategia de Optimización en Base de Datos (MySQL 8.0)

A partir del dictamen del DBA Senior:

1. **Eficiencia en Cláusulas `LIMIT` y `OFFSET`:**
   Para un padrón de ~515 socios y un histórico de < 5.000 expedientes, el costo de `OFFSET` se mantiene en órdenes inferiores a **15 ms** siempre que el ordenamiento esté respaldado por un índice B-Tree.
2. **Índices Secundarios a Implementar:**
   - En tabla `socios`:
     - `idx_socios_categoria_subcomision`: `(anoSocial, codSubcomision)` para acelerar filtros de ranking.
   - En tabla `socios_estudios`:
     - `idx_socio_estudios_legajo`: `(nroLegajo, nroSocio)` para búsqueda instantánea por legajo.
   - En tabla `ranking_puntajeaplicado`:
     - `idx_puntaje_socio`: `(socio_id, puntajeAplicado)` como índice cubriente (*covering index*) para sumatorias agregadas de saldo.
   - En tabla `expedientes_expediente`:
     - `idx_expediente_estado_fecha`: `(estado, fecha_creacion DESC)` para resolver paginación y orden sin `filesort`.
3. **Optimización de `COUNT(*)`:**
   La consulta `count` de DRF aprovecha automáticamente los índices secundarios más estrechos sin requerir Full Table Scan.
4. **Gobernanza de Datos e Inmutabilidad:**
   - **Cero sentencias `UPDATE`/`DELETE` directas sobre saldos:** Las consultas paginadas operan con nivel de aislamiento de lectura estándar sin bloqueos exclusivos (`FOR UPDATE`).
   - **Respeto absoluto al esquema legacy:** Ninguna tabla o columna preexistente (`socios`, `anoSocial`, `codSubcomision`, `nroSocio`) será renombrada ni alterada en sus tipos de datos.

---

## 5. Cumplimiento de Reglas Innegociables de AGENTS.md y Diseño

1. **Tokens de Diseño de `DESIGN.md`:**
   - El componente `MatPaginator` consumirá estrictamente la paleta y tipografía oficial:
     - Color primario: `{colors.primary}` (`#151846`) para botones activos e íconos interactivos.
     - Color de acento: `{colors.accent}` (`#6E9DDC`) en estados de foco y selección.
     - Superficie de tarjeta: `{colors.surface-card}` (`#FFFFFF`) y modo oscuro `{colors.dark-surface-card}` (`#1E293B`).
     - Tipografía: `Montserrat` y `Roboto` según la escala tipográfica canónica.
2. **Servicio Central de Notificaciones (`NotificationService`):**
   - Ante fallas de conexión o páginas inválidas devueltas por la API, los mensajes de error se emitirán exclusivamente mediante `NotificationService.error(...)` (ubicación: abajo a la derecha, 10 segundos de duración, desvanecimiento automático, botón de cierre accesible con X, persistencia entre pantallas).
   - Queda estrictamente prohibido el uso de alertas embebidas en formularios o `$.notify`.
3. **Búsqueda Reactiva con Select2 / Autocompletado:**
   - En cualquier componente donde se filtre por socio individual, se mantiene la integración con el autocompletado reactivo con `debounceTime(300ms)` y búsqueda a partir de 3 caracteres.
4. **Accesibilidad Universal (WCAG 2.2 AA):**
   - Etiquetas ARIA informativas en controles del paginador (`aria-label="Página anterior"`, `aria-label="Página siguiente"`).
   - Anuncio accesible de cambios de página mediante `aria-live="polite"`.
   - Navegación completa por teclado (`Tab`, `Shift+Tab`, `Enter`, `Spacebar`).

---

## 6. Estrategia de Testing Integral (TDD)

### 6.1. Backend (Pytest)
Ubicación: `backend/tests/test_ranking_pagination.py` y `backend/tests/expedientes/test_expedientes_pagination.py`.

- [ ] **Test 1: Estructura Canónica de Envolvente:**
  Solicitud `GET /api/v1/ranking/?page=1&page_size=20` retorna HTTP 200 y JSON con campos exactos: `count`, `total_pages`, `current_page`, `page_size`, `next`, `previous`, `results`.
- [ ] **Test 2: Navegación entre Páginas:**
  Solicitud a `page=2` retorna los siguientes 20 elementos y enlaces `previous` y `next` consistentes.
- [ ] **Test 3: Techo Rígido de Tamaño de Página:**
  Solicitud con `page_size=500` retorna HTTP 200 con máximo 100 registros y `"page_size": 100`.
- [ ] **Test 4: Página Fuera de Rango (404 RFC 9457):**
  Solicitud con `page=9999` retorna HTTP 404 con estructura de error RFC 9457 (`title`, `status`, `detail`).
- [ ] **Test 5: Parámetro Inválido:**
  Solicitud con `page=abc` o `page=-5` es capturada de forma defensiva retornando HTTP 404/400 sin generar errores 500.
- [ ] **Test 6: Paginación en Expedientes con Filtro de Estado:**
  `GET /api/v1/expedientes/?page=1&page_size=10&estado=revision_resolucion` fracciona adecuadamente el conjunto filtrado.
- [ ] **Test 7: Compatibilidad hacia Atrás:**
  Llamadas legadas sin parámetros de paginación se resuelven sin romper contratos existentes.

### 6.2. Frontend (Karma / Jasmine)
Ubicación: `frontend/src/app/ranking-socios/ranking-socios.component.spec.ts` y `frontend/src/app/services/ranking.service.spec.ts`.

- [ ] **Test 1: Servicio emite parámetros correctos:**
  `RankingService.obtenerRankingPaginado` concatena adecuadamente query parameters (`page`, `page_size`, `ordering`, `search`).
- [ ] **Test 2: Componente renderiza MatPaginator:**
  Verifica la presencia de `<mat-paginator>` y la correcta vinculación de `[length]` con `totalRegistros`.
- [ ] **Test 3: Emisión de PageEvent actualiza el stream:**
  Al simular cambio de página en `MatPaginator`, se dispara una nueva llamada HTTP con el número de página incrementado.
- [ ] **Test 4: Reseteo automático de página ante filtros:**
  Al cambiar el valor de búsqueda o categoría, el índice de página vuelve forzosamente a `1`.
- [ ] **Test 5: Captura de errores con NotificationService:**
  Si el backend responde con error 404 o 500, el componente invoca `NotificationService.error` y mantiene un estado vacío sin romperse.

---

## 7. Desglose de Tareas Atómicas (< 30 min) para SCRUM-118

Siguiendo la metodología Spec-Driven Development (SDD):

| ID Tarea | Nombre de la Tarea Atómica | Estimación | Especialista Responsable | Entregables / Archivos Afectados | Criterio de Aceptación Verificable |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **T-118.01** | Implementar `StandardResultsSetPagination` en Backend | 25 min | Dev Backend Senior | `backend/core/pagination.py`, `backend/core/settings.py` | Clase DRF creada con envolvente canónica, techo de 100 y captura de `NotFound` RFC 9457. |
| **T-118.02** | Tests unitarios Pytest de la clase de paginación canónica | 20 min | Dev Backend Senior | `backend/tests/test_pagination_core.py` | Pytest en verde validando estructura envolvente, límites de `page_size` y excepciones 404. |
| **T-118.03** | Integrar paginación server-side en `RankingListView` | 25 min | Dev Backend Senior | `backend/ranking/views.py`, `backend/tests/test_ranking_pagination.py` | Endpoint `/api/v1/ranking/` acepta `page` y `page_size` retornando envolvente paginada. |
| **T-118.04** | Integrar paginación server-side en `ExpedienteCollectionView` | 25 min | Dev Backend Senior | `backend/expedientes/views/__init__.py`, `backend/tests/expedientes/test_expedientes_pagination.py` | Endpoint `/api/v1/expedientes/` pagina con filtros de estado y legajo preservados. |
| **T-118.05** | Crear índices de optimización en base de datos MySQL | 20 min | DBA Senior | `backend/ranking/migrations/`, `backend/expedientes/migrations/` | Migraciones Django que crean índices no invasivos en `socios`, `puntajeaplicado` y `expedientes`. |
| **T-118.06** | Definir interfaz TypeScript `PaginatedResponse<T>` | 15 min | Dev Frontend Senior | `frontend/src/app/models/paginated-response.model.ts` | Interfaz genérica creada y exportada con tipado estricto. |
| **T-118.07** | Actualizar `RankingService` con soporte paginado y specs | 20 min | Dev Frontend Senior | `frontend/src/app/services/ranking.service.ts`, `ranking.service.spec.ts` | Método `obtenerRankingPaginado` implementado con pruebas unitarias en verde. |
| **T-118.08** | Actualizar `TribunalDataService` / `ExpedienteApiService` y specs | 20 min | Dev Frontend Senior | `frontend/src/app/services/tribunal-data.service.ts`, `expediente-api.service.ts` | Métodos de expedientes paginados implementados con pruebas unitarias en verde. |
| **T-118.09** | Integrar `MatPaginator` y flujo reactivo en `RankingSociosComponent` | 30 min | Dev Frontend Senior | `frontend/src/app/ranking-socios/ranking-socios.component.ts`, `.html`, `.scss` | Tabla de ranking muestra `MatPaginator`, resetea en filtros y elimina `.slice()` de cliente. |
| **T-118.10** | Integrar `MatPaginator` en tabla de `GestionarExpedientesComponent` | 25 min | Dev Frontend Senior | `frontend/src/app/gestionar-expedientes/gestionar-expedientes.component.ts`, `.html` | Vista de tabla de expedientes muestra `MatPaginator` al pie de la tarjeta y sincroniza cambios. |
| **T-118.11** | Pruebas unitarias de componentes Frontend (Karma/Jasmine) | 25 min | Dev Frontend Senior | `ranking-socios.component.spec.ts`, `gestionar-expedientes.component.spec.ts` | Tests de interacción de paginador, cambio de página y filtros pasando en verde (0 fallos). |
| **T-118.12** | Verificación E2E de rendimiento y consistencia con Notas del PO | 20 min | Tech Lead Orchestrator | `specs/010-optimizacion-rendimiento/reporte_rendimiento_118.md` | Reducción de payload confirmada (>75%), LCP < 2.5s, INP < 150ms, 100% apego a `notasPO.md`. |

---

## 8. Definición de Hecho (DoD) Específica de SCRUM-118

Para declarar finalizada la tarea **SCRUM-118**:

1. [ ] **Contrato REST Validado:** `GET /api/v1/ranking/?page=1&page_size=20` y `GET /api/v1/expedientes/?page=1&page_size=20` retornan HTTP 200 con la envolvente canónica `{ count, total_pages, current_page, page_size, next, previous, results }`.
2. [ ] **Control de Bordes y Errores:** Solicitudes con `page=9999` devuelven HTTP 404 estructurado bajo RFC 9457; solicitudes con `page_size > 100` son acotadas a 100 registros.
3. [ ] **UI con MatPaginator Canónico:** Ambas pantallas (`/ranking-socios` y la tabla de `/gestionar-expedientes`) incorporan `MatPaginator` con selector de tamaño `[10, 20, 50, 100]` estilizado con tokens de `DESIGN.md`.
4. [ ] **Reactividad y UX Intacta:** Los filtros y búsquedas resetean forzosamente la paginación a la página 1; el ordenamiento se calcula globalmente en el motor MySQL y no en memoria del navegador.
5. [ ] **Métricas de Rendimiento Cumplidas:** El tamaño de la respuesta de red para la página inicial del ranking se reduce en al menos un **75%** (de ~220 KB a menos de 40 KB); el renderizado de la tabla en Angular no excede los 50 nodos DOM activos.
6. [ ] **Gobernanza de Datos:** Cero sentencias `UPDATE`/`DELETE` manuales en la base de datos; esquema legacy respetado estrictamente sin modificaciones a nombres de tablas o columnas preexistentes.
7. [ ] **Notificaciones Accesibles:** Los errores de carga se canalizan exclusivamente por `NotificationService` (abajo a la derecha, 10 segundos, no dismiss en navegación).
8. [ ] **Pruebas Automatizadas 100% en Verde:** Todas las pruebas unitarias y de integración (`pytest` y `npm test`) pasan con 0 errores y sin regresiones.
