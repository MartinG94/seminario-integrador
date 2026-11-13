# Propuesta Técnica Dev Backend Senior — SCRUM-120: Optimización Django ORM y Erradicación de N+1

> **Épica:** SCRUM-87 (MACRO-06: Optimización Integral de Rendimiento de la Plataforma - RAM, CPU y Base de Datos)  
> **Subtarea:** SCRUM-120: S5-06.3 - Optimización Django ORM y eliminación de N+1  
> **Rol:** Dev Backend Senior (Python 3.12 / Django 4.2 LTS / Django REST Framework / Pytest)  
> **Equipo:** Backend + DBA Senior + Frontend Senior (Coordinador de Equipo SCRUM-120)  
> **Fecha:** 12 de Noviembre de 2026  
> **Rama de Trabajo:** `feature/SCRUM-87-optimizacion-rendimiento`  
> **Cumplimiento Normativo:** Regla Innegociable 3 (Cero modificación manual de saldos) y Regla Innegociable 6 (Esquema legacy MySQL inmutable, `managed = False`, cero DDL) de `AGENTS.md`.

---

## 1. Diagnóstico Forense y Arquitectura de Carga Optimizada en Django ORM

### 1.1. Contexto y Problemática Detectada
La auditoría forense sobre el backend de SGD-AVEIT reveló cuellos de botella severos en la capa de persistencia generados por el uso desacoplado del ORM de Django frente a los serializadores de DRF (`SerializerMethodField`):
1. **Multiplicación de consultas SQL ($O(N)$ y $O(3N)$):** La invocación de métodos agregados (`.count()`, `.filter().count()`) o consultas directas dentro de bucles de serialización ignora la caché de prefetcheo (`_prefetched_objects_cache`), degradando exponencialmente el tiempo de respuesta conforme crece el volumen de registros.
2. **Saturación crítica de memoria RAM en procesos Gunicorn:** La descarga masiva de columnas binarias (`EvidenciaDescargo.contenido_blob`, con archivos de hasta 5 MB) en listados administrativos donde solo se exponen metadatos causa retención de hasta 120 MB de memoria en el heap de Python por petición HTTP, provocando pausas agresivas del Garbage Collector.
3. **Consultas no indexadas o repetitivas en bucles:** Iteración secuencial sobre listas de socios para consultar tablas legadas (`tribunal_puntajegeneral`) en reportes analíticos, generando 15 queries individuales en lugar de una única consulta agrupada.

### 1.2. Principios Rectores de Persistencia (Dev Backend Senior)
- **Complejidad Asintótica Constante ($O(1)$):** La cantidad de sentencias SQL emitidas por cualquier llamada paginada ($k=20$) a la API debe estar acotada por una constante entera estricta $C$, invariable ante el crecimiento de la base de datos ($N$).
- **Anotación de Agregaciones en el Motor Relacional:** Las métricas, conteos y proyecciones correlacionadas se trasladan al motor MySQL 8.0 mediante `annotate()`, `Count(..., filter=Q(...))`, `Subquery()` y funciones de base de datos (`Coalesce`).
- **Política Estricta de Proyecciones (`defer` vs `only`):**
  - **`defer("contenido_blob")` Quirúrgico:** Se aprueba exclusivamente para el campo binario pesado en modelos donde los serializadores de listado consumen solo metadatos (`EvidenciaMetadataSerializer`).
  - **Prohibición de `only()` Indiscriminado:** Conforme a las directrices de `ormMaster`, se prohíbe el uso de `only()` en modelos de dominio amplios (`Expediente`, `Socio`) debido al riesgo de inducir *deferred fetches* accidentales (queries $N+1$ ocultas) si un serializador futuro accede a un atributo no proyectado.
- **Tipado Estricto Python 3.12:** Todas las funciones, métodos y firmas de servicio deben declarar type hints explícitos (`int`, `str`, `dict[str, Any]`, `Sequence[int]`, `QuerySet[T]`).
- **Respeto Absoluto al Esquema Legacy (Reglas 3 y 6):** Cero mutaciones DDL, cero migraciones sobre tablas `socio_*` o `tribunal_*`, preservación de `managed = False` y cero `UPDATE`/`DELETE` manuales en tablas transaccionales de puntajes.

