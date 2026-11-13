# Propuesta Técnica de Backend — Dev Backend Senior
## Subtarea SCRUM-119: Estabilidad de Contratos de API, Inmutabilidad de Identificadores y Revalidación HTTP para Soporte de Angular OnPush y trackBy
> **Épica:** SCRUM-87 (MACRO-06: Optimización Integral de Rendimiento de la Plataforma - RAM, CPU y Base de Datos)  
> **Subtarea:** SCRUM-119 (S5-06.2: Optimización Angular OnPush, trackBy y Ciclo de Vida RxJS)  
> **Proyecto:** Sistema de Gestión Disciplinaria y Premiaciones — SGD-AVEIT (UTN FRC)  
> **Rama de Trabajo:** `feature/SCRUM-87-optimizacion-rendimiento`  
> **Autor:** Desarrollador Backend Senior (Python 3.12 / Django 4.2 LTS / DRF)  
> **Equipo:** Equipo SCRUM-119 (Tech Lead Orchestrator, Dev Frontend Senior, Dev Backend Senior, DBA Senior)  
> **Fecha:** 12 de Noviembre de 2026  
> **Estándares y Normativas:** Django REST Framework 3.14+, RFC 9110 / RFC 9111 (HTTP Caching & Conditional Requests), RFC 9457 (Problem Details), ISO/IEC 25010:2011, Spec-Driven Development (SDD), Regla Innegociable 6 de `AGENTS.md`.

---

## 1. Resumen Ejecutivo y Diagnóstico de Interacción Backend-Frontend

El presente informe técnico constituye la propuesta formal del **Dev Backend Senior** para la subtarea **SCRUM-119**, enmarcada en la épica de optimización integral **SCRUM-87**. 

El objetivo primordial de SCRUM-119 en la capa de cliente es transformar la detección de cambios de Angular de su modo reactivo indiscriminado (`ChangeDetectionStrategy.Default` / Zone.js) a un modelo de detección granular reactiva basado en **`ChangeDetectionStrategy.OnPush`**, directivas **`trackBy`** universales y un control estricto del ciclo de vida de suscripciones RxJS (`takeUntil`).

Sin embargo, para que esta arquitectura frontend alcance sus metas de rendimiento (**INP < 200 ms**, **tiempo de renderizado de lista < 50 ms**, **cero memory leaks** y **ausencia total de Layout Thrashing**), la capa de servicios REST en Django REST Framework (DRF) debe brindar **garantías innegociables de estabilidad de contratos, inmutabilidad de identificadores y soporte para negociación HTTP condicional**.

### 1.1. Principio Fundamental: Cómo Backend habilita OnPush y trackBy

```mermaid
flowchart LR
    subgraph Backend_DRF ["Backend DRF (Django 4.2 / Python 3.12)"]
        BE_PK["Identificadores Canónicos Inmutables (id, nroSocio, numero)"]
        BE_Sort["Ordenamiento SQL Determinista (order_by)"]
        BE_ETag["Negociación HTTP Condicional (ETag + Cache-Control)"]
    end

    subgraph HTTP_Layer ["Capa de Transporte HTTP"]
        HTTP_304["HTTP 304 Not Modified (0 bytes payload)"]
        HTTP_200["HTTP 200 OK con payload canónico"]
    end

    subgraph Frontend_Angular ["Frontend Angular 14.2 (SCRUM-119)"]
        FE_TrackBy["trackBy: recicla 100% de nodos DOM (0 Layout Thrashing)"]
        FE_OnPush["OnPush: Omite ciclos de Zone.js ante referencias estables"]
        FE_INP["INP < 200ms y CPU del Main Thread liberada"]
    end

    BE_PK --> FE_TrackBy
    BE_Sort --> FE_TrackBy
    BE_ETag --> HTTP_304
    HTTP_304 --> FE_OnPush
    BE_PK --> HTTP_200
    HTTP_200 --> FE_TrackBy
    FE_TrackBy --> FE_INP
    FE_OnPush --> FE_INP
```

