# ADR-001: Estrategia de Consumo del Padrón Institucional y Capa Anticorrupción de Sólo Lectura

- **Identificador:** ADR-001
- **Fecha:** 2026-09-19
- **Estado:** Aceptado
- **Trazabilidad:** Historia de Usuario Jira [`SCRUM-37`](https://guillenmartin94.atlassian.net/browse/SCRUM-37) (Código: `S1-04`)
- **Normativa de Referencia:** Estatuto AVEIT 2026 (Arts. 3 y 6), Reglamento Procesal 2026 (Art. 12), Constitución del Proyecto (Principios 1, 2 y 8). *(Nota de desvinculación: La US SCRUM-37 no depende de los baremos tarifados de la Circular 001/2026, la cual rige exclusivamente para solicitudes T01 y alertas de puntos).*

---

## 1. Contexto y Planteo del Problema

La Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (**A.V.E.I.T.** - UTN FRC) cuenta con un sistema institucional preexistente y una base de datos central en MySQL (`svaveit`) que administra el padrón histórico de ~515 socios y sus respectivas subcomisiones de pertenencia (tablas `socio_lista`, `socio_tiposubcomision`, `socio_estudio`, `socio_email`, `socio_estadoHistorial`, entre otras).

El nuevo Sistema de Gestión Disciplinaria (**SGD-AVEIT**) debe operar sobre la masa societaria para:
1. Autenticar a socios y autoridades institucionales.
2. Identificar la pertenencia a subcomisiones y el año social en curso.
3. Consultar legajos disciplinarios y antecedentes al abrir solicitudes de sanción/mérito (Formulario T01).
4. Computar quórums y representatividades colegiadas en el Tribunal de Disciplina.

### La Problemática
El Tribunal de Disciplina **no es la autoridad rectora del padrón societario**: no emite altas de socios, no procesa renuncias ni modificaciones de carrera universitaria. Si el SGD-AVEIT implementara una tabla propia de socios editable, se originaría de forma inevitable una **divergencia de datos maestros** (un socio dado de baja o suspendido en la institución continuaría figurando habilitado en el Tribunal, o transferencias de subcomisión no impactarían en tiempo real).

Adicionalmente, el esquema preexistente presenta deuda técnica acumulada:
- Nombres de tablas y columnas con mezcla de convenciones (`socio_lista`, `anoSocial`, `codSubcomision`, `compositeKey`).
- Dispersión de atributos en tablas satélites sin claves foráneas declaradas formalmente en el DDL o mediante artificios de clave compuesta (`socio_email`, `socio_estadoHistorial`).
- Necesidad de normalización terminológica de interfaz: la plataforma SGD-AVEIT adopta las denominaciones canónicas *"Pasivo"* y *"Activo"* (Decisión de Product Owner del 08/09/2026 y Principio 8 de la Constitución) para los socios ordinarios denominados *"Junior"* y *"Senior"* en los Arts. 3 y 6 del Estatuto 2026.
- Ausencia de tipado estricto en el motor de base de datos legado.

---

## 2. Fuerzas Impulsoras y Restricciones (Decision Drivers)

- **DD-1 (Fuente Única de Verdad):** Garantizar que exista una sola fuente canónica para los datos de socios y subcomisiones, eliminando cualquier posibilidad de divergencia o duplicación no controlada.
- **DD-2 (Principio de Menor Privilegio y Seguridad):** El sistema SGD-AVEIT debe tener permisos estrictos de **sólo lectura (`SELECT`)** sobre las tablas institucionales del padrón, garantizando que ninguna operación del Tribunal pueda alterar los registros maestros.
- **DD-3 (Alineación Normativa 2026):** Dar estricto cumplimiento a la Decisión de Product Owner del 08/09/2026 y el Principio 8 de la Constitución sobre las categorías de los Arts. 3 y 6 del Estatuto 2026:
  - Categoría **Pasivo**: Mapea a los socios ordinarios de 1.º a 3.º año social (denominados *"Junior"* en el Estatuto 2026).
  - Categoría **Activo**: Mapea a los socios ordinarios de 4.º a 6.º año social (denominados *"Senior"* en el Estatuto 2026).
  - **Separación de Vigencia:** La categoría social jamás debe confundirse con la vigencia de la membresía o cuenta (`habilitado`/`inactivo`), la cual debe modelarse de forma independiente.
- **DD-4 (Estabilidad de Identidad):** El legajo universitario y el número de socio deben resolverse como una identidad unívoca, inmutable y auditable en todo el ciclo procesal.
- **DD-5 (Aislamiento de Entornos y Resiliencia):** El sistema debe poder ejecutarse y probarse localmente en Docker y pipelines de CI/CD sin depender de conectividad a la red física de AVEIT, y debe ser observable ante cortes o degradaciones de enlace.

---

## 3. Alternativas Evaluadas y Justificación de Descarte

### Opción A: Modelo Local Independiente con CRUD en SGD-AVEIT
- **Descripción:** Crear modelos Django de `Socio` y `Subcomision` locales con interfaces de administración para altas, bajas y modificaciones.
- **Veredicto:** **DESCARTADA**.
- **Justificación:** Viola DD-1 y la Constitución del proyecto. Crea un sistema paralelo que divergiría en días, trasladando al Tribunal tareas administrativas que estatutariamente corresponden a la Comisión Directiva y a la Secretaría de la Asociación.

### Opción B: Réplica Periódica Asíncrona (ETL / Cron Job Batch)
- **Descripción:** Ejecutar una tarea programada (cron diario/nocturno) que copie los registros de `socio_lista` hacia tablas réplica locales en la base de datos de SGD-AVEIT.
- **Veredicto:** **DESCARTADA**.
- **Justificación:** Para un volumen acotado (~515 registros), introduce latencia innecesaria en la actualización de estados de socios y agrega complejidad operativa injustificada (monitoreo de jobs fallidos, inconsistencias temporales durante el día).

### Opción C: Capa Anticorrupción (ACL) con Adaptador de Sólo Lectura
- **Descripción:** Consultar en tiempo real la base institucional mediante una conexión delegada de sólo lectura, interponiendo un **Adaptador de Dominio (Anticorruption Layer)** que traduce las entidades legadas al modelo canónico 2026 de SGD-AVEIT.
- **Veredicto:** **ELEGIDA (ACEPTADA)**.
- **Justificación:** Satisface la totalidad de los drivers. Mantiene la fuente única de verdad, asegura privilegios de sólo lectura, aísla la deuda técnica del legado y permite desacoplar los entornos mediante inyección de dependencias (adaptador MySQL para producción y adaptador Mock en memoria para tests y CI).

---

## 4. Decisión Adoptada: Arquitectura y Patrones de Diseño

Se decide implementar una **Capa Anticorrupción (ACL)** basada en el patrón de **Arquitectura Hexagonal (Puertos y Adaptadores)** dentro de la aplicación Django `backend/padron/`:

```
+───────────────────────────────────────────────────────────────────────────+
|                  SGD-AVEIT — CAPA DE DOMINIO Y APLICACIÓN                 |
|  - Servicios: Apertura T01, Quórum TD, Ranking Oficial, Búsqueda Legajos  |
+─────────────────────────────────────┬─────────────────────────────────────+
                                      │ consume
+─────────────────────────────────────v─────────────────────────────────────+
|               PUERTO DE DOMINIO: `PadronRepositoryInterface`              |
|  - get_by_id(socio_id: int) -> Optional[SocioInstitucionalDTO]            |
|  - get_by_legajo(legajo: str) -> Optional[SocioInstitucionalDTO]          |
|  - list_socios(filtros: Dict) -> List[SocioInstitucionalDTO]              |
|  - list_subcomisiones() -> List[SubcomisionDTO]                           |
|  - check_health() -> HealthStatusDTO                                      |
+──────────────────────────┬────────────────────────────────────────────────+
                           │ implementa
         ┌─────────────────┴─────────────────┐
         ▼                                   ▼
+─────────────────────────────+   +─────────────────────────────────────────+
|    `DatabasePadronAdapter`  |   |           `MockPadronAdapter`           |
| (Producción / Local Docker) |   |        (Tests Pytest / CI Pipeline)     |
| - Conexión SQL read-only    |   | - Fixtures deterministas en memoria     |
| - Mapeo ORM 'socio_lista'   |   | - Simulación de fallas controladas      |
+──────────────┬──────────────+   +─────────────────────────────────────────+
               │ ORM Select
+──────────────v──────────────+
|  MySQL Institucional AVEIT  |
|  (Tablas: socio_lista, ...) |
+─────────────────────────────+
```

### 4.1 Reglas Canónicas de Transformación de Dominio (Mapeador)
El adaptador aplica obligatoriamente las siguientes reglas de traducción al transformar una fila del esquema preexistente a `SocioInstitucionalDTO`:

1. **Resolución de Identidad Estable y Métodos de Consulta (CA2 / H02 / H05 / HIGH-IT2-001):**
   - En el esquema MySQL institucional, `socio_estudio.nroLegajo` es de tipo numérico `int(11)`.
   - La Capa Anticorrupción define que el legajo es una clave alfanumérica canónica para consumo de la API y el frontend.
   - **Regla de casteo y desambiguación determinista:** Si el socio posee registro en `socio_estudio`, su legajo se normaliza como la representación textual de su valor entero estricto: `legajo = str(socio_estudio.nroLegajo)` (ejemplo: `8921` $\rightarrow$ `"8921"`). En caso de cardinalidad 1 a N, se selecciona deterministamente el registro con mayor `compositeKey` mediante `Prefetch('estudios', queryset=SocioEstudio.objects.order_by('-compositeKey'))` en tiempo de consulta, evitando declarar `Meta.ordering` para impedir que Django inyecte columnas secundarias en cláusulas `SELECT DISTINCT` que provoquen filas duplicadas en búsquedas.
   - **Búsqueda por legajo sin JOINs cartesianos:** La búsqueda por legajo se ejecuta mediante subconsulta con `Exists`, garantizando que la consulta principal sobre `socio_lista` permanezca matemáticamente deduplicada y sin recuentos inflados en paginación.
   - **Regla ante ausencia de legajo:** Si el socio no cuenta con registro académico en `socio_estudio` (ingresante sin matrícula definitiva o socio honorario), se modela como `legajo = None` (`null` en JSON). Queda terminantemente prohibido inventar prefijos artificiales (como `LEG-EXT`) o suplantar el legajo con el `nroSocio`, evitando colisiones de identidad.
   - **Regla de documento de identidad (H15):** Se normaliza `socio_lista.nroDoc` como clave complementaria de individualización civil. Si `nroDoc > 0`, se castea a cadena de texto limpia `dni = str(socio_lista.nroDoc)`. En caso de valores cero, nulos o centinelas residuales, se modela como `dni = None` (`null` en JSON).
   - **Dualidad de métodos en el Puerto (`PadronRepositoryInterface`):**
     - `get_by_id(socio_id: int)`: Método de resolución técnica por clave primaria institucional (`nroSocio`). Es consumido internamente por los módulos de Expedientes (Sprint 2), Ranking (Sprint 1) y Votación (Sprint 4) para resolver relaciones foráneas, y es el único método para recuperar socios que no posean legajo universitario.
     - `get_by_legajo(legajo: str)`: Método de resolución funcional para consultas directas por número de legajo de estudiante UTN.
2. **Subcomisiones y Limpieza de Valor Centinela (CA1 / H03):**
   - En la tabla `socio_lista`, la columna `codSubcomision` posee restricción `NOT NULL`. Para representar la ausencia de subcomisión, el sistema legado empleaba el valor centinela histórico `codSubcomision = 99` etiquetado como `"Sin Subcomisión"`.
   - La Capa Anticorrupción intercepta este valor centinela:
     $$\text{Si } \text{codSubcomision} == 99 \implies \text{subcomision} = \text{None}$$
     En la API JSON y en TypeScript se expone como `subcomision = null`, garantizando semántica limpia sin distorsionar reportes ni métricas estadísticas.
3. **Categorización Estatutaria Automática (CA3):**
   - Si $1 \le \text{anoSocial} \le 3 \implies \text{category} = \text{"PASSIVE"}$ (denominación oficial en UI: *"Pasivo"*; alias anterior *Junior*).
   - Si $4 \le \text{anoSocial} \le 6 \implies \text{category} = \text{"ACTIVE"}$ (denominación oficial en UI: *"Activo"*; alias anterior *Senior*).
   - Si $\text{anoSocial}$ es inválido o nulo, el adaptador reporta el registro como anómalo (`"UNKNOWN"`) y no asume categoría por defecto.
4. **Desacoplamiento de Vigencia (CA4) y Advertencia de Trampa Semántica (H07):**
   - La categoría estatutaria (`ACTIVE`/`PASSIVE`) es independiente del estado operativo.
   - El estado de cuenta se extrae del histórico de membresía (`socio_estadoHistorial` / `socio_email.habilitado`) y se mapea a `is_active: bool` y `membership_status: str` (`"ENABLED"`, `"SUSPENDED"`, `"TERMINATED"`), con presentación visual en español rioplatense ("Habilitado", "Suspendido", "Baja") conforme al Principio 7 de la Constitución.
    - > [!WARNING]
    - > **Trampa Semántica Histórica (socio_estado vs category):** La tabla preexistente `socio_estado` contiene registros homónimos (`codEstadoSocio = 1`: "Activo" [al día con cuota/plenos derechos], `codEstadoSocio = 2`: "Pasivo" [en receso o licencia]). El adaptador **prohíbe estrictamente** mapear `socio_estado` a `category`. La categoría societaria (`ACTIVE`/`PASSIVE`) proviene **únicamente de `anoSocial`** (Arts. 3 y 6 del Estatuto 2026 y Principio 8 de la Constitución). La tabla `socio_estado` alimenta exclusivamente la vigencia operativa (`membership_status`).
5. **Resolución de Correo Electrónico Institucional (BLK-004):**
   - La tabla matriz `socio_lista` carece de columna física de correo. Los emails residen en la tabla satélite `socio_email` vinculada por `nroSocio`.
   - La Capa Anticorrupción mapea `socio_email` y extrae prioritariamente la casilla donde `habilitado = 1` y `comprobado = 1` (o la primera casilla habilitada). En caso de que el socio no posea correos registrados o habilitados, se mapea limpiamente a `email = None`.
6. **Resolución de Estado de Membresía mediante Historial Transaccional (BLK-005):**
   - La tabla `socio_lista` no cuenta con clave foránea directa a `socio_estado`. La condición de membresía de un socio es transaccional y reside en la tabla satélite `socio_estadoHistorial` (`idEstadoHistorial`, `nroSocio`, `fechaHora`, `codEstadoSocio`).
   - El adaptador resuelve el estado vigente mediante el registro con la marca temporal `fechaHora` más reciente para cada socio (`Subquery` indexada con `OuterRef` o prefetch optimizado). Dicho estado se traduce a `MembershipStatusEnum` (`codEstadoSocio = 1` $\implies$ `ENABLED`, `codEstadoSocio = 2` $\implies$ `SUSPENDED`, otros $\implies$ `TERMINATED`).

---

## 5. Estrategia de Resiliencia y Observabilidad (Cumplimiento CA5 / H04)

Para dar estricto cumplimiento al criterio **CA5** (*"Fallas/sincronizaciones quedan observables"*):

1. **Control de Tiempos de Espera (Timeouts):** Las consultas hacia la base institucional cuentan con un timeout estricto de conexión y lectura ($T \le 3000\text{ ms}$).
2. **Registro Estructurado de Eventos:** Cualquier excepción de red, caída de host o latencia anómala se captura y registra mediante el logger del sistema (`logging.getLogger('padron.adapter')`), incluyendo código de error, latencia observada y timestamp UTC, sin filtrar credenciales.
3. **Endpoint de Monitoreo (`/api/v1/padron/health/`) [MED-003 / MED-IT2-001]:** Configurado con `permission_classes = [AllowAny]` y `authentication_classes = []` para permitir su consumo irrestricto por sondas de infraestructura (Docker, Kubernetes, monitores de uptime) sin exigir autenticación JWT. Expone en formato JSON el estado de la conexión con el padrón a través de `HealthStatusDTO` con los siguientes 6 campos unificados:
   - `status`: `"HEALTHY"` | `"DEGRADED"` | `"UNAVAILABLE"`.
     - **`HEALTHY` (HTTP 200):** Conexión exitosa, latencia observada $< 500\text{ ms}$ y recuento de registros auditables $> 0$.
     - **`DEGRADED` (HTTP 200):** Conexión exitosa pero con latencia $500\text{ ms} \le \text{latencia} \le 3000\text{ ms}$, o recuento anómalo $= 0$ registros.
     - **`UNAVAILABLE` (HTTP 503):** Latencia superior a $3000\text{ ms}$, corte de enlace o excepción de base de datos (`OperationalError`, `InterfaceError`).
   - `latency_ms`: Tiempo de respuesta de la última verificación en milisegundos.
   - `source`: Origen del adaptador en ejecución (`"mysql_institutional"` | `"mock_isolated"`).
   - `record_count`: Total de registros activos auditables devueltos por la fuente.
   - `last_checked_at`: Marca temporal en formato ISO-8601 del último sondeo.
   - `message`: Diagnóstico legible u observación del estado operativo del enlace.

---

## 6. Consecuencias y Trade-offs

### Consecuencias Positivas (+)
- **Cero Divergencia:** SGD-AVEIT refleja inmediatamente cualquier cambio en el padrón institucional.
- **Seguridad Garantizada:** Imposibilidad de alterar accidentalmente registros institucionales desde la aplicación disciplinaria.
- **Cumplimiento Normativo Innegociable:** Traduce las categorías Pasivo/Activo según el Estatuto 2026 y la decisión de PO del 08/09/2026.
- **Alta Testabilidad:** El adaptador mock desacopla completamente el desarrollo diario y los tests del estado de la red física.

### Consecuencias Negativas y Mitigaciones (-)
- **Dependencia de Disponibilidad de Red:** Si la base institucional no responde, SGD-AVEIT no puede resolver nuevos legajos en tiempo real.
  - *Mitigación adoptada en Sprint 1:* Monitoreo proactivo a través del endpoint `/api/v1/padron/health/` y manejo controlado de excepciones con timeout estricto de 3000 ms.
  - *Mitigación futura opcional (Roadmap / YAGNI):* Si en entornos de producción con alta concurrencia se detectaran cuellos de botella de red, se evaluará habilitar una capa de caché en memoria de corta duración (TTL de 5 minutos) sobre catálogos estáticos como subcomisiones. Para el alcance del Sprint 1 y el volumen acotado (~515 registros), las consultas indexadas directas ofrecen latencias óptimas (<10 ms) sin introducir complejidad de invalidación.
- **Riesgo de Duplicación y Colisión de Modelos Django (BLK-003):**
  - *Problema:* El módulo de Ranking (`backend/ranking/` en rama remota `SCRUM-38`) definió preliminarmente modelos para `socio_lista` y `socio_tiposubcomision`. Si ambas aplicaciones se ejecutan concurrentemente con modelos apuntando a la misma tabla física (`db_table`), Django arrojará el error crítico `models.E028: db_table is used by multiple models`.
  - *Directriz de Integración Adoptada:* El módulo `backend/padron/` constituye la **única autoridad canónica de acceso al padrón institucional** (`managed = False`). Al momento de integrar ambas ramas en `main`, la aplicación `ranking` deberá eliminar sus modelos duplicados `Socio`, `Subcomision` y `SocioEstudio`, consumiendo exclusivamente el puerto `PadronRepositoryInterface` o reutilizando las entidades de `padron`.
- **Discrepancia de Nomenclatura e Idioma de Enums entre Ramas (LOW-002):**
  - *Problema:* En la rama `SCRUM-38`, el cálculo de categorías en `backend/ranking/models.py` retorna cadenas en español en mayúsculas (`"ACTIVO"` / `"PASIVO"`), mientras que el estándar del proyecto exige código y contratos en inglés.
  - *Directriz de Integración Adoptada:* Conforme a la Sección 3 de `AGENTS.md`, los identificadores, contratos y enums de dominio se definen en inglés. Al fusionar las ramas, `ranking` consumirá el enum canónico `SocioCategoryEnum` (`"ACTIVE"` / `"PASSIVE"`) de `backend/padron/domain.py`, reservando las etiquetas visuales en español rioplatense ("Activo" / "Pasivo") para la capa de presentación (UI / Serializers).
- **Configuración de Timeouts en Conexión de Base de Datos (LOW-001):**
  - *Problema:* Si MySQL experimenta caídas físicas de red o congelamientos, la ausencia de timeouts en el driver C `mysqlclient` bloquea los hilos de Django esperando el timeout del sistema operativo (60 a 120 segundos), agotando los workers de Gunicorn (*Worker Starvation*) y volteando la plataforma entera.
  - *Directriz Adoptada:* Aprovechando que la tarea `T1` debe registrar la app en `INSTALLED_APPS` de `backend/core/settings.py`, se incorporan `"connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "3"))` y `"read_timeout": int(os.getenv("DB_READ_TIMEOUT", "3"))` en `DATABASES['default']['OPTIONS']` (rama MySQL). Esto garantiza *fail-fast* a los 3 segundos y respuesta HTTP 503 en `/api/v1/padron/health/`.
  - *Reversibilidad en Merge:* El cambio es un diff atómico de 2 líneas dentro del diccionario `OPTIONS` de MySQL que no afecta SQLite ni el código de `padron`. Si el Líder Técnico decide gestionar la configuración central por su cuenta al fusionar con `main`, puede descartar o modificar libremente esas dos líneas sin impactar ningún componente de la User Story.
- **Unificación de Lógica de Categorías Estatutarias (SSOT de Dominio - Ex DEBT-001):**
  - *Problema:* Para paginar en MySQL con `LIMIT`/`OFFSET`, la condición estatutaria de categoría no puede filtrarse en memoria de Python. Hardcodear los rangos de año social en `services.py` y replicarlos en `DatabasePadronAdapter.list_socios()` con `anoSocial__in=[1, 2, 3]` introduce duplicación de números mágicos.
  - *Directriz Adoptada:* Se definen en `backend/padron/domain.py` las tuplas canónicas inmutables `PASSIVE_SOCIAL_YEARS = (1, 2, 3)` y `ACTIVE_SOCIAL_YEARS = (4, 5, 6)`. Tanto la lógica de dominio puro en `services.py` como la construcción de predicados SQL en `adapters.py` consumen estas constantes. Se descarta cualquier propuesta de alteración de DDL (`ALTER TABLE ... STORED GENERATED`) sobre la base institucional por violar los límites del Bounded Context y la inmutabilidad del esquema maestro.
- **Compromiso Operativo Asumido por Esquema Legado (Legacy Constraint - Ex DEBT-002):**
  - *Naturaleza del Esquema:* La tabla institucional `socio_lista` no almacena el estado actual del socio, el cual reside como una secuencia temporal de eventos en `socio_estadoHistorial`.
  - *Directriz y Justificación Arquitectónica:* La subconsulta correlacionada (`Subquery` con `OuterRef("pk")` y `order_by("-fechaHora")[:1]`) en `DatabasePadronAdapter` no constituye deuda técnica propia, sino la implementación canónica del patrón **Capa Anticorrupción (ACL)** para aislar la anomalía del esquema externo sin contaminar el dominio del SGD. Dado el volumen acotado de la masa societaria de AVEIT (~515 socios y ~3.000 a 5.000 filas de historial a lo largo de una década) y la existencia del índice físico `KEY fk_historial_socio (nroSocio)`, las consultas resuelven en memoria en $< 2\text{ ms}$. Conforme al principio YAGNI, se descarta la introducción de capas de caché distribuido (Redis) o desnormalizaciones forzadas en Secretaría.

---

## 7. Registro de Aprobaciones

| Rol | Nombre | Decisión | Fecha |
| :--- | :--- | :---: | :---: |
| **Responsable de US (Dev)** | Axel Villegas | **Aprobado** | 2026-09-19 |
| **Product Owner** | Lucas Martín Guillén | *Pendiente de homologación formal en Sprint Review* | — |
