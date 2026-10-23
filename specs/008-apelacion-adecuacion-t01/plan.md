# Plan Técnico — Spec 008: Tramitar Apelación y Adecuación del T01 (PB-02)

## 1. Esquema legacy

El legado (`tribunal_solicitud`, `tribunal_expediente`, `tribunal_t02`, `tribunal_t03`, `tribunal_enmendado`) no modela apelaciones de T01, períodos por socio, adecuaciones de puntos/involucrados ni el parámetro del plazo. `tribunal_enmendado` registra enmiendas de disposiciones ya emitidas, no el debate previo a la resolución. Se crean tablas nuevas en el módulo `expedientes` (AGENTS.md, regla 6). La solicitud T01 emitida (`SolicitudT01.snapshot_emitido`) ya es inmutable y actúa como versión original.

## 2. Arquitectura

| Capa | Archivo | Responsabilidad |
| :--- | :--- | :--- |
| Dominio puro | `backend/expedientes/domain/t01_appeal.py` | Validación de plazo, texto de apelación, adecuación (cambios, agravamiento, afectados, signo). |
| Persistencia | `backend/expedientes/models.py` | `ParametroPlazoApelacion`, `PeriodoApelacion`, `ApelacionT01`, `AdecuacionT01` (sólo-inserción). |
| Aplicación | `backend/expedientes/services/t01_appeal_service.py` | Apertura de períodos, apelación, adecuación, reapertura, notificaciones e historial. |
| Flujo | `workflow_service.py`, `deadline_service.py`, `Expediente.iniciar_plazo_descargo` | Plazo parametrizado al abrir y vencimiento según el último período. |
| API | `views`, `urls`, `serializers` | Parámetro, apelación, adecuación e historial del T01. |
| Frontend | `mis-expedientes`, `gestionar-expedientes`, `calendario` | Apelar, adecuar con autocompletado de socios y editar el plazo. |

## 3. DDL

**`expedientes_parametro_plazo_apelacion`** — historial; el vigente es el último.

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `dias_habiles` | SMALLINT | 1 a 30 |
| `autor_id` | FK → `auth_user` | Nulo para el valor inicial |
| `created_at` | DATETIME(6) | |

**`expedientes_periodo_apelacion`**

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK | `PROTECT` |
| `socio_id` | FK → `socios_socio` | `PROTECT` |
| `origen` | VARCHAR(12) | `APERTURA` / `ADECUACION` |
| `adecuacion_id` | FK nula | Adecuación que lo abrió |
| `dias_habiles` | SMALLINT | Valor congelado |
| `inicio_at`, `limite_at` | DATETIME(6) | |
| `created_at` | DATETIME(6) | |

**`expedientes_apelacion_t01`** — una fila por versión.

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id`, `socio_id` | FK | `PROTECT` |
| `numero` | INT | Único con expediente y socio |
| `texto` | TEXT | 20 a 5.000 caracteres |
| `created_at` | DATETIME(6) | Fecha del servidor |

**`expedientes_adecuacion_t01`**

| Columna | Tipo | Notas |
| :--- | :--- | :--- |
| `id` | BIGINT PK | |
| `expediente_id` | FK | `PROTECT` |
| `version` | INT | Única con expediente |
| `puntos_anteriores`, `puntos_nuevos` | DECIMAL(10,2) | |
| `socios_anteriores`, `socios_nuevos` | JSON | `[{id, legajo, nombre}]` |
| `motivos` | TEXT | ≥ 20 caracteres |
| `reabre_plazo` | BOOL | |
| `socios_con_nuevo_plazo` | JSON | IDs de socios con nuevo período |
| `autor_id` | FK → `auth_user` | |
| `autor_legajo` | VARCHAR(20) | |
| `created_at` | DATETIME(6) | |

## 4. Reglas de flujo

- **Apertura:** al entrar a `justificando`, si el expediente proviene de un T01 y no tiene períodos, se abre uno por socio con el parámetro vigente y `plazo_limite_at` toma ese límite.
- **Vencimiento:** para expedientes T01 el plazo efectivo es el máximo `limite_at` de sus períodos; lo usan la transición manual y el job de vencimiento.
- **Reapertura:** `revision_resolucion → justificando` sólo desde la adecuación aprobada por el TD, con `CambioEstadoExpediente`.

## 5. Decisiones y alternativas descartadas

- **Versiones por fila** en apelaciones y adecuaciones: cumple CA2/CA4 y la regla de cero `UPDATE` sobre registros auditables.
- **Períodos por socio** y no un único plazo: la reapertura alcanza sólo a los afectados (CA5).
- **Adecuar `Expediente.puntos` y `Expediente.socios`:** son los valores solicitados vigentes, no saldos; los saldos se mueven sólo con la resolución emitida (Sprint 5).
- **Descartado:** reutilizar `DescargoExpediente` con un tipo nuevo: mezclaría apelaciones con la valoración de causales T02 (Spec 006).
- **Descartado:** variable de entorno para el plazo: el TD no podría ajustarlo sin un despliegue.