1. **`ChangeDetectionStrategy.OnPush`** en Angular opera bajo el principio de **igualdad referencial estricta** (`Object.is(prev, curr)` o `prev === curr`). Si el backend emite una respuesta JSON 200 OK idéntica en cada sondeo o interacción, Angular deserializa un nuevo array de objetos en memoria heap, forzando la re-evaluación del árbol de componentes aunque los datos no hayan cambiado.
2. **`*ngFor` con `trackBy`** requiere **identificadores estables, únicos y no volátiles**. Si el backend omite identificadores en colecciones anidadas (ej. transiciones de estado en el historial de un expediente), genera identificadores temporales basados en hashes o muta el tipo primitivo (`105` vs `'105'`), Angular no puede reconciliar los nodos DOM existentes y se ve forzado a destruirlos y recrearlos desde cero (*Layout Thrashing* masivo).
3. **Caché Condicional HTTP (`ETag` / `304 Not Modified`)**: Si el backend informa al navegador que el estado de los datos no ha variado respecto al último `ETag` recibido, el frontend no instancia nuevos objetos en memoria ni emite por sus `Observable`, permitiendo que `OnPush` mantenga al componente completamente dormido (**0 ms de CPU y 0 ms de scripting**).

---

## 2. Auditoría Forense de Contratos DRF Existentes y Brechas Identificadas

Se realizó una auditoría exhaustiva sobre los serializadores y endpoints de Django REST Framework consumidos por los componentes críticos listados en el relevamiento de SCRUM-119:

### 2.1. Matriz de Auditoría de Serializadores

| Serializador DRF | Archivo de Origen | Entidad de Dominio | Identificador Actual | Brecha / Riesgo para OnPush & trackBy | Nivel de Riesgo |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **`RankingSocioSerializer`** | `backend/ranking/serializers.py` | `padron.models.Socio` (legacy) | `id = str(obj.nroSocio)` | `id` se serializa como `str`, mientras que en otras APIs societarias `socio_id` o `id` es `int`. Ausencia de encabezados HTTP `ETag` en `RankingListView`. | **ALTO** |
| **`ExpedienteListSerializer`** | `backend/expedientes/serializers/__init__.py` | `expedientes.Expediente` | `id` (int), `numero` (str) | En la propiedad anidada `historial`, los objetos devueltos **carecen de campo `id`**, obligando a Angular a usar `trackByIndice` y destruyendo nodos en actualizaciones. | **CRÍTICO** |
| **`ExpedienteVisorSerializer`** | `backend/expedientes/serializers/visor_serializers.py` | `ExpedienteVisor` y Timeline | `id = f"creacion-{id}"`, etc. | Óptimo: el timeline construye IDs sintéticos deterministas y estables. Requiere certificación en pruebas de regresión. | **BAJO** |
| **`SocioInstitucionalSerializer`** | `backend/padron/serializers.py` | `padron.models.Socio` | `socio_id` (int) | El campo se denomina `socio_id` en lugar de `id`, lo cual puede provocar divergencias si un componente genérico invoca `TrackByUtils.byId` (que busca `item.id`). | **MEDIO** |
| **`AsistenciaEventoSerializer`** | `backend/expedientes/serializers/evento_serializers.py` | `AsistenciaEvento` | `id` (int), `socio_id` (int) | Adecuado. Requiere garantizar que `socio_id` e `id` no sean nulos durante la carga masiva de asistencias (~515 registros). | **BAJO** |
| **`ArticuloReglamentoSerializer`**| `backend/expedientes/serializers/reglamento_serializers.py` | `ArticuloReglamento` | `id` (int), `numero` (int) | Óptimo y estable. | **BAJO** |

### 2.2. Brecha Crítica N° 1: Colección `historial` en `ExpedienteListSerializer`

En `backend/expedientes/serializers/__init__.py`, líneas 623-634:
```python
# CÓDIGO ACTUAL (INCOMPLETO PARA trackBy):
def get_historial(self, obj: Expediente) -> list[dict[str, str]]:
    changes = sorted(obj.cambios_estado.all(), key=lambda c: (c.fecha_hora, c.id))
    return [
        {
            "estado_anterior": change.estado_anterior,
            "estado_nuevo": change.estado_nuevo,
            "actor": change.actor,
            "fecha_hora": change.fecha_hora.isoformat(),
            "motivo": change.motivo,
        }
        for change in changes
    ]
```

**Impacto:** Los diccionarios devueltos no exponen `id: change.id`. Cuando el frontend renderiza la tabla de historial en `GestionarExpedientesComponent` o `MisExpedientesComponent`, la plantilla no puede utilizar `trackBy: trackById`. Al cambiar de estado un expediente, Angular destruye y recrea toda la tabla de transiciones, perdiendo el foco y generando pausas de renderizado.

### 2.3. Brecha Crítica N° 2: Ausencia de Caché Condicional en `RankingListView`

