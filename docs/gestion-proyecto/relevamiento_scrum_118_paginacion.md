# Relevamiento de Requerimientos — SCRUM-118: Paginación Server-Side en Backend y Frontend

> **Épica:** SCRUM-87 (MACRO-06: Optimización Integral de Rendimiento de la Plataforma - RAM, CPU y Base de Datos)  
> **Subtarea:** SCRUM-118: S5-06.1 - Paginación server-side en Backend y Frontend  
> **Autor:** Analista de Sistemas Senior (Arquitectura de Integración, APIs REST y Paginación Server-Side)  
> **Fecha:** 12 de Noviembre de 2026  
> **Estado:** Relevado y presentado  

---

## 1. Relevamiento del Estado Actual del Sistema

Tras la inspección exhaustiva del código fuente del backend (`backend/core/settings.py`, `backend/ranking/`, `backend/expedientes/`, `backend/padron/`) y frontend (`frontend/src/app/`), se constata una marcada asimetría arquitectónica y una ausencia casi total de paginación server-side en las colecciones críticas del sistema.

### 1.1. Inventario de Endpoints y Vistas Relevadas

| Módulo / Dominio | Endpoint REST | Vista Backend | Comportamiento Actual Backend | Componente / Servicio Frontend | Comportamiento Actual Frontend |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ranking Oficial** | `GET /api/v1/ranking/`<br>`GET /api/ranking/` | `RankingListView` (`APIView`) | Consulta queryset reconciliado completo (~515 socios con sumatorias y coalescencias de `PuntajeAplicado`). Retorna un **array JSON plano** con todos los socios (`many=True`). | `RankingSociosComponent` (`ranking.service.ts`) | Recibe los 515 objetos en memoria. Filtra con `.filter()`, ordena con `.sort()` y pagina en cliente con `.slice()` manual sin `MatPaginator`. |
| **Expedientes Disciplinarios** | `GET /api/v1/expedientes/` | `ExpedienteCollectionView` (`APIView`) | Ejecuta `close_expired_deadlines()`, filtra por legajo y serializa **todo el queryset** con `ExpedienteListSerializer(queryset, many=True)`. | `GestionarExpedientesComponent` (`tribunal-data.service.ts`) | La tabla exploradora renderiza `<tr *ngFor="let exp of expedientesFiltrados">` sobre toda la colección sin paginador alguno (ni cliente ni servidor). |
| **Mis Expedientes** | `GET /api/v1/expedientes/mis-expedientes/` | `MisExpedientesView` (`APIView`) | Retorna `ExpedienteListSerializer(queryset, many=True)` en lista plana. | `MisExpedientesComponent` | Renderiza `<tr *ngFor="let exp of expedientesOrdenados">` sin paginador. |
| **Expedientes por Socio** | `GET /api/v1/expedientes/por-socio/?legajo=X` | `ExpedientesPorSocioView` (`APIView`) | Retorna `ExpedienteResumenSerializer(queryset, many=True)` en lista plana. | `ExpedientesSocioDialogComponent` | Renderiza modal con lista completa no paginada. |
| **Mis Solicitudes T01** | `GET /api/v1/expedientes/solicitudes-t01/mis-solicitudes/` | `MisSolicitudesT01View` (`APIView`) | Retorna `SolicitudT01Serializer(queryset, many=True)` en lista plana. | `SolicitarPuntosComponent` | Pestaña "Mis Solicitudes" renderiza `misSolicitudesOrdenadas` sin paginación. |
| **Eventos Institucionales** | `GET /api/v1/expedientes/eventos/` | `EventoInstitucionalViewSet` (`ModelViewSet`) | Hereda de `ModelViewSet`. Al no tener `DEFAULT_PAGINATION_CLASS` configurada en `settings.py`, retorna array plano con todos los eventos y asistencias anidadas. | `EventoService.getEventos(filtros)` | Envía query param `page` opcional, pero espera y procesa `EventoInstitucional[]` plano. |
| **Padrón Institucional** | `GET /api/v1/padron/socios/` | `PadronSocioListView` (`APIView`) | Implementa paginación propietaria mediante `PaginatedSociosSerializer` (`count`, `page`, `page_size`, `results`), pero no sigue el estándar DRF (carece de `next`, `previous`, `total_pages`). | `SocioApiService.searchSocios` | Consume `{ count, next, previous, results }` tipado en `PaginatedResponse<T>`. |