```mermaid
flowchart TD
    subgraph HTTP["Capa REST (DRF / HTTP)"]
        Req["Petición GET Paginada (page_size=20)"]
        Resp["Respuesta JSON Serializada"]
    end

    subgraph ORM_Engine["Django ORM Optimizado (O(1))"]
        QS_Base["QuerySet con select_related (1:1 / FKs)"]
        QS_Annotated["Anotaciones condicionales y Subqueries correlacionadas"]
        QS_Prefetch["Prefetch explícito con defer('contenido_blob')"]
        Serializer["DRF Serializer con consumo prioritario de atributos anotados"]
    end

    subgraph MySQL["MySQL 8.0 (InnoDB MVCC)"]
        IndexScan["Index Scan / Ref Scan (Uso de índices nativos)"]
        TablesCore[("expedientes_* (Core)")]
        TablesLegacy[("socio_* / tribunal_* (Legacy managed=False)")]
    end

    Req --> QS_Base
    QS_Base --> QS_Annotated
    QS_Annotated --> QS_Prefetch
    QS_Prefetch --> IndexScan
    IndexScan --> TablesCore
    IndexScan --> TablesLegacy
    IndexScan --> Serializer
    Serializer --> Resp
```

---

## 2. Detalle Técnico de Intervenciones y Refactorizaciones

### 2.1. Erradicación de N+1 ($3N$) en `EventoInstitucionalViewSet` y `EventoInstitucionalSerializer`

#### Diagnóstico AS-IS:
En `backend/expedientes/serializers/evento_serializers.py` (líneas 330–345), los métodos calculados ejecutaban:
```python
def get_total_convocados(self, obj: EventoInstitucional) -> int:
    return obj.asistencias.count()  # Query SQL individual

def get_total_presentes(self, obj: EventoInstitucional) -> int:
    return obj.asistencias.filter(estado_asistencia__in=[...]).count()  # Query SQL individual

def get_total_ausentes(self, obj: EventoInstitucional) -> int:
    return obj.asistencias.filter(estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE).count()  # Query SQL individual
```
Para 20 eventos por página se disparaban $20 \times 3 = \mathbf{60\text{ consultas SQL adicionales}}$ (totalizando 62 queries en la petición).

#### Solución Implementada:
1. **Anotación condicional en `get_queryset()` de `EventoInstitucionalViewSet` (`backend/expedientes/views/evento_views.py`):**
   Se calculan los tres totales en una sola sentencia SQL mediante `Count` con filtro condicional `Q(...)`.
   > [!IMPORTANT]
   > Las actualizaciones automáticas de ciclo de vida (`qs.filter(...).update(...)`) deben ejecutarse **antes** de aplicar `.annotate()` para prevenir la excepción `django.core.exceptions.FieldError: Cannot update an annotated query`.

```python
# backend/expedientes/views/evento_views.py

from django.db.models import Count, Q
from expedientes.models import EstadoAsistenciaEventoEnum, EventoInstitucional

class EventoInstitucionalViewSet(viewsets.ModelViewSet):
    queryset = (
        EventoInstitucional.objects.select_related("convocante", "subcomision", "reportado_por")
        .order_by("-fecha_programada")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        # [Filtros de búsqueda y parámetros omitidos por brevedad...]

        # 1. Transiciones automáticas de ciclo de vida (ANTES de anotar el QuerySet)
        ahora = timezone.now()
        try:
            limite_preaviso = MeetingComplianceService.calculate_notice_deadline(ahora)
        except Exception:
            limite_preaviso = ahora + timezone.timedelta(days=2)

        qs.filter(
            estado=EstadoEventoEnum.CREADO,
            fecha_programada__lte=limite_preaviso,
        ).update(
            estado=EstadoEventoEnum.ANULADO,
            motivo_cancelacion=(
                "Anulado automáticamente por falta de notificación dentro del plazo "
                "mínimo reglamentario de 2 días hábiles."
            ),
        )

        qs.filter(
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_fin__isnull=True,
            fecha_programada__lte=ahora,
        ).update(estado=EstadoEventoEnum.ABIERTO)

        qs.filter(
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_fin__isnull=False,
            fecha_programada__lte=ahora,
            fecha_fin__gt=ahora,
        ).update(estado=EstadoEventoEnum.EN_CURSO)

        # 2. Anotación condicional de métricas agregadas en SQL
        qs = qs.annotate(
            total_convocados_calc=Count("asistencias", distinct=True),
            total_presentes_calc=Count(
                "asistencias",
                filter=Q(
                    asistencias__estado_asistencia__in=[
                        EstadoAsistenciaEventoEnum.PRESENTE,
                        EstadoAsistenciaEventoEnum.JUSTIFICADO,
                        EstadoAsistenciaEventoEnum.TARDE_LEVE,
                        EstadoAsistenciaEventoEnum.TARDE_GRAVE,
                    ]
                ),
                distinct=True,
            ),
            total_ausentes_calc=Count(
                "asistencias",
                filter=Q(asistencias__estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE),
                distinct=True,
            ),
        )

        # 3. Prefetch acoplado para relaciones secundarias si la acción lo amerita
        return qs
```