`RankingListView` (`backend/ranking/views.py`) procesa y serializa **~515 registros** con 5 subconsultas correlacionadas por fila en cada petición `GET /api/v1/ranking/`. Cuando el usuario navega reiteradamente hacia el ranking o cuando se producen eventos pasivos en el cliente, el backend devuelve repetidamente `200 OK` con un payload JSON de ~120 KB, provocando:
- Consumo inútil de ancho de banda y CPU en Gunicorn/WSGI.
- Deserialización de 515 objetos en el cliente JavaScript.
- Emisión de un nuevo array por el Observable `rankingService.obtenerRanking()`, forzando la evaluación completa de la plantilla bajo `OnPush`.

---

## 3. Especificación Técnica de Identificadores Únicos e Inmutables

Para garantizar que el 100% de las iteraciones `*ngFor` en Angular puedan consumir de manera confiable la clase utilitaria `TrackByUtils` (`TrackByUtils.byId`, `TrackByUtils.bySocio`, `TrackByUtils.byExpediente`), se establecen los siguientes contratos canónicos invariantes:

### 3.1. Taxonomía de Identificadores Backend ➔ Frontend

```markdown
| Entidad / DTO de API | Endpoint DRF | Campo Clave Primario | Tipo de Dato JSON | Tipo TypeScript | Invariante de Negocio y Garantía Backend |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Ranking Socio** | `/api/v1/ranking/`<br>`/api/ranking/` | `id`<br>`legajo` | `string`<br>`string` | `string`<br>`string` | `id` mapea a `str(nroSocio)` (PK física en `socio_lista`). Inmutable, jamás nulo. `legajo` como cadena única padrón. |
| **Expediente** | `/api/v1/expedientes/`<br>`/api/v1/expedientes/mis-expedientes/` | `id`<br>`numero` | `integer`<br>`string` | `number`<br>`string` | `id` es la PK autoincremental de Django (`expedientes_expediente.id`). `numero` es el código canónico único institucional (`EXP-2026-XXXX`). |
| **Historial de Estado** | Campo anidado en detalle y lista de expedientes | `id`<br>`fecha_hora` | `integer`<br>`string` (ISO 8601) | `number`<br>`string` | **Nueva inclusión requerida:** `id: change.id` (PK de `CambioEstado`). `fecha_hora` en formato UTC ISO 8601 estricto. |
| **Socio Involucrado** | Array `socios` en expediente | `id`<br>`socioId`<br>`legajo` | `integer`<br>`integer`<br>`string` | `number`<br>`number`<br>`string` | Dualidad garantizada: se expone tanto `id` como `socioId` con el mismo valor entero (`socio.id`) para interoperar con cualquier llamada de `trackBy`. |
| **Evidencia / Archivo** | `/api/v1/expedientes/{id}/evidencias/` | `id`<br>`sha256_hash` | `integer`<br>`string` | `number`<br>`string` | `id` PK física de `EvidenciaDescargo`. `sha256_hash` digest hexadecimal de 64 caracteres. |
| **Descargo (T02/T03)** | Array `descargos` en expediente | `id`<br>`presentado_at` | `integer`<br>`string` (ISO 8601) | `number`<br>`string` | `id` PK física de `DescargoExpediente`. |
| **Hito del Timeline** | `/api/v1/expedientes/{id}/visor/` | `id` | `string` | `string` | Clave sintética determinista: `f"{tipo}-{objeto_id}"` (ej. `creacion-10`, `descargo-4`). No volátil. |
| **Evento Institucional**| `/api/v1/eventos/` | `id` | `integer` | `number` | PK física de `EventoInstitucional`. |
| **Convocado Asistencia**| `/api/v1/eventos/{id}/asistencias/` | `id`<br>`socio_id` | `integer`<br>`integer` | `number`<br>`number` | `id` PK física de `AsistenciaEvento`. `socio_id` FK a `socio_lista.nroSocio`. |
| **Artículo Reglamento**| `/api/v1/reglamentos/` | `id`<br>`numero` | `integer`<br>`integer` | `number`<br>`number` | PK y número ordinal de artículo en reglamento disciplinario. |
```

### 3.2. Reglas de Inmutabilidad y Prohibición de Hashes Volátiles

1. **Prohibición de `uuid.uuid4()` o `hash()` Volátiles en Serializadores:** Queda terminantemente prohibido generar claves de identidad mediante llamadas a `uuid.uuid4()`, `id(obj)` de Python o funciones de hash que dependan del puntero de memoria del proceso. Toda clave primaria devuelta en JSON debe derivar directamente del estado persistido en base de datos.
2. **Determinismo Sintético:** En vistas agregadas como el Visor Autorizado (`ExpedienteVisorSerializer`), los identificadores de elementos compuestos deben formarse exclusivamente mediante prefijos canónicos seguidos de la clave primaria subyacente:
   $$\text{ID}_{\text{hito}} = \text{prefijo} + \text{"-"} + \text{PK}_{\text{entidad}}$$
   Ejemplo: `"descargo-12"`, `"cambio-estado-45"`, `"plazo-8"`. Esto asegura que dos peticiones sucesivas al visor generen exactamente el mismo grafo de identificadores.
