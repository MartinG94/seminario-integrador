# Spec 010 — Optimización Integral de Rendimiento de la Plataforma (SCRUM-87)
## MACRO-06: Rendimiento de RAM, CPU y Base de Datos (Sprint 5)

> **Épica:** SCRUM-87 (MACRO-06)  
> **Subtareas Consolidadas:**  
> - **SCRUM-118:** S5-06.1 - Paginación server-side en Backend y Frontend  
> - **SCRUM-119:** S5-06.2 - Optimización Angular OnPush, trackBy y Ciclo de Vida (RxJS)  
> - **SCRUM-120:** S5-06.3 - Optimización Django ORM y eliminación de N+1  
> **Proyecto:** Sistema de Gestión Disciplinaria y Premiaciones — SGD-AVEIT (UTN FRC)  
> **Rama de Trabajo:** `feature/SCRUM-87-optimizacion-rendimiento`  
> **Estado:** Especificado y Consolidado bajo metodología Spec-Driven Development (SDD)  
> **Referencias Rectoras:**  
> - Constitución SGD-AVEIT (`docs/constitution.md`)  
> - Reglas Innegociables de Desarrollo (`AGENTS.md`)  
> - Notas del Product Owner (`docs/gestion-proyecto/notasPO.md` - 27/09/2026 y 07/10/2026)  
> - Plan de Implementación Sprint 5 Consolidado (`PLAN_SPRINT_5_CONSOLIDADO.md`, §1 N-02, §3 Macro-06)  
> - Sistema de Diseño Institucional (`DESIGN.md`)  
> - Estándares Addy Osmani Web Performance (LCP < 2.5s, INP < 200ms, CLS < 0.1)  
> - Estándar ISO/IEC 25010:2011 (Eficiencia de Desempeño y Mantenibilidad)

---

## 1. Contexto y Objetivos del Negocio

El Sistema de Gestión Disciplinaria (SGD-AVEIT) gestiona el padrón institucional (~515 socios activos y pasivos), expedientes colegiados, descargos tipificados (T02/T03) y cómputo transaccional de saldos de puntos.

A medida que el volumen acumulado de expedientes y asistencias ha crecido a lo largo de los sprints 1 a 4, se han identificado tres cuellos de botella sistémicos:
1. **Sobrecarga en Red y Memoria (Ausencia de Paginación Server-Side):** Las consultas a `/api/v1/ranking/`, `/api/v1/expedientes/` y `/api/v1/expedientes/eventos/` retornan listas planas de cientos de objetos (payloads de 180 a 260 KB). Esto penaliza el tiempo de carga en dispositivos móviles y satura la memoria del backend y del navegador.
2. **Bloqueo del Hilo Principal en Frontend (Angular Default Change Detection y DOM Masivo):** El 94.4% de los componentes se ejecutan bajo `ChangeDetectionStrategy.Default`. Componentes como `RankingSociosComponent` evalúan getters impuros con filtros y ordenamientos en cada ciclo de Zone.js, mientras que el 92% de las directivas `*ngFor` carecen de `trackBy`, forzando la destrucción y recreación íntegra de cientos de nodos DOM. Adicionalmente, existen suscripciones RxJS huérfanas que retienen memoria Heap (*memory leaks*).
3. **Ineficiencia en Persistencia (Consultas N+1 y Carga de Binarios BLOB):** Endpoints como el listado de eventos institucionales disparan 62 consultas SQL para 20 registros ($3N$ consultas en conteos de asistencias); el catálogo de antecedentes ejecuta 101 consultas ($O(N)$ puro); y las consultas de expedientes descargan archivos binarios de hasta 5 MB (`contenido_blob`) cuando solo se requieren metadatos.

### Objetivo General de la Épica:
Alcanzar una plataforma de alto rendimiento, escalable y ergonómica mediante:
- Paginación server-side canónica en DRF integrada con `MatPaginator` en Angular 14.
- Adopción universal de `ChangeDetectionStrategy.OnPush`, funciones `trackBy` y protocolo estricto de desuscripción `takeUntil(this.destroy$)`.
- Optimización de consultas ORM a complejidad constante $O(1)$ sin modificar en absoluto el esquema legacy MySQL 8.0 (`managed = False`, CERO DDL).