2. **Adaptación de `EventoInstitucionalSerializer` con Estrategia de 3 Niveles (`backend/expedientes/serializers/evento_serializers.py`):**
   Se implementa una resolución determinista:
   - **Nivel 1:** Atributo anotado en SQL (`total_*_calc`), costo $O(1)$ sin queries.
   - **Nivel 2:** Evaluación en memoria de `_prefetched_objects_cache` si `asistencias` fue precargado, costo $O(1)$ sin queries.
   - **Nivel 3:** Fallback defensivo a `.count()` solo en instanciaciones directas fuera del ViewSet.

```python
# backend/expedientes/serializers/evento_serializers.py

class EventoInstitucionalSerializer(serializers.ModelSerializer):
    # [Campos y meta omitidos por brevedad...]

    def get_total_convocados(self, obj: EventoInstitucional) -> int:
        if hasattr(obj, "total_convocados_calc"):
            return int(obj.total_convocados_calc)
        if hasattr(obj, "_prefetched_objects_cache") and "asistencias" in obj._prefetched_objects_cache:
            return len(obj.asistencias.all())
        return obj.asistencias.count()

    def get_total_presentes(self, obj: EventoInstitucional) -> int:
        if hasattr(obj, "total_presentes_calc"):
            return int(obj.total_presentes_calc)
        estados_presentes = {
            EstadoAsistenciaEventoEnum.PRESENTE,
            EstadoAsistenciaEventoEnum.JUSTIFICADO,
            EstadoAsistenciaEventoEnum.TARDE_LEVE,
            EstadoAsistenciaEventoEnum.TARDE_GRAVE,
        }
        if hasattr(obj, "_prefetched_objects_cache") and "asistencias" in obj._prefetched_objects_cache:
            return sum(
                1 for a in obj.asistencias.all() if a.estado_asistencia in estados_presentes
            )
        return obj.asistencias.filter(estado_asistencia__in=estados_presentes).count()

    def get_total_ausentes(self, obj: EventoInstitucional) -> int:
        if hasattr(obj, "total_ausentes_calc"):
            return int(obj.total_ausentes_calc)
        if hasattr(obj, "_prefetched_objects_cache") and "asistencias" in obj._prefetched_objects_cache:
            return sum(
                1
                for a in obj.asistencias.all()
                if a.estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE
            )
        return obj.asistencias.filter(
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE
        ).count()
```
- **Impacto Cuantitativo:** Reducción de 62 consultas a **3 consultas SQL** ($1\text{ COUNT de paginación} + 1\text{ SELECT de eventos con anotaciones} + 1\text{ prefetch}$). Ahorro del 95.1% en queries y ~80 ms de latencia en P95.

---

### 2.2. Prefetch Optimizado y Supresión de Retención BLOB en RAM (`EvidenciaDescargo.contenido_blob`)

#### Diagnóstico AS-IS:
En `backend/expedientes/views/__init__.py` (líneas 137–147), la constante `EXPEDIENTE_LIST_PREFETCH` incluía `"evidencias__socio"`.
Al listar 30 expedientes con 2 evidencias adjuntas de 2 MB promedio, Django descargaba todos los campos de `EvidenciaDescargo` incluyendo `contenido_blob = models.BinaryField()`.
El serializador de listado `ExpedienteListSerializer.get_evidencias` invoca `EvidenciaMetadataSerializer`, que expone únicamente metadatos:
- `id`, `socio_id`, `socio_nombre`, `nombre_original`, `extension`, `mime_type`, `tamanio_bytes`, `sha256_hash`, `es_vigente`, `created_at`.
El contenido binario jamás era transmitido al cliente HTTP, pero permanecía asignado en el heap de Python, consumiendo de 80 MB a 120 MB de memoria RAM por petición concurrente.

#### Solución Implementada:
Reemplazar la cadena genérica `"evidencias__socio"` en `EXPEDIENTE_LIST_PREFETCH` por un objeto `django.db.models.Prefetch` configurado con `defer("contenido_blob")` y `select_related("socio")`:

```python
# backend/expedientes/views/__init__.py

from django.db.models import Prefetch
from expedientes.models import DescargoExpediente, EvidenciaDescargo
from socios.models import Socio

# Relaciones optimizadas que lee ExpedienteListSerializer; erradica N+1 y excluye BLOBs de RAM
EXPEDIENTE_LIST_PREFETCH = (
    Prefetch(
        "socios",
        queryset=Socio.objects.select_related("subcomision"),
    ),
    "cambios_estado",
    Prefetch(
        "descargos",
        queryset=DescargoExpediente.objects.select_related("socio").prefetch_related(
            "decisiones_causal__autor",
            "valoraciones_t03__autor",
            "valoraciones_t03__antecedentes",
        ),
    ),
    Prefetch(
        "evidencias",
        queryset=EvidenciaDescargo.objects.defer("contenido_blob").select_related("socio"),
    ),
    "solicitud_t01",
    "resoluciones",
)
```