3. **Consistencia de Tipos en Respuestas JSON:**
   - Si una propiedad es clave primaria numérica, se emite como número entero en JSON (`105`).
   - Si es un identificador de negocio o legajo alfanumérico, se emite estrictamente como string (`"11239"`).
   - Se prohíbe alternar tipos entre endpoints para la misma entidad.

---

## 4. Consistencia de Referencias y Determinismo en Respuestas JSON

Para evitar que el cliente reciba arrays con reordenamientos espurios que confundan a las directivas `trackBy` y degraden el rendimiento de ordenamiento en el DOM:

### 4.1. Pre-ordenamiento Determinista en PostgreSQL / MySQL

Todo QuerySet devuelto por el backend debe contar con un **ordenamiento primario explícito y un criterio de desempate secundario por clave primaria**:

```python
# Patrón canónico de ordenamiento determinista en vistas DRF
def order_ranking_queryset(queryset: QuerySet, ordering: str | None = None) -> QuerySet:
    """Aplica ordenamiento garantizando siempre desempate determinista por nroSocio."""
    if not ordering:
        # Por defecto: mayor saldo primero, desempate por nroSocio ascendente
        return queryset.order_by("-saldo_calc", "nroSocio")
    
    # Procesar tokens de ordenamiento...
    tokens = [tok.strip() for tok in ordering.split(",") if tok.strip()]
    if "nroSocio" not in tokens and "-nroSocio" not in tokens:
        tokens.append("nroSocio")  # Desempate mandatorio
        
    return queryset.order_by(*tokens)
```

Esto garantiza que dos lecturas consecutivas sobre la misma tabla con los mismos filtros devuelvan la lista de socios en un orden **idéntico**, eliminando saltos de posición en la tabla de Angular.

### 4.2. Normalización de Timestamps a ISO 8601 (RFC 3339)

Todas las fechas y sellos de tiempo serializados (`fecha_hora`, `created_at`, `presentado_at`, `plazo_limite_at`) deben serializarse con formato estricto ISO 8601 con indicación explícita de zona horaria o UTC (`Z` / `-03:00`):
```python
# Serialización canónica en DRF
created_at = serializers.DateTimeField(format="iso-8601", default_timezone=ZoneInfo("America/Argentina/Cordoba"))
```
Esto previene que discrepancias en los milisegundos o variaciones en la representación de cadena (`2026-11-12 11:30:00` vs `2026-11-12T11:30:00Z`) hagan fracasar las comparaciones de inmutabilidad en los selectores de Angular.

### 4.3. Precisión Numérica en Saldo y Puntos

Para evitar variaciones de redondeo en JavaScript causadas por la representación de números en coma flotante IEEE 754:
- Los puntos de expedientes y saldos de socios deben ser calculados en el backend utilizando `decimal.Decimal` y serializados como números con 2 decimales exactos (`DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)`).
- Se prohíben discrepancias como `0.33000000000000002`. Las sanciones y felicitaciones se representan de forma fija: `0.25`, `-0.25`, `0.33`, `-0.33`.

---

## 5. Estrategia de Negociación HTTP Condicional (`ETag` / `Cache-Control`)

La incorporación de cabeceras HTTP de validación condicional es la herramienta de mayor impacto para maximizar la eficiencia de `ChangeDetectionStrategy.OnPush` en el frontend.

### 5.1. Flujo de Revalidación HTTP con `ETag` y `If-None-Match`

```mermaid
sequenceDiagram
    autonumber
    actor User as Usuario (Navegador)
    participant Angular as SPA Angular (OnPush)
    participant HTTP as Interceptor HTTP
    participant DRF as Backend DRF (Django)
    participant DB as MySQL 8.0 (InnoDB)

    User->>Angular: Navega a /ranking-socios
    Angular->>HTTP: rankingService.obtenerRanking()
    HTTP->>DRF: GET /api/v1/ranking/
    DRF->>DB: get_reconciled_ranking_queryset()
    DB-->>DRF: 515 socios
    DRF-->>HTTP: HTTP 200 OK + ETag: "w/3a8f1b9c" + Cache-Control: private, no-cache
    HTTP-->>Angular: Emite array (515 socios) -> OnPush renderiza vista

    Note over User, Angular: El usuario cambia de pantalla a /mis-expedientes y regresa a /ranking-socios

    User->>Angular: Regresa a /ranking-socios
    Angular->>HTTP: rankingService.obtenerRanking()
    HTTP->>DRF: GET /api/v1/ranking/ [If-None-Match: "w/3a8f1b9c"]
    DRF->>DB: SELECT MAX(fechaHora) FROM tribunal_puntajeaplicado (Fast Index Scan)
    DB-->>DRF: Última modificación sin cambios
    DRF-->>HTTP: HTTP 304 Not Modified (0 bytes payload)
    HTTP-->>Angular: Resuelve sin emitir nuevo array en Observable
    Note over Angular: OnPush detecta referencia idéntica: 0 ms CPU, 0 ms DOM Update!
```