---

## 2. Historias de Usuario

### HU-01: Navegación Eficiente en Listados y Tablas Institucionales
**Como** integrante del Tribunal de Disciplina o Comisión Directiva,  
**quiero** navegar por el Ranking de Socios, el Tablero de Expedientes y la nómina de Eventos en páginas de tamaño configurable (10, 20, 50, 100),  
**para** consultar la información de manera ágil sin demoras ni congelamiento visual de la interfaz.

### HU-02: Experiencia Fluida en Dispositivos Móviles (Mobile-First)
**Como** socio activo o pasivo de AVEIT accediendo desde mi teléfono móvil,  
**quiero** consultar "Mis Expedientes" y el estado de mis puntos con un consumo mínimo de datos móviles,  
**para** verificar mis causas de inmediato con un tiempo de carga inicial menor a 2.5 segundos.

### HU-03: Estabilidad y Eficiencia de Recursos del Servidor
**Como** Administrador del Sistema (Subcomisión de Cómputos),  
**quiero** que las peticiones a la API ejecuten un número constante y acotado de consultas SQL ($O(1)$) y no retengan archivos binarios pesados en memoria RAM,  
**para** garantizar la alta disponibilidad y evitar la saturación de los contenedores Docker bajo concurrencia.

---

## 3. Requisitos en Notación EARS (Easy Approach to Requirements Syntax)

### 3.1. Requisitos Ubicuos (Ubiquitous Requirements)

1. **`EARS-U01` (Envolvente Canónica de Paginación):**  
   El sistema *debe* estructurar todas las respuestas de colecciones paginadas bajo el esquema estándar de 7 campos: `count` (entero), `total_pages` (entero), `current_page` (entero), `page_size` (entero), `next` (string o null), `previous` (string o null) y `results` (array de objetos).
2. **`EARS-U02` (Complejidad de Persistencia $O(1)$):**  
   El sistema *debe* resolver la persistencia de todos los endpoints de listado paginado en una cantidad constante de consultas SQL ($O(1)$) independiente del volumen total de registros $N$ almacenados en la base de datos.
3. **`EARS-U03` (Estrategia OnPush Universal):**  
   El sistema *debe* declarar `changeDetection: ChangeDetectionStrategy.OnPush` en el 100% de los componentes de presentación y contenedores de la SPA.
4. **`EARS-U04` (Identidad de Nodos con trackBy):**  
   El sistema *debe* vincular una función `trackBy` con clave unívoca de entidad (`id`, `legajo` o valor primitivo) en todas las directivas `*ngFor` de plantillas HTML.
5. **`EARS-U05` (Inmutabilidad del Esquema Legacy - Regla 6):**  
   El sistema *debe* interactuar con el motor MySQL 8.0 respetando estrictamente los nombres de tablas, columnas y tipos del padrón y ranking legado (`socio_*`, `tribunal_*`), manteniendo `managed = False` y CERO sentencias DDL.