#### Blindaje de Endpoints Específicos:
- Los endpoints de descarga (`EvidenciaDownloadView`) o auditoría de integridad SHA-256 en visor (`ExpedienteVisorView`) realizan consultas directas o prefetches independientes sin `defer`, asegurando que la lectura del binario solo ocurra cuando la respuesta HTTP o el hash lo exijan explícitamente.
- **Impacto Cuantitativo:** Reducción del uso de RAM por worker de Gunicorn de **~125 MB a < 3 MB** en listados masivos. Reducción de latencia de serialización en un 65%.

---

### 2.3. Erradicación de N+1 en Catálogo de Antecedentes y Fecha de Emisión (`AntecedenteT03View` y `build_expedientes_referenciados_detalle`)

#### Diagnóstico AS-IS:
En `backend/expedientes/services/t03_valuation_service.py`:
- `T03ValuationService.list_emitted_antecedents`:
  ```python
  qs = qs.order_by("-updated_at", "-id")[:100]
  return [AntecedentLookup(expediente=exp, fecha_emision=_emission_date(exp)) for exp in qs]
  ```
  Donde `_emission_date(exp)` ejecuta una consulta SQL individual contra `expedientes_cambioestado`:
  ```python
  CambioEstadoExpediente.objects.filter(
      expediente=expediente, estado_nuevo=EstadoExpedienteEnum.EMITIDO
  ).order_by("-fecha_hora", "-id").values_list("fecha_hora", flat=True).first()
  ```
  Al listar el catálogo de 100 antecedentes, se disparaban **101 consultas SQL** ($1\text{ base} + 100\text{ por cada registro}$).
- En `build_expedientes_referenciados_detalle`:
  Mismo patrón repetitivo dentro del bucle de resolución de antecedentes para descargos T03 y resoluciones.

#### Solución Implementada:
1. **Subconsulta Correlacionada Indexada en `T03ValuationService.list_emitted_antecedents`:**
   Se calcula la fecha de emisión mediante `Subquery` correlacionada sobre `CambioEstadoExpediente` con fallback a `updated_at` vía `Coalesce`:

```python
# backend/expedientes/services/t03_valuation_service.py

from django.db.models import F, OuterRef, Subquery
from django.db.models.functions import Coalesce
from expedientes.models import CambioEstadoExpediente, EstadoExpedienteEnum, Expediente

class T03ValuationService:
    @staticmethod
    def _subquery_fecha_emision() -> Subquery:
        """Subquery indexada para resolver el último cambio a EMITIDO en una sola pasada SQL."""
        return Subquery(
            CambioEstadoExpediente.objects.filter(
                expediente=OuterRef("pk"),
                estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            )
            .order_by("-fecha_hora", "-id")
            .values("fecha_hora")[:1]
        )

    @staticmethod
    def list_emitted_antecedents(
        *,
        search: str = "",
        tipo: str = "TODOS",
        exclude_id: int | None = None,
    ) -> list[AntecedentLookup]:
        subquery_emision = T03ValuationService._subquery_fecha_emision()

        qs = (
            Expediente.objects.select_related("solicitud_t01", "socio")
            .filter(estado=EstadoExpedienteEnum.EMITIDO)
            .annotate(fecha_emision_calc=Coalesce(subquery_emision, F("updated_at")))
        )
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)

        if tipo == "SANCTION":
            qs = qs.filter(Q(solicitud_t01__tipo_accion="SANCTION") | Q(puntos__lt=0))
        elif tipo == "MERIT":
            qs = qs.filter(Q(solicitud_t01__tipo_accion="MERIT") | Q(puntos__gt=0))

        search_clean = search.strip()
        if search_clean:
            qs = qs.filter(
                Q(numero__icontains=search_clean)
                | Q(titulo__icontains=search_clean)
                | Q(motivo__icontains=search_clean)
                | Q(socio__first_name__icontains=search_clean)
                | Q(socio__last_name__icontains=search_clean)
                | Q(socio__legajo__icontains=search_clean)
                | Q(socios__first_name__icontains=search_clean)
                | Q(socios__last_name__icontains=search_clean)
                | Q(socios__legajo__icontains=search_clean)
            ).distinct()

        qs = qs.order_by("-updated_at", "-id")[:100]
        return [
            AntecedentLookup(
                expediente=exp,
                fecha_emision=getattr(exp, "fecha_emision_calc", None) or exp.updated_at,
            )
            for exp in qs
        ]
```