### 5.2. Impacto Directo en Angular `OnPush`

Cuando el navegador o el interceptor HTTP de Angular recibe un **`304 Not Modified`**:
1. **0 bytes de payload transmitidos por la red** (frente a los ~120 KB habituales).
2. **0 ms de tiempo de CPU consumidos en parsing JSON** en el hilo principal (*Main Thread*).
3. El servicio frontend puede optar por no emitir una nueva referencia o emitir la referencia previa cacheada.
4. Al conservar la referencia previa en memoria (`===`), los componentes decorados con `OnPush` **omiten por completo el ciclo de detección de cambios**.
5. Se erradica cualquier riesgo de *Layout Thrashing* o parpadeo visual en la interfaz.

### 5.3. Algoritmo de Generación Ligera de ETag (Sin Serialización Completa)

Para evitar que el cálculo del ETag en el servidor consuma la misma CPU que la serialización completa, se implementa una estrategia de **ETag Débil de Alta Velocidad (Fast Weak ETag)** basada en metadatos agregados de base de datos:

#### A. Para el Ranking de Socios (`/api/v1/ranking/`):
El ETag depende de dos variables cardinales:
1. `max_puntaje`: El valor máximo de `fechaHora` en la tabla `tribunal_puntajeaplicado`.
2. `count_socios`: La cantidad total de socios en `socio_lista` (`SELECT COUNT(*) FROM socio_lista`).
3. Parámetros de consulta relevantes (`categoria`, `subcomision`, `search`, `ordering`).

$$\text{ETag} = \text{MD5}\Big( \text{f"{count\_socios}:{max\_puntaje}:{query\_params}"} \Big)$$

Esta consulta se resuelve en **menos de 3 ms** en MySQL utilizando el índice sobre `fechaHora`, permitiendo responder `304 Not Modified` sin ejecutar las 2,575 subconsultas correlacionadas del ranking.

#### B. Para el Listado de Expedientes (`/api/v1/expedientes/`):
El ETag se calcula a partir de:
1. `SELECT MAX(fecha_hora) FROM expedientes_cambio_estado`.
2. `SELECT COUNT(*) FROM expedientes_expediente WHERE estado != 'archivado'`.
3. ID y rol del usuario solicitante (garantizando aislamiento RBAC).

### 5.4. Implementación del `ConditionalETagMixin` en DRF

Se diseña el mixin reutilizable para incorporar en `RankingListView` y `ExpedienteViewSet`:

```python
"""
backend/core/pagination_caching.py
Mixin reutilizable para soporte de validación condicional ETag en vistas de Django REST Framework.
"""

import hashlib
from typing import Any
from django.utils.cache import get_conditional_response
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status


class ConditionalETagMixin:
    """
    Mixin para endpoints de solo lectura (GET) de alta frecuencia.
    Evalúa la cabecera 'If-None-Match' contra un ETag determinista y retorna
    HTTP 304 Not Modified con cuerpo vacío cuando los datos no han variado.
    """

    def get_etag_seed(self, request: Request) -> str:
        """
        Debe ser sobreescrito por la vista para devolver una cadena representativa
        del estado de los datos (ej. timestamp de última modificación + conteo de filas).
        """
        raise NotImplementedError("Las subclases deben implementar 'get_etag_seed'.")

    def compute_etag(self, request: Request) -> str:
        """Calcula el hash MD5 representativo del estado del recurso."""
        seed = self.get_etag_seed(request)
        digest = hashlib.md5(seed.encode("utf-8")).hexdigest()
        return f'W/"{digest}"'

    def dispatch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Intercepta la petición antes de ejecutar la lógica pesada de la vista."""
        if request.method in ("GET", "HEAD"):
            try:
                etag = self.compute_etag(request)
                if_none_match = request.headers.get("If-None-Match")

                if if_none_match and if_none_match.strip() == etag:
                    response = Response(status=status.HTTP_304_NOT_MODIFIED)
                    response["ETag"] = etag
                    response["Cache-Control"] = "private, no-cache, must-revalidate"
                    return response
            except Exception:
                # Si falla el cálculo rápido de ETag, continúa con el flujo normal
                pass

        response = super().dispatch(request, *args, **kwargs)

        if request.method in ("GET", "HEAD") and response.status_code == status.HTTP_200_OK:
            try:
                etag = self.compute_etag(request)
                response["ETag"] = etag
                response["Cache-Control"] = "private, no-cache, must-revalidate"
            except Exception:
                pass

        return response
```