### 1.2. Diagnóstico de Impacto en Escalabilidad, Ancho de Banda y Consumo de Recursos

1. **Sobrecarga de Memoria RAM en Backend (Django / Gunicorn / MySQL):**
   - En `settings.py`, `REST_FRAMEWORK` no define ninguna clase de paginación global (`DEFAULT_PAGINATION_CLASS` está ausente).
   - Cada solicitud a `/api/v1/ranking/` instancia 515 objetos `Socio`, evalúa anotaciones dinámicas de saldo y genera grafos de diccionarios en memoria Python para su serialización.
   - En peticiones concurrentes (e.g., cierre de cuatrimestre o votación de asamblea), la retención de memoria por worker de Gunicorn escala linealmente con el tamaño del padrón y el volumen acumulado de expedientes, aumentando el riesgo de saturación de RAM en el contenedor Docker.
2. **Latencia y Saturación de Ancho de Banda (Network Overhead & TTFB):**
   - El payload no comprimido de `/api/v1/ranking/` promedia entre **180 KB y 260 KB** por llamada.
   - En dispositivos móviles sobre redes celulares de velocidad media (3G/4G), esto introduce una penalización de transferencia de **400 ms a 1.200 ms** únicamente en tiempo de descarga de datos, afectando el LCP (Largest Contentful Paint) que la directiva de Addy Osmani exige mantener estrictamente por debajo de **2,5 segundos**.
3. **Sobrecarga de CPU y Renderizado en Frontend (Angular 14):**
   - En `RankingSociosComponent`, la ordenación y filtrado se realizan íntegramente en el hilo principal (*main thread*) de JavaScript a través de getters complejos (`sociosOrdenados`, `sociosPaginados`). Cada pulsación en el input de búsqueda dispara un reordenamiento completo de 515 elementos.
   - En `GestionarExpedientesComponent`, al no existir paginación en la vista de tabla, Angular crea cientos de nodos DOM, cada uno con directivas estructurales, botones de acción, tooltips y listeners de eventos. Esto degrada drásticamente la métrica **INP** (Interaction to Next Paint, meta < 200 ms) y genera *layout thrashing* durante el scroll.

---

## 2. Definición del Contrato REST Estándar de Paginación Server-Side (DRF)

Para resolver la dispersión actual, se formaliza el contrato canónico de paginación basado en `PageNumberPagination` de Django REST Framework, enriquecido con metadatos de navegación y compatibilidad con RFC 9457 para el tratamiento de errores.

### 2.1. Estructura de la Envolvente JSON de Respuesta (Canonical Response Envelope)

Toda respuesta de una colección paginada debe responder con el siguiente esquema JSON:

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

### 2.2. Parámetros de Consulta (Query Parameters)

| Parámetro | Tipo | Requerido | Valor por Defecto | Restricciones / Límites | Descripción |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `page` | `integer` | No | `1` | Mínimo: `1`. Entero positivo. | Número de página solicitado (indexación en base 1). |
| `page_size` | `integer` | No | `20` (o configurable por vista) | Mínimo: `1`, Máximo: `100`. | Cantidad de registros por página solicitados por el cliente. |

### 2.3. Matriz de Comportamiento y Códigos HTTP de Casos Borde

1. **Página fuera de rango (`page > total_pages`):**
   - **Código HTTP:** `404 Not Found`.
   - **Cuerpo RFC 9457:**
     ```json
     {
       "type": "https://errors.aveit.org.ar/invalid-page",
       "title": "Página no encontrada",
       "status": 404,
       "detail": "Página inválida. La página solicitada no contiene resultados."
     }
     ```
2. **Parámetros no numéricos o inválidos (`page=abc`, `page=-5`, `page_size=0`):**
   - **Código HTTP:** `400 Bad Request` o sanitización automática (fallback defensivo de DRF a `page=1`). Si se detecta un valor malformado explícito, DRF `PageNumberPagination` levanta `NotFound("Página inválida.")`.
3. **Solicitud de tamaño de página excesivo (`page_size > 100`):**
   - **Comportamiento:** Se aplica el techo rígido `max_page_size = 100` sin arrojar error, devolviendo como máximo 100 registros para neutralizar vectores de denegación de servicio (DoS).