6. **`EARS-U06` (Preservación del Servicio Centralizado de Notificaciones):**  
   La optimización de componentes y ciclo de vida *no debe* alterar la duración de 10 segundos, el desvanecimiento, el temporizador independiente ni el posicionamiento inferior derecho de las notificaciones transitorias (PR #49).
7. **`EARS-U07` (Alineación con Sistema de Diseño AVEIT):**  
   Todos los elementos de interfaz incorporados (incluyendo `MatPaginator`) *deben* consumir exclusivamente los tokens de diseño y gradientes especificados en `DESIGN.md`.

### 3.2. Requisitos Disparados por Eventos (Event-driven Requirements)

1. **`EARS-E01` (Procesamiento de Parámetros de Paginación):**  
   CUANDO el cliente envíe una petición `GET` a `/api/v1/ranking/`, `/api/v1/expedientes/`, `/api/v1/expedientes/mis-expedientes/` o `/api/v1/expedientes/eventos/` con los parámetros `page` y `page_size`, el backend *debe* fraccionar la consulta mediante `LIMIT` y `OFFSET` y retornar la envolvente canónica.
2. **`EARS-E02` (Reinicio Automático de Página ante Filtros):**  
   CUANDO el usuario modifique cualquier filtro de búsqueda textual, categoría estatutaria, subcomisión o estado procesal en el frontend, el sistema *debe* resetear automáticamente el índice de paginación a la página 1 (`pageIndex = 0`).
3. **`EARS-E03` (Ordenamiento Global en Base de Datos):**  
   CUANDO el usuario solicite un ordenamiento por cabecera de columna (ej. `saldo`, `apellido`, `grupo`), el sistema *debe* remitir el parámetro `ordering` al servidor para que el orden se aplique sobre la totalidad del conjunto en base de datos previo a la paginación.
4. **`EARS-E04` (Cancelación de Suscripciones en Desmontaje):**  
   CUANDO un componente Angular se destruya (`ngOnDestroy`), el sistema *debe* emitir y completar su sujeto `destroy$` cancelando de inmediato todas las peticiones HTTP en vuelo y temporizadores activos.
5. **`EARS-E05` (Diferimiento de Archivos Binarios Pesados):**  
   CUANDO se consulten listados de expedientes o se construya el tablero de causas, el sistema *debe* diferir la selección de la columna `contenido_blob` (`defer("contenido_blob")`) en el prefetch de evidencias.
6. **`EARS-E06` (Anotación Condicional de Asistencias en Eventos):**  
   CUANDO se liste la colección de eventos institucionales, el sistema *debe* calcular los totales de convocados, presentes y ausentes mediante anotaciones condicionales `Count(..., filter=Q(...))` en el QuerySet base, resolviendo la petición en un máximo de 3 consultas SQL.
7. **`EARS-E07` (Subquery de Fecha de Emisión en Antecedentes):**  
   CUANDO se consulte el catálogo de antecedentes emitidos (`/api/v1/expedientes/antecedentes/?catalogo=1`), el sistema *debe* calcular la fecha de emisión del último estado emitido mediante una `Subquery` correlacionada indexada, ejecutando exactamente una (1) única consulta SQL.

### 3.3. Requisitos Conducidos por Estado (State-driven Requirements)

1. **`EARS-S01` (Actualización de Vista bajo OnPush):**  
   MIENTRAS un componente opere bajo `ChangeDetectionStrategy.OnPush`, cualquier modificación de estado interna proveniente de respuestas asíncronas no ligadas al pipe `async` *debe* invocar `cdr.markForCheck()` para programar la verificación visual.
2. **`EARS-S02` (Aislamiento del Ticker de Reloj):**  
   MIENTRAS el cronómetro de plazos procesales esté activo en `MisExpedientesComponent`, sus emisiones periódicas cada un segundo *deben* actualizar exclusivamente el badge de tiempo mediante `markForCheck()` local sin despertar la detección de cambios global de la aplicación.

### 3.4. Requisitos de Manejo de Errores y Comportamientos No Deseados (RFC 9457)

1. **`EARS-W01` (Página Fuera de Rango):**  
   SI el cliente envía una petición con un número de página superior al total disponible (`page > total_pages`), el backend *debe* responder con código HTTP `404 Not Found` y un cuerpo estructurado bajo el estándar RFC 9457 con `type: "https://errors.aveit.org.ar/invalid-page"`.
2. **`EARS-W02` (Techo Rígido de Tamaño de Página):**  
   SI el cliente envía un parámetro `page_size` superior a 100, el backend *debe* acotar automáticamente la entrega a 100 registros sin arrojar error, neutralizando vectores de denegación de servicio (DoS).
3. **`EARS-W03` (Parámetros de Paginación Malformados):**  
   SI el cliente envía valores no enteros o negativos en `page` o `page_size`, el backend *debe* capturar la excepción y responder con HTTP `400 Bad Request` o retornar la primera página con los valores por defecto.

---

## 4. Escenarios de Calidad Verificables (ISO/IEC 25010 y Core Web Vitals)

### 4.1. Matriz de Atributos de Calidad

| ID | Estándar / Atributo | Métrica Cuantificable | Umbral Exigido | Método de Medición |
| :--- | :--- | :--- | :--- | :--- |
| **`ESC-01`** | Addy Osmani / INP | Interaction to Next Paint | **< 200 ms** (P75) | Chrome DevTools Performance Profiler en filtrado y ordenamiento de 515 socios. |
| **`ESC-02`** | Addy Osmani / LCP | Largest Contentful Paint | **< 2.5 s** | Chrome DevTools Lighthouse / Performance en red 4G simulada. |
| **`ESC-03`** | Addy Osmani / CLS | Cumulative Layout Shift | **< 0.1** | Medición de desplazamiento de layout durante la renderización de tablas. |
| **`ESC-04`** | ISO 25010 / Utilización Red | Tamaño de Payload HTTP | **< 35 KB** por página ($k=20$) | Inspección de red (Network Tab) en `/api/v1/ranking/?page=1&page_size=20`. |
| **`ESC-05`** | ISO 25010 / Memoria Cliente | Retención de Heap y Fugas | **$\Delta \le 0.5\text{ MB}$** tras 10 navegaciones; **0 Detached DOM Nodes** | Chrome Memory Profiler (Heap Snapshot comparativo tras forzar GC). |
| **`ESC-06`** | ISO 25010 / Persistencia BD | Consultas SQL por Petición | **$O(1)$ estricto**; Eventos $\le 3$; Antecedentes $= 1$; Gestión $\le 8$ | Pytest con `django_assert_num_queries` y `CaptureQueriesContext`. |
| **`ESC-07`** | ISO 25010 / Memoria Backend | RAM por worker Gunicorn | Incremento **$< 5\text{ MB}$** en serialización de expedientes | Monitoreo de memoria del proceso Django/Gunicorn con evidencias adjuntas. |

### 4.2. Escenarios Formales (Atributo — Estímulo — Respuesta)

```
[ESC-CAL-01] Tiempo de Interacción en Filtrado de Padrón (INP)
- Atributo: Eficiencia de Desempeño / Comportamiento temporal (ISO 25010 §4.2.1).
- Estímulo: El operador ingresa caracteres de búsqueda en el Ranking de Socios (~515 registros).
- Respuesta: Angular evalúa el evento mediante flujos reactivos con debounce (150 ms) y emite la consulta paginada al backend. Al recibir los 20 registros, actualiza exclusivamente las filas modificadas utilizando trackBy.
- Medición: El tiempo de respuesta de interacción (INP) es menor a 150 ms y el tiempo de scripting en CPU es menor a 50 ms por tecla.
```

```
[ESC-CAL-02] Aislamiento de Memoria RAM en Transferencia de Expedientes
- Atributo: Eficiencia de Desempeño / Utilización de recursos (ISO 25010 §4.2.2).
- Estímulo: Se solicita el listado de expedientes (/api/v1/expedientes/?page=1&page_size=20) en una base de datos con 50 expedientes que contienen evidencias adjuntas de 2 MB a 5 MB cada una.
- Respuesta: El prefetch de evidencias aplica defer("contenido_blob"), seleccionando únicamente id, nombre, mime y hash.
- Medición: El consumo de memoria del proceso Django no supera los 500 KB para atender la petición, y el payload JSON transferido al cliente no excede los 30 KB.
```

```
[ESC-CAL-03] Navegación Cíclica Libre de Memory Leaks
- Atributo: Eficiencia de Desempeño / Capacidad y Mantenibilidad (ISO 25010 §4.2.3).
- Estímulo: Un usuario navega 10 veces de manera consecutiva entre /ranking-socios, /gestionar-expedientes y /mis-expedientes.
- Respuesta: En cada transición de ruta, el componente desmontado ejecuta ngOnDestroy(), dispara destroy$.next() y cancela todas las suscripciones HTTP y timers.
- Medición: Al forzar el Garbage Collector en el Heap Snapshot, no existen instancias retenidas de componentes destruidos ni nodos DOM huérfanos. La variación neta de memoria es menor o igual a 0.5 MB.
```

---

## 5. Contrato de Integración API REST Canónico

### 5.1. Estructura de la Envolvente JSON de Respuesta (`200 OK`)

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

### 5.2. Parámetros de Consulta Soportados

| Parámetro | Tipo | Requerido | Valor por Defecto | Restricción | Descripción |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `page` | Integer | No | `1` | $\ge 1$ | Número de página solicitado (indexación en base 1). |
| `page_size` | Integer | No | `20` | $1 \le \text{page\_size} \le 100$ | Cantidad de registros devueltos por página. |
| `ordering` | String | No | `-updated_at` / `-saldo` | Campos válidos según vista | Ordenamiento global (prefijo `-` para descendente). |
| `search` | String | No | None | Longitud $\le 100$ | Búsqueda textual sobre campos habilitados. |

### 5.3. Esquema de Errores RFC 9457 (`404 Not Found`)

```json
{
  "type": "https://errors.aveit.org.ar/invalid-page",
  "title": "Página no encontrada",
  "status": 404,
  "detail": "Página inválida. La página solicitada no contiene resultados.",
  "instance": "/api/v1/ranking/?page=9999&page_size=20"
}
```

---

## 6. Criterios de Aceptación Globales de la Épica (Definition of Done)

Para declarar formalmente concluida y aprobada la Épica **SCRUM-87**:

- [ ] **DoD-01 (Paginación Server-Side):** Los endpoints `/api/v1/ranking/`, `/api/v1/expedientes/`, `/api/v1/expedientes/mis-expedientes/` y `/api/v1/expedientes/eventos/` retornan la envolvente canónica `{ count, total_pages, current_page, page_size, next, previous, results }` y respetan el límite de `page_size <= 100`.
- [ ] **DoD-02 (MatPaginator Integrado):** La pantalla de Ranking de Socios, la tabla de Gestión de Expedientes y la tabla de Mis Expedientes exhiben el componente `MatPaginator` con selector de tamaño `[10, 20, 50, 100]`, reseteo automático a página 1 en filtros y preservación del diseño de `DESIGN.md`.
- [ ] **DoD-03 (OnPush y trackBy 100%):** El 100% de los componentes principales declaran `ChangeDetectionStrategy.OnPush` y el 100% de las directivas `*ngFor` implementan funciones `trackBy` mediante `TrackByUtils`.
- [ ] **DoD-04 (Eliminación de Getters Computados):** Ningún componente ejecuta `sort()` o `filter()` de arrays dentro de getters invocados en plantillas HTML.
- [ ] **DoD-05 (Cero Fugas de Memoria en Frontend):** Todas las suscripciones manuales a observables implementan `.pipe(takeUntil(this.destroy$))` en `ngOnDestroy`. El delta de Heap en 10 navegaciones cíclicas es $\le 0.5\text{ MB}$ con 0 detached DOM nodes.
- [ ] **DoD-06 (Erradicación de N+1 en Persistencia):**
  - Eventos institucionales: de 62 a $\le 3$ consultas SQL.
  - Catálogo de antecedentes: de 101 a exactamente 1 consulta SQL.
  - Expedientes: prefetch diferido con `defer("contenido_blob")` sin cargar archivos binarios en memoria.
- [ ] **DoD-07 (Salvaguarda del Esquema Legacy - Regla 6):** Cero mutaciones DDL, cero migraciones sobre tablas legacy (`socio_*`, `tribunal_*`) y `managed = False` inalterado.
- [ ] **DoD-08 (Suites de Pruebas Automatizadas en Verde):**
  - Backend: `pytest -q` finaliza con 0 fallos, incorporando tests de persistencia y número de queries con `django_assert_num_queries`.
  - Frontend: `npm test` finaliza con 0 fallos, validando desmonte de componentes, emisión de `PageEvent` y reactividad de filtros.