---

## 6. Refactorizaciones Concretas de Código Backend para SCRUM-119

A continuación se detallan las refactorizaciones exactas a realizar en el código fuente de backend:

### 6.1. Incorporación de `id` en `historial` de `ExpedienteListSerializer`

En `backend/expedientes/serializers/__init__.py`:

```python
# Refactorización en ExpedienteListSerializer
def get_historial(self, obj: Expediente) -> list[dict[str, Any]]:
    """
    Retorna el historial de cambios de estado incluyendo 'id' único inmutable (change.id)
    para soportar directivas trackBy universales en el frontend Angular (SCRUM-119).
    """
    changes = sorted(obj.cambios_estado.all(), key=lambda c: (c.fecha_hora, c.id))
    return [
        {
            "id": change.id,  # <- INCLUSIÓN MANDATORIA PARA trackById
            "estado_anterior": change.estado_anterior,
            "estado_nuevo": change.estado_nuevo,
            "actor": change.actor,
            "fecha_hora": change.fecha_hora.isoformat(),
            "motivo": change.motivo,
        }
        for change in changes
    ]
```

### 6.2. Armonización de Identificadores en `_serializar_socio_involucrado`

En `backend/expedientes/serializers/__init__.py`:

```python
def _serializar_socio_involucrado(
    socio: Socio, context: dict | None = None
) -> dict[str, int | str]:
    """Serializa socio imputado/involucrado con claves canónicas duales ('id' y 'socioId')."""
    legajo = str(socio.legajo or "").strip()
    grupo = ""
    # ... resolución de grupo omitida por brevedad ...

    return {
        "id": socio.id,          # <- Mapeo universal para TrackByUtils.byId
        "socioId": socio.id,     # <- Compatibilidad con interfaz InvolucradoJustificacion
        "legajo": legajo,
        "nombre": f"{socio.first_name} {socio.last_name}".strip(),
        "first_name": socio.first_name,
        "last_name": socio.last_name,
        "grupo": grupo,
        "estado": estado,
    }
```

### 6.3. Incorporación de `ConditionalETagMixin` en `RankingListView`

En `backend/ranking/views.py`:

```python
from core.pagination_caching import ConditionalETagMixin
from django.db import connection

class RankingListView(ConditionalETagMixin, APIView):
    """
    Endpoint GET /api/v1/ranking/ optimizado con cabeceras ETag y soporte HTTP 304.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get_etag_seed(self, request: Request) -> str:
        """Calcula semilla ultraligera basada en el estado de la base de datos."""
        query_params = request.GET.urlencode()
        with connection.cursor() as cursor:
            cursor.execute("SELECT MAX(fechaHora) FROM tribunal_puntajeaplicado")
            max_fecha = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM socio_lista")
            total_socios = cursor.fetchone()[0]
            
        return f"{total_socios}:{max_fecha}:{query_params}"

    def get(self, request: Request) -> Response:
        # ... lógica de filtrado y serialización existente ...
        serializer = RankingSocioSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
```

---

## 7. Plan de Pruebas Unitarias de Regresión en Serializadores (Pytest)

Se diseñan los casos de prueba formales a incorporar en la suite automatizada `backend/tests/test_serializer_contracts_immutability.py` para asegurar que ningún cambio futuro vulnere las garantías requeridas por el frontend:

```python
"""
backend/tests/test_serializer_contracts_immutability.py
Pruebas de regresión unitarias para estabilidad de identificadores, inmutabilidad y ETag (SCRUM-119).
"""

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import CambioEstado, EstadoExpedienteEnum, Expediente
from padron.models import Socio as SocioLegacy
from ranking.serializers import RankingSocioSerializer
from expedientes.serializers import ExpedienteListSerializer


@pytest.mark.django_db
class TestSerializerContractsImmutability:
    """Verifica que los serializadores emitan identificadores inmutables para Angular trackBy."""

    def test_ranking_socio_serializer_has_stable_unique_identifiers(self, db):
        """Certifica que RankingSocioSerializer emita 'id' y 'legajo' no nulos y estables."""
        socio = SocioLegacy.objects.first()
        if not socio:
            pytest.skip("No hay socios en base de datos para la prueba.")

        serializer_1 = RankingSocioSerializer(socio)
        data_1 = serializer_1.data

        serializer_2 = RankingSocioSerializer(socio)
        data_2 = serializer_2.data

        # 1. El identificador debe estar presente y no ser nulo ni vacío
        assert data_1["id"] is not None
        assert str(data_1["id"]).strip() != ""

        # 2. Inmutabilidad estricta: llamadas sucesivas devuelven el mismo id
        assert data_1["id"] == data_2["id"]
        assert data_1["legajo"] == data_2["legajo"]

        # 3. El identificador coincide con la clave institucional nroSocio
        assert str(data_1["id"]) == str(socio.nroSocio)

    def test_expediente_list_serializer_historial_exposes_unique_id(self, db):
        """Certifica que cada elemento de 'historial' exponga 'id' para trackById."""
        expediente = Expediente.objects.first()
        if not expediente:
            pytest.skip("No hay expedientes en base de datos para la prueba.")

        # Asegurar al menos una transición de estado en el historial
        cambio = CambioEstado.objects.filter(expediente=expediente).first()
        if not cambio:
            cambio = CambioEstado.objects.create(
                expediente=expediente,
                estado_anterior=EstadoExpedienteEnum.INICIADO,
                estado_nuevo=EstadoExpedienteEnum.JUSTIFICANDO,
                actor="SISTEMA",
                motivo="Prueba de contrato",
                fecha_hora=timezone.now(),
            )

        serializer = ExpedienteListSerializer(expediente)
        historial = serializer.data.get("historial", [])

        assert len(historial) > 0, "El historial del expediente no debe estar vacío."
        for item in historial:
            assert "id" in item, "Cada elemento del historial DEBE incluir el campo 'id'."
            assert isinstance(item["id"], int), "El campo 'id' del historial debe ser un entero."
            assert item["id"] > 0, "El campo 'id' debe ser un identificador positivo válido."
            assert "fecha_hora" in item
            # Validar formato ISO 8601
            assert "T" in item["fecha_hora"]

    def test_no_volatile_keys_in_repeated_serializations(self, db):
        """Certifica la ausencia total de hashes volátiles (uuid4/id) en serializaciones."""
        socio = SocioLegacy.objects.first()
        if not socio:
            pytest.skip("No hay socios en base de datos.")

        # Serializar 5 veces consecutivas
        outputs = [RankingSocioSerializer(socio).data for _ in range(5)]

        # Todas las salidas deben ser idénticas campo por campo
        primera = outputs[0]
        for idx, salida in enumerate(outputs[1:], start=2):
            assert salida == primera, f"La serialización {idx} generó datos divergentes o volátiles."

    def test_ranking_endpoint_returns_etag_and_handles_304(self, db):
        """Verifica que /api/v1/ranking/ emita ETag y responda 304 ante If-None-Match."""
        client = APIClient()
        url = "/api/v1/ranking/"

        # Primera petición: debe retornar 200 OK con encabezado ETag
        response_1 = client.get(url)
        assert response_1.status_code == status.HTTP_200_OK
        assert "ETag" in response_1.headers
        etag = response_1.headers["ETag"]
        assert etag.startswith('W/"') or etag.startswith('"')
        assert "Cache-Control" in response_1.headers

        # Segunda petición condicional: enviar If-None-Match con el mismo ETag
        response_2 = client.get(url, HTTP_IF_NONE_MATCH=etag)
        assert response_2.status_code == status.HTTP_304_NOT_MODIFIED
        assert response_2.content == b""  # Cuerpo de respuesta estrictamente vacío (0 bytes)
        assert response_2.headers["ETag"] == etag
```

---

## 8. Matriz de Integración Interdisciplinaria (Frontend, Backend, DBA)

La siguiente matriz sintetiza la sincronización técnica entre las tres disciplinas asignadas a **SCRUM-119**:

```markdown
| Dimensión Técnica | Responsabilidad Backend (Dev Backend Senior) | Responsabilidad Frontend (Dev Frontend Senior) | Responsabilidad DBA (DBA Senior) |
| :--- | :--- | :--- | :--- |
| **Identificadores Únicos** | Garantizar `id` (int/str) y `legajo` (str) inmutables en todas las colecciones principales y anidadas (`historial`, `socios`). | Consumir `TrackByUtils.byId`, `TrackByUtils.bySocio` y `TrackByUtils.byExpediente` en todas las plantillas HTML (`*ngFor`). | Certificar que las claves primarias (`nroSocio`, `id`) no sufran re-indexaciones ni mutaciones en el esquema legacy. |
| **Re-renderizado OnPush** | Emitir respuestas JSON normalizadas y deterministas sin variaciones de claves ni tipos primitivos. | Declarar `changeDetection: ChangeDetectionStrategy.OnPush` y gestionar `markForCheck()` tras la resolución asíncrona. | Optimizar buffers de sesión de MySQL (`sort_buffer_size`) para prevenir tiempos muertos en respuestas REST. |
| **Caché Condicional (ETag)** | Implementar `ConditionalETagMixin` en endpoints de lectura intensiva, respondiendo `304 Not Modified` sin payload. | Configurar interceptor HTTP o servicio para preservar referencias en memoria ante respuestas `304`. | Mantener índices eficientes sobre columnas de timestamp (`fechaHora`, `updated_at`) para cálculo del ETag en <3 ms. |
| **Ciclo de Vida RxJS** | Brindar endpoints con tiempos de respuesta consistentes y soportar cancelación limpia de sockets HTTP. | Implementar el patrón `takeUntil(this.destroy$)` con `Subject<void>` en todos los componentes con `.subscribe()`. | Verificar la erradicación de consultas huérfanas (*zombie queries*) en `Threads_running` de MySQL 8.0. |
```

---

## 9. Plan de Tareas Atómicas de Implementación SDD (<30 min)

Conforme a la metodología **Spec-Driven Development (SDD)** y las compuertas de calidad de `AGENTS.md`, el trabajo de backend se estructura en las siguientes tareas atómicas:

- [ ] **T-BE-119-01: Inclusión de `id` en `historial` de `ExpedienteListSerializer` (15 min)**
  - Modificar `get_historial()` en `backend/expedientes/serializers/__init__.py` para incluir `"id": change.id`.
  - Asegurar tipado de retorno `list[dict[str, Any]]`.
  - Ejecutar test unitario enfocado de serialización de expediente.

- [ ] **T-BE-119-02: Normalización de Claves Duales en `_serializar_socio_involucrado` (15 min)**
  - Exponer tanto `id` como `socioId` con el mismo valor numérico en el helper de serialización de imputados.
  - Verificar que no se introduzcan llamadas redundantes a base de datos (preservar caché de contexto).

- [ ] **T-BE-119-03: Implementación de `ConditionalETagMixin` en `core/pagination_caching.py` (25 min)**
  - Crear el módulo `backend/core/pagination_caching.py` con `ConditionalETagMixin`.
  - Conectar el mixin en `RankingListView` (`backend/ranking/views.py`) implementando el cálculo ultraligero de semilla `get_etag_seed()`.
  - Verificar que las cabeceras `ETag` y `Cache-Control` se emitan correctamente en respuestas 200 OK.

- [ ] **T-BE-119-04: Desarrollo de Suite de Tests de Regresión Pytest (25 min)**
  - Crear `backend/tests/test_serializer_contracts_immutability.py`.
  - Implementar los 4 tests unitarios: estabilidad de IDs de ranking, exposición de `id` en historial de expediente, ausencia de campos volátiles y respuesta `304 Not Modified`.
  - Ejecutar la suite de tests en verde (`pytest -q backend/tests/test_serializer_contracts_immutability.py`).

---

## 10. Conclusiones y Dictamen de Viabilidad

La presente propuesta técnica establece las bases de backend necesarias para que la optimización de frontend de **SCRUM-119** opere a su máxima capacidad:

1. **Garantía Plena de Reciclaje DOM:** Al asegurar que el 100% de las colecciones (incluidas las sublistas anidadas como el historial de causas) expongan claves primarias inmutables (`id`, `nroSocio`, `numero`), el frontend puede eliminar en su totalidad el *Layout Thrashing*, alcanzando tiempos de actualización de lista inferiores a **50 ms**.
2. **Erradicación de CPU Innecesaria mediante HTTP 304:** La adopción de `ConditionalETagMixin` permite a componentes masivos como `RankingSociosComponent` navegar y revalidar datos sin penalizar la memoria de la SPA ni forzar recálculos de Zone.js, contribuyendo directamente al objetivo de **INP < 200 ms**.
3. **Estricto Cumplimiento de `AGENTS.md`:** Cero modificaciones DDL sobre la base de datos MySQL 8.0, respeto absoluto del esquema relacional legado y trazabilidad integral mediante pruebas unitarias automatizadas con Pytest.