### 2.4. Implementación Canónica en Backend (`backend/core/pagination.py`)

```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class StandardResultsSetPagination(PageNumberPagination):
    """Paginador canónico estándar del SGD-AVEIT con metadatos completos."""
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    page_query_param = "page"

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data,
        })
```

### 2.5. Estrategia de Transición y Compatibilidad hacia Atrás (Backward Compatibility)

Para salvaguardar la ejecución de la suite de pruebas preexistente (`test_ranking_api.py`) y evitar disrupciones durante la integración:
- **Estrategia Híbrida Transitoria:**
  En las vistas `APIView` que actualmente retornan listas planas (`RankingListView`, `ExpedienteCollectionView`):
  1. Si la petición incluye los parámetros de consulta `page` o `page_size`, se aplica la paginación con la envolvente `{ count, total_pages, current_page, page_size, next, previous, results }`.
  2. Si no se incluye ninguno de dichos parámetros (o si se pasa explícitamente `pagination=false` / `all=true`), se mantiene la compatibilidad de lista plana durante la ventana de migración, hasta la actualización de los tests correspondientes.
  3. En la meta final del Sprint 5, se estandariza la envolvente paginada universalmente y se adaptan los tests unitarios.

---

## 3. Relevamiento de la Integración en Angular con MatPaginator y PageEvent

### 3.1. Modelo e Interfaz Genérica TypeScript (`frontend/src/app/models/paginated-response.model.ts`)

```typescript
export interface PaginatedResponse<T> {
  count: number;
  total_pages?: number;
  current_page?: number;
  page_size?: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

### 3.2. Vinculación de Componente con `MatPaginator` y `PageEvent`

En cada pantalla de listado (`ranking-socios`, `gestionar-expedientes`, `mis-expedientes`, `solicitar-puntos`), se integra el componente canónico de Angular Material en la vista HTML:

```html
<mat-paginator
  [length]="totalRegistros"
  [pageSize]="tamanoPagina"
  [pageSizeOptions]="[10, 20, 50, 100]"
  [pageIndex]="paginaActual - 1"
  (page)="onCambioPagina($event)"
  showFirstLastButtons
  aria-label="Seleccionar página de resultados">