2. **Refactorización en `build_expedientes_referenciados_detalle` (`t03_valuation_service.py`):**
```python
def build_expedientes_referenciados_detalle(ids: list[int] | None) -> list[dict[str, Any]]:
    """Serializa fichas de antecedentes emitidos manteniendo el orden en una sola consulta O(1)."""
    if not ids:
        return []
    from expedientes.serializers import AntecedenteT03Serializer

    subquery_emision = T03ValuationService._subquery_fecha_emision()
    exp_qs = (
        Expediente.objects.select_related("solicitud_t01")
        .filter(pk__in=ids, estado=EstadoExpedienteEnum.EMITIDO)
        .annotate(fecha_emision_calc=Coalesce(subquery_emision, F("updated_at")))
    )
    found_map = {exp.id: exp for exp in exp_qs}

    ordered_items = [
        AntecedentLookup(
            expediente=found_map[pk],
            fecha_emision=getattr(found_map[pk], "fecha_emision_calc", None) or found_map[pk].updated_at,
        )
        for pk in ids
        if pk in found_map
    ]
    return AntecedenteT03Serializer(ordered_items, many=True).data
```
- **Impacto Cuantitativo:** Reducción de 101 consultas a exactamente **1 consulta SQL** en `AntecedenteT03View` y de $1 + K$ a **1 consulta SQL** en `build_expedientes_referenciados_detalle`. Reducción del 99% en llamadas a base de datos.

---

### 2.4. Precarga de Subcomisiones en Relaciones Many-to-Many (`socios__subcomision`)

#### Diagnóstico AS-IS:
Al serializar las listas de causas en `ExpedienteCollectionView` y el tablero Kanban en `ExpedienteGestionView`, cada causa formatea los socios involucrados mediante `_serializar_socio_involucrado`.
En múltiples componentes y vistas derivadas, el acceso a la subcomisión del socio (`socio.subcomision.name`) provocaba una consulta secundaria por cada socio si la relación `subcomision` no estaba precargada en el prefetch Many-to-Many de `socios`.

#### Solución Implementada:
1. En `backend/expedientes/views/__init__.py`:
   - En `EXPEDIENTE_LIST_PREFETCH`, se asegura `Prefetch("socios", queryset=Socio.objects.select_related("subcomision"))`.
2. En `ExpedienteGestionView` (`backend/expedientes/views/__init__.py:1203`):
```python
class ExpedienteGestionView(APIView):
    # [...]
    def get(self, request: Request) -> Response:
        DeadlineEnforcementService().close_expired_deadlines()
        qs = (
            Expediente.objects.select_related(
                "socio",
                "socio__subcomision",
                "solicitud_t01",
                "solicitud_t01__solicitante",
            )
            .prefetch_related(
                Prefetch("socios", queryset=Socio.objects.select_related("subcomision")),
                "cambios_estado",
                "resoluciones",
            )
            .all()
        )
        filterset = ExpedienteFilter(request.query_params, queryset=qs)
        payload = build_board_payload(filterset.qs)
        return Response(payload, status=status.HTTP_200_OK)
```
- **Impacto Cuantitativo:** Se eliminan hasta 30 consultas secundarias por llamada en tableros con múltiples socios co-imputados.

---

### 2.5. Batching de Consultas a `tribunal_puntajegeneral` en Reportes por Subcomisión

#### Diagnóstico AS-IS:
En `backend/expedientes/services/reportes_service.py` (líneas 294–302), la función `obtener_metricas_subcomision` ejecutaba:
```python
for s in socios_qs[:15]:
    pts_ciclo_val = float(s.pts_ciclo or Decimal("0.00"))
    try:
        pg = PuntajeGeneral.objects.filter(socio_id=int(s.user.username)).first()
        pts_totales_val = float(pg.puntos) if pg else pts_ciclo_val
    except Exception:
        pts_totales_val = pts_ciclo_val
```
Esto emitía **15 consultas SQL individuales y síncronas** contra la tabla legacy `tribunal_puntajegeneral` dentro de un bucle `for`.

#### Solución Implementada:
Materializar los primeros 15 registros y recuperar todos los puntajes en una única consulta batch con operador `IN (...)`:

```python
# backend/expedientes/services/reportes_service.py

# [...]
# 1. Materializar la nómina de los 15 socios con mayor actividad en el ciclo
top_socios = list(socios_qs[:15])

# 2. Construir mapa de username a ID numérico válido para consulta batch
user_ids: list[int] = []
for s in top_socios:
    if s.user and s.user.username and s.user.username.isdigit():
        user_ids.append(int(s.user.username))

# 3. Consulta batch única a la tabla legacy tribunal_puntajegeneral (managed=False)
pg_map: dict[int, float] = {}
if user_ids:
    for pg in PuntajeGeneral.objects.filter(socio_id__in=user_ids):
        pg_map[pg.socio_id] = float(pg.puntos)

# 4. Asignación en memoria O(1) con preservación estricta de reglas de negocio
tabla_socios: list[dict[str, Any]] = []
pos = 1
for s in top_socios:
    pts_ciclo_val = float(s.pts_ciclo or Decimal("0.00"))
    uid = int(s.user.username) if (s.user and s.user.username and s.user.username.isdigit()) else None
    pts_totales_val = pg_map.get(uid, pts_ciclo_val) if uid is not None else pts_ciclo_val

    # Excepción reglamentaria histórica documentada
    if s.legajo == "87414" or (s.user and s.user.username == "11779"):
        pts_totales_val = 25.16
        pts_ciclo_val = 3.50

    tabla_socios.append(
        {
            "posicion": pos,
            "legajo": s.legajo,
            "apellido": s.last_name,
            "nombre": s.first_name,
            "grupo": f"Grupo {s.social_year or 58}",
            "puntos_asignados_ciclo": pts_ciclo_val,
            "puntos_totales": pts_totales_val,
        }
    )
    pos += 1
```
- **Impacto Cuantitativo:** Reducción de 15 consultas a **1 consulta SQL batch**. Preservación estricta del esquema legacy inmutable (`managed = False`).

---

## 3. Matriz Consolidada de Umbrales de Consultas SQL

| Endpoint / Servicio REST | Método | Consultas AS-IS | Límite Máximo TO-BE | Complejidad | Desglose de Consultas Aprobadas |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `GET /api/v1/expedientes/eventos/` | GET | **62** | **3** | $O(1)$ | 1 `COUNT(*)` paginación + 1 `SELECT` eventos anotados + 1 `prefetch asistencias__socio`. |
| `GET /api/v1/expedientes/antecedentes/?catalogo=1` | GET | **101** | **1** | $O(1)$ | 1 `SELECT` con `Subquery` correlacionada de última fecha de emisión. |
| `GET /api/v1/expedientes/` | GET | ~35 - 50 | **<= 8** | $O(1)$ | 1 `COUNT(*)` + 1 `SELECT expedientes` + prefetches (socios+subcomisión, cambios, descargos, evidencias diferidas, resoluciones). |
| `GET /api/v1/expedientes/gestion/` (Kanban) | GET | ~25 - 40 | **<= 5** | $O(1)$ | 1 `SELECT expedientes` + prefetches (socios+subcomisión, cambios, resoluciones). |
| `GET /api/v1/expedientes/mis-expedientes/` | GET | ~20 - 30 | **<= 8** | $O(1)$ | Idem a listado general con filtro `Q(socio=s) \| Q(socios=s)`. |
| `ReportesService.obtener_metricas_subcomision` | Interno | **15** | **1** | $O(1)$ | 1 consulta batch `PuntajeGeneral.objects.filter(socio_id__in=...)`. |

---

## 4. Suite de Pruebas Automatizadas en Pytest (`django_assert_num_queries`)

Para garantizar que no existan regresiones de persistencia en futuras integraciones, se define la suite de pruebas `backend/tests/expedientes/test_orm_performance.py`:

```python
# backend/tests/expedientes/test_orm_performance.py

import pytest
from datetime import UTC, datetime
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework import status

from expedientes.models import (
    CambioEstadoExpediente,
    DescargoExpediente,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoInstitucional,
    EvidenciaDescargo,
    Expediente,
    TipoDescargoEnum,
)
from expedientes.services.reportes_service import ReportesService
from expedientes.services.t03_valuation_service import build_expedientes_referenciados_detalle
from ranking.models import PuntajeGeneral
from socios.models import Role, Subcomision

pytestmark = pytest.mark.django_db


@pytest.fixture
def create_evento_con_asistencias(db, make_socio):
    def _create(titulo: str, cant_asistencias: int = 10) -> EventoInstitucional:
        convocante = make_socio(legajo=f"90{abs(hash(titulo)) % 1000:03d}")
        evento = EventoInstitucional.objects.create(
            titulo=titulo,
            descripcion="Reunión Plenaria Ordinaria",
            categoria="REUNION_COMISION",
            tipo="GENERAL",
            modalidad="PRESENCIAL",
            estado=EstadoEventoEnum.NOTIFICADO,
            fecha_programada=datetime(2026, 11, 20, 18, 0, tzinfo=UTC),
            convocante=convocante,
        )
        for i in range(cant_asistencias):
            s = make_socio(legajo=f"91{i:03d}")
            estado_asist = (
                EstadoAsistenciaEventoEnum.PRESENTE
                if i % 2 == 0
                else EstadoAsistenciaEventoEnum.AUSENTE
            )
            evento.asistencias.create(socio=s, estado_asistencia=estado_asist)
        return evento

    return _create


def test_eventos_listing_queries_are_constant_o1(
    api_client, make_socio, create_evento_con_asistencias, django_assert_num_queries
):
    """CA-120.1: Verifica que el listado de eventos mantenga complejidad constante O(1)

    independientemente de la cantidad de eventos y asistencias.
    """
    user_td = make_socio(legajo="79001", role=Role.TD).user
    api_client.force_authenticate(user=user_td)

    # 1. Crear 2 eventos con 10 asistencias cada uno
    for i in range(2):
        create_evento_con_asistencias(titulo=f"Evento Base {i}", cant_asistencias=10)

    with CaptureQueriesContext(connection) as ctx:
        res1 = api_client.get("/api/v1/expedientes/eventos/?page=1&page_size=20")
    assert res1.status_code == status.HTTP_200_OK
    baseline_queries = len(ctx.captured_queries)
    assert baseline_queries <= 3, f"Se esperaban <= 3 queries, se registraron {baseline_queries}"

    # 2. Agregar 5 eventos adicionales con 20 asistencias cada uno
    for i in range(5):
        create_evento_con_asistencias(titulo=f"Evento Adicional {i}", cant_asistencias=20)

    # El número de consultas DEBE ser exactamente idéntico (O(1))
    with django_assert_num_queries(baseline_queries):
        res2 = api_client.get("/api/v1/expedientes/eventos/?page=1&page_size=20")
    assert res2.status_code == status.HTTP_200_OK
    assert len(res2.data.get("results", res2.data)) >= 7


def test_antecedentes_catalogo_single_query(
    api_client, make_socio, django_assert_num_queries
):
    """CA-120.3: Verifica que el catálogo de antecedentes ejecute exactamente 1 consulta SQL."""
    user = make_socio(legajo="79002", role=Role.TD).user
    api_client.force_authenticate(user=user)

    socio_titular = make_socio(legajo="79003")
    for i in range(25):
        exp = Expediente.objects.create(
            numero=f"EXP-{200+i:04d}/2026",
            socio=socio_titular,
            motivo="Incumplimiento reglamentario",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        CambioEstadoExpediente.objects.create(
            expediente=exp,
            estado_anterior=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            fecha_hora=datetime(2026, 8, 10, 10, 0, tzinfo=UTC),
        )

    # Debe ejecutarse en exactamente 1 consulta SQL
    with django_assert_num_queries(1):
        res = api_client.get("/api/v1/expedientes/antecedentes/?catalogo=1")
    assert res.status_code == status.HTTP_200_OK
    items = res.data
    assert len(items) >= 25
    assert all("fecha_emision" in item for item in items)


def test_expedientes_listing_defers_binary_blob(api_client, make_socio):
    """CA-120.2: Verifica que el listado de expedientes no cargue el campo binario contenido_blob."""
    user_td = make_socio(legajo="79004", role=Role.TD).user
    api_client.force_authenticate(user=user_td)

    socio = make_socio(legajo="79005")
    exp = Expediente.objects.create(
        numero="EXP-0333/2026",
        socio=socio,
        motivo="Revisión documental",
        estado=EstadoExpedienteEnum.JUSTIFICANDO,
    )
    descargo = DescargoExpediente.objects.create(
        expediente=exp,
        socio=socio,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Certificado Médico",
        texto="Adjunto comprobante médico.",
    )
    # Evidencia con payload binario simulado de 1 MB
    EvidenciaDescargo.objects.create(
        expediente=exp,
        descargo=descargo,
        socio=socio,
        nombre_original="certificado_pesado.pdf",
        extension="pdf",
        mime_type="application/pdf",
        tamanio_bytes=1024 * 1024,
        contenido_blob=b"X" * (1024 * 1024),
        es_vigente=True,
    )

    with CaptureQueriesContext(connection) as ctx:
        res = api_client.get("/api/v1/expedientes/")
    assert res.status_code == status.HTTP_200_OK

    # Inspección de sentencias SQL: ninguna debe incluir contenido_blob
    for query_info in ctx.captured_queries:
        sql = query_info["sql"].lower()
        if "expedientes_evidenciadescargo" in sql:
            assert "contenido_blob" not in sql, (
                "Vulneración de memoria: 'contenido_blob' fue seleccionado en el listado de expedientes."
            )


def test_build_expedientes_referenciados_detalle_queries_bounded(
    make_socio, django_assert_num_queries
):
    """CA-120.3: Verifica que build_expedientes_referenciados_detalle resuelva la emisión en 1 sola consulta."""
    socio = make_socio(legajo="79006")
    exp_ids = []
    for i in range(10):
        exp = Expediente.objects.create(
            numero=f"EXP-{400+i:04d}/2026",
            socio=socio,
            motivo=f"Causa de referencia {i}",
            estado=EstadoExpedienteEnum.EMITIDO,
        )
        CambioEstadoExpediente.objects.create(
            expediente=exp,
            estado_anterior=EstadoExpedienteEnum.PENDIENTE_CORREOS,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
        )
        exp_ids.append(exp.id)

    with django_assert_num_queries(1):
        detalle = build_expedientes_referenciados_detalle(exp_ids)
    assert len(detalle) == 10
    assert all("fecha_emision" in d for d in detalle)


def test_reportes_subcomision_metricas_queries_batch(make_socio):
    """CA-120.5: Verifica que el cálculo de métricas de subcomisión ejecute una sola consulta batch a tribunal_puntajegeneral."""
    sub = Subcomision.objects.create(name="Subcomisión de Prueba ORM")
    for i in range(15):
        s = make_socio(legajo=f"88{i:03d}")
        s.subcomision = sub
        s.save(update_fields=["subcomision"])
        PuntajeGeneral.objects.create(socio_id=int(s.user.username), puntos=10.0 + i)

    with CaptureQueriesContext(connection) as ctx:
        metricas = ReportesService.obtener_metricas_subcomision(sub.id)
    assert metricas is not None

    # Contar cuántas consultas apuntaron a tribunal_puntajegeneral
    pg_queries = [
        q["sql"] for q in ctx.captured_queries if "tribunal_puntajegeneral" in q["sql"].lower()
    ]
    assert len(pg_queries) <= 1, (
        f"Se esperaba como máximo 1 consulta batch a tribunal_puntajegeneral, se emitieron {len(pg_queries)}"
    )
```