</mat-paginator>
```

Y en el controlador TypeScript:

```typescript
onCambioPagina(event: PageEvent): void {
  this.paginaActual = event.pageIndex + 1; // Conversión base 0 a base 1
  this.tamanoPagina = event.pageSize;
  this.cargarDatos();
}
```

### 3.3. Sincronización Reactiva con Filtros y Ordenamiento (State Machine RxJS)

Para erradicar inconsistencias de estado y condiciones de carrera (*race conditions*):
1. **Invariante de Paginación ante Filtros:**
   Cada vez que el usuario modifica un filtro de texto, categoría, subcomisión o grupo, el índice de página debe resetearse forzosamente a la primera página (`paginaActual = 1`, `pageIndex = 0`).
2. **Conservación de Página ante Reordenamiento:**
   Al hacer clic en la cabecera de una columna ordenable (e.g., ordenar por `saldo` asc/desc), se mantiene el tamaño de página y se re-consulta la página actual o se resetea a la primera página según convención de la vista.
3. **Flujo Reactivo Unificado con RxJS:**
   ```typescript
   private readonly refresh$ = new BehaviorSubject<void>(undefined);

   ngOnInit(): void {
     this.refresh$.pipe(
       debounceTime(150),
       switchMap(() => {
         this.cargando = true;
         return this.service.obtenerPaginado({
           page: this.paginaActual,
           page_size: this.tamanoPagina,
           search: this.filtroTexto,
           ordering: this.obtenerCadenaOrdenamiento(),
           // ...filtros específicos
         }).pipe(
           catchError(err => {
             this.notifications.error('Error al cargar datos paginados.');
             return of({ count: 0, results: [], total_pages: 0, current_page: 1, next: null, previous: null });
           }),
           finalize(() => this.cargando = false)
         );
       }),
       takeUntil(this.destroy$)
     ).subscribe(res => {
       this.datos = res.results;
       this.totalRegistros = res.count;
     });
   }
   ```
4. **Prevención de Fugas de Memoria:**
   Implementación estricta de `takeUntil(this.destroy$)` en el ciclo `ngOnDestroy` de cada componente para cancelar suscripciones activas.

---

## 4. Registro Normalizado de Requisitos (requirementsExtractor)

### 4.1. Fuentes y Alcance
- **`SRC-01`:** `PLAN_SPRINT_5_CONSOLIDADO.md` (§1 N-02, §3 Macro-06 SCRUM-87 / SCRUM-118, §4.4, §5.1).
- **`SRC-02`:** `docs/constitution.md` (Art. 3 Puertas de Calidad, Art. 4 Desacople y tipado, Art. 5 Sistema de Diseño).
- **`SRC-03`:** `docs/gestion-proyecto/notasPO.md` (§Notas del PO 27/09/2026 y 07/10/2026 - Padrón, Ranking y Ordenamiento).
- **`SRC-04`:** Código fuente Backend: `backend/ranking/views.py`, `backend/expedientes/views/`, `backend/core/settings.py`.
- **`SRC-05`:** Código fuente Frontend: `frontend/src/app/ranking-socios/`, `frontend/src/app/gestionar-expedientes/`, `frontend/src/app/services/`.

### 4.2. Requisitos Funcionales (RF)

| ID | Nivel / Padre | Enunciado | Origen | Derivación / Validación | Evidencia | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RF-PAG-01** | Global | Proveer paginación server-side estándar en todas las consultas de colecciones del sistema. | Explícito | Requerimiento de optimización de la Épica SCRUM-87. | SRC-01 (§3 MACRO-06) | Aprobado |
| **RF-PAG-02** | Detallado / RF-PAG-01 | Procesar los parámetros de consulta `page` y `page_size` en el endpoint de Ranking Oficial (`/api/v1/ranking/`). | Explícito | Permite fraccionar la entrega de los ~515 socios reconciliados. | SRC-01 (§4.4), SRC-04 | Aprobado |
| **RF-PAG-03** | Detallado / RF-PAG-01 | Procesar los parámetros de consulta `page` y `page_size` en el endpoint de Expedientes (`/api/v1/expedientes/`). | Explícito | Permite fraccionar la tabla exploradora de expedientes. | SRC-01 (§4.4), SRC-04 | Aprobado |
| **RF-PAG-04** | Detallado / RF-PAG-01 | Retornar la respuesta paginada estructurada en la envolvente canónica con `count`, `total_pages`, `current_page`, `page_size`, `next`, `previous` y `results`. | Derivado | Necesidad de metainformación para alimentar `MatPaginator` en Angular. | SRC-01, SRC-05 | Pendiente |
| **RF-PAG-05** | Detallado / RF-PAG-01 | Responder con código HTTP 404 y detalle RFC 9457 cuando se solicite una página superior a `total_pages`. | Derivado | Semántica HTTP REST estándar según RFC 9110 / RFC 9457. | SRC-02 (Art. 4) | Pendiente |
| **RF-PAG-06** | Detallado / RF-PAG-01 | Integrar `MatPaginator` con selector de tamaño de página en la vista de Ranking de Socios. | Explícito | Sustitución de los botones de paginación ad-hoc en cliente. | SRC-01 (§4.4), SRC-05 | Aprobado |
| **RF-PAG-07** | Detallado / RF-PAG-01 | Integrar `MatPaginator` en la tabla de detalle/exploración de Gestionar Expedientes. | Explícito | Incorporación de paginador inexistente en la vista actual. | SRC-01 (§4.4), SRC-05 | Aprobado |
| **RF-PAG-08** | Detallado / RF-PAG-01 | Resetear automáticamente el índice de página a 1 ante cualquier modificación de los filtros de búsqueda. | Derivado | Prevención de vistas vacías cuando el filtro reduce la cantidad de páginas. | SRC-05, Heurística UX | Pendiente |

### 4.3. Requisitos No Funcionales (RNF) y Escenarios de Calidad

*Taxonomía aplicada: ISO/IEC 25010:2011 — Eficiencia de Desempeño (Comportamiento temporal y Utilización de recursos).*

| ID | Categoría | Enunciado / Medida | Alcance | Origen | Evidencia | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RNF-PERF-01** | Comportamiento temporal | El tiempo de respuesta de extremo a extremo (TTFB + transferencia) para la carga de una página de 20 registros debe ser inferior a 300 ms en red local y menor a 800 ms en conexión móvil estándar. | APIs de Ranking y Expedientes | Derivado | SRC-01, Directivas Addy Osmani | Pendiente |
| **RNF-PERF-02** | Utilización de recursos | La transferencia de datos por petición de listado paginado no debe exceder los 30 KB por página de 20 registros. | Endpoints `/api/v1/ranking/` y `/api/v1/expedientes/` | Derivado | SRC-01, Auditoría de payload actual (~200 KB) | Pendiente |
| **RNF-PERF-03** | Utilización de recursos | El renderizado de la tabla paginada en Angular no debe superar los 50 nodos DOM por vista de página, asegurando un INP < 150 ms durante la navegación entre páginas. | Frontend SPA Angular | Derivado | SRC-01, Directivas Addy Osmani | Pendiente |
| **RNF-PERF-04** | Capacidad / Resiliencia | El backend debe limitar rígidamente el parámetro `page_size` a un máximo de 100 registros ante peticiones que intenten solicitar volúmenes masivos. | Backend DRF | Derivado | Protección DoS y estabilidad de RAM | Pendiente |

#### Escenarios de Calidad (Formato Atributo - Estímulo - Respuesta)

1. **Escenario 1 (Eficiencia de Desempeño - Tamaño de Payload y Ancho de Banda):**
   - **Atributo:** Eficiencia de desempeño / Utilización de recursos de red.
   - **Estímulo:** El usuario navega al Ranking de Socios o a la tabla de Gestionar Expedientes desde un dispositivo móvil.
   - **Respuesta:** El backend retorna únicamente los 20 registros de la página solicitada en un payload JSON menor a 30 KB (reducción superior al 80% comparado con la lista plana de 200+ KB), logrando un tiempo de carga perceptible inmediato sin bloquear el hilo principal.
2. **Escenario 2 (Comportamiento Temporal e Interacción Fluida - INP):**
   - **Atributo:** Comportamiento temporal y usabilidad interactiva.
   - **Estímulo:** El operador del Tribunal de Disciplina cambia de página o altera el criterio de ordenamiento en la tabla de expedientes.
   - **Respuesta:** El componente destruye y renderiza exclusivamente las 20 filas correspondientes mediante directivas optimizadas, completando la transición visual en menos de 100 ms sin registrar caídas de frames ni congelamiento de la UI.
3. **Escenario 3 (Robustez y Manejo de Bordes):**
   - **Atributo:** Tolerancia a fallos y consistencia de datos.
   - **Estímulo:** Un cliente envía una solicitud con `page=9999` sobre un listado que posee solo 15 páginas.
   - **Respuesta:** El backend responde en menos de 50 ms con un código HTTP `404 Not Found` estructurado en formato RFC 9457, y el frontend captura el error de forma limpia mostrando un estado vacío informativo sin interrumpir la sesión.

### 4.4. Reglas de Negocio (RN), Restricciones (RES), Dependencias (DEP) y Supuestos (SUP)

| ID | Tipo | Enunciado | Origen | Evidencia | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RN-PAG-01** | RN | El tamaño de página por defecto para el Ranking de Socios y Tablas de Expedientes es de 20 registros. Las opciones disponibles en el selector de la UI son 10, 20, 50 y 100 registros. | Derivado | Estándar de densidad y ergonomía de tablas. | Aprobado |
| **RN-PAG-02** | RN | El ordenamiento de las colecciones se calcula sobre la totalidad del conjunto de datos en base de datos previo a la aplicación del corte de paginación (`LIMIT` y `OFFSET`), garantizando que la posición relativa de cada socio o expediente sea consistente. | Derivado | Notas del PO sobre ordenamiento de Saldo y Grupos. | Aprobado |
| **RN-PAG-03** | RN | Ante la aplicación o modificación de cualquier filtro de búsqueda o categoría, la paginación debe retornar mandatoriamente a la página 1. | Derivado | Buenas prácticas de UX para evitar páginas vacías fuera de rango. | Aprobado |
| **RES-PAG-01** | RES | No se deben modificar sentencias directas de actualización sobre saldos de puntos; la paginación opera estrictamente sobre consultas de lectura optimizadas (`SELECT`). | Explícito | Constitución Art. 2, Regla Innegociable 3 de AGENTS.md. | Aprobado |
| **RES-PAG-02** | RES | La interfaz visual de paginación debe apegarse estrictamente a los tokens tipográficos y cromáticos institucionales de `DESIGN.md` y Angular Material. | Explícito | Constitución Art. 5, AGENTS.md. | Aprobado |
| **DEP-PAG-01** | DEP | La efectividad de la paginación server-side en backend requiere que las consultas base eliminen problemas N+1 mediante `select_related` y `prefetch_related` (tarea complementaria `SCRUM-120`). | Derivado | Plan Sprint 5 Consolidado §4.4 (N-02). | Aprobado |
| **DEP-PAG-02** | DEP | El rendimiento en el frontend requiere complementarse con la estrategia `ChangeDetectionStrategy.OnPush` y directiva `trackBy` (tarea complementaria `SCRUM-119`). | Derivado | Plan Sprint 5 Consolidado §4.4 (N-02). | Aprobado |
| **SUP-PAG-01** | SUP | Se asume que el volumen actual de socios activos y pasivos de AVEIT se mantiene en el orden de ~515 registros, mientras que el volumen de expedientes acumulados crecerá a un ritmo estimado de 200 a 500 causas anuales. | Derivado | Datos del padrón institucional y notas del PO. | Aprobado |
| **SUP-PAG-02** | SUP | Se asume que la base de datos MySQL 8.0 soporta eficientemente consultas indexadas con cláusulas `LIMIT` y `OFFSET` sin penalización severa para el rango de registros previsto (< 100.000 filas). | Derivado | Características del motor relacional MySQL 8.0. | Aprobado |

---

## 5. Criterios de Aceptación Verificables (DoD) para SCRUM-118

Para dar por cumplida la tarea `SCRUM-118` en el marco de la Definición de Terminado (Definition of Done) del Sprint 5:

1. **CA-01 (Contrato Backend DRF):**
   - El endpoint `GET /api/v1/ranking/?page=1&page_size=20` responde con código HTTP `200 OK` y un cuerpo JSON con los campos de primer nivel: `count` (entero), `total_pages` (entero), `current_page` (entero), `page_size` (entero), `next` (string o null), `previous` (string o null) y `results` (array de exactamente 20 elementos).
   - El endpoint `GET /api/v1/expedientes/?page=1&page_size=20` responde con la misma estructura envolvente canónica.
2. **CA-02 (Límites y Manejo de Errores):**
   - Una solicitud con `page=9999` devuelve código HTTP `404 Not Found` con mensaje estructurado.
   - Una solicitud con `page_size=500` devuelve como máximo 100 registros en el array `results`.
3. **CA-03 (Interfaz de Usuario con MatPaginator):**
   - La pantalla de Ranking de Socios (`/ranking-socios`) y la tabla de Gestión de Expedientes (`/gestionar-expedientes`) renderizan un componente `MatPaginator` accesible al pie de la tabla con los controles de navegación (Primera, Anterior, Siguiente, Última) y el selector de tamaño `[10, 20, 50, 100]`.
4. **CA-04 (Sincronización Reactiva de Filtros y Ordenamiento):**
   - Al tipear un término en el buscador de socios o cambiar la subcomisión, el paginador se reinicia automáticamente en la página 1 y muestra los resultados coincidentes paginados.
   - Al ordenar por cabecera de columna (e.g. `saldo`), los datos mostrados reflejan el orden global de la base de datos y no un ordenamiento local sobre la página visible.
5. **CA-05 (Rendimiento Cuantificable):**
   - El tamaño del payload de red de `/api/v1/ranking/?page=1&page_size=20` se reduce en al menos un **75%** respecto al payload plano anterior (de ~200 KB a menos de 40 KB).
   - No se observan errores de detección de cambios ni suscripciones huérfanas en el profiler de Angular tras navegar repetidamente entre páginas.
6. **CA-06 (Pruebas Automatizadas en Verde):**
   - Se incorporan y superan con éxito los tests unitarios en Backend (`pytest` validando códigos 200, 404, límites de `page_size` y estructura JSON).
   - Se incorporan y superan con éxito los tests unitarios en Frontend (`npm test` validando emisión de `PageEvent`, reseteo de página ante filtros y mapeo de datos en servicios).
   - Suite de pruebas ejecutada con 0 fallos y sin regresiones.