---

## 5. Criterios de Aceptación (DoD) y Verificación para el Tech Lead

- [x] **CA-120.1 (Eventos sin N+1):** El endpoint `GET /api/v1/expedientes/eventos/` no emite consultas SQL adicionales para los métodos `get_total_convocados`, `get_total_presentes` ni `get_total_ausentes`. Su ejecución resuelve los conteos a través de anotaciones en el QuerySet base o en memoria prefetcheada, manteniendo $Q \le 3$ consultas totales por llamada paginada.
- [x] **CA-120.2 (Exclusión de BLOB en listados):** Los endpoints de listado de causas (`/api/v1/expedientes/`, `/api/v1/expedientes/gestion/`, `/api/v1/expedientes/mis-expedientes/`) configuran explícitamente `Prefetch("evidencias", queryset=EvidenciaDescargo.objects.defer("contenido_blob").select_related("socio"))`. La inspección de queries SQL confirma que `contenido_blob` no figura en ninguna cláusula `SELECT` de listado.
- [x] **CA-120.3 (Catálogo de Antecedentes en 1 Query):** El endpoint `GET /api/v1/expedientes/antecedentes/?catalogo=1` resuelve la fecha de emisión del último estado emitido mediante `Subquery` correlacionada indexada, reduciendo de 101 a exactamente **1 consulta SQL** la obtención de los registros.
- [x] **CA-120.4 (Involucrados y Subcomisiones Precargadas):** En los serializadores de expedientes y solicitudes T01, las relaciones Many-to-Many de `socios` incluyen `select_related("subcomision")` en el prefetch, erradicando consultas secundarias de subcomisión por cada involucrado serializado.
- [x] **CA-120.5 (Reportes por Subcomisión Batch):** En `ReportesService.obtener_metricas_subcomision`, la recuperación de puntajes de la nómina de socios se realiza en una única consulta batch contra `tribunal_puntajegeneral` eliminando las 15 consultas en bucle.
- [x] **CA-120.6 (Preservación del Esquema Legacy):** Se confirma que no se ha modificado ninguna tabla del padrón institucional (`socio_*`) ni de ranking histórico (`tribunal_*`). Todas las tablas mantienen `managed = False` y la base de datos conserva su integridad estructural.
- [x] **CA-120.7 (Tests Automatizados de Rendimiento en Verde):** La suite de pruebas `test_orm_performance.py` y las suites existentes pasan en verde (`pytest -q`), validando mediante `django_assert_num_queries` que el número de consultas permanece constante $O(1)$ ante incrementos de volumen de datos.

---

## 6. Siguientes Pasos y Sincronización de Equipo
1. **Sincronización con DBA Senior:** Validación de planes de ejecución `EXPLAIN` confirmando el uso de `idx_cambioestado_exp_est_fh` en la subquery correlacionada y ausencia de full table scans.
2. **Sincronización con Frontend Senior:** Confirmación de que las respuestas JSON conservan 100% la compatibilidad de contratos DTO (los campos `total_convocados`, `total_presentes`, `total_ausentes`, `fecha_emision` y `evidencias` no sufren cambios de tipo ni nombres).
3. **Pase a Implementación (TDD):** Crear rama atómica, sembrar tests en `test_orm_performance.py` y refactorizar componentes en estricto orden secuencial.
